"""
FabrikaOS — Üretim, Arıza, Bakım, Duruş Demo Verisi
Senaryo: AnadoluTech Metal Sanayi — 6 aylık (180 günlük) gerçekçi üretim verileri

- Üretim verileri: Makine bazlı, vardiya bazlı, OEE hesaplamalı
- Arıza kayıtları: Çözülmüş + açık arızalar
- Bakım kayıtları: Periyodik + korektif bakımlar
- Duruş kayıtları: 6 Büyük Kayıp kategorisinde
"""
import random
from datetime import date, datetime, timedelta, timezone, time
from app.extensions import db
from app.models.makine import Makine, UretimVerisi, ArizaKaydi, BakimKaydi, DurusKaydi
from app.models.personel import Calisan
from app.models.kullanici import Kullanici


def seed():
    print('[3/12] Üretim verileri...')
    random.seed(2026)

    makineler = Makine.query.filter_by(aktif=True).all()
    calisanlar = Calisan.query.filter(Calisan.departman.in_(['Üretim', 'Bakım'])).all()
    uretim_operatorleri = Calisan.query.filter_by(departman='Üretim', aktif=True).all()
    teknisyenler = Kullanici.query.filter_by(rol='teknisyen').all()
    operatorler = Kullanici.query.filter_by(rol='operator').all()

    bugun = date.today()
    vardiyalar = ['sabah', 'ogleden_sonra', 'gece']

    # ── SON 6 AY (180 GÜN) ÜRETİM VERİSİ ──
    makine_operator_map = {}
    for m in makineler:
        uygun = [c for c in uretim_operatorleri if c.beceri_json and
                 any(b.get('makine_id') == m.id for b in (c.beceri_json or []))]
        if not uygun:
            uygun = uretim_operatorleri
        makine_operator_map[m.id] = uygun

    for gun_offset in range(180, 0, -1):
        tarih = bugun - timedelta(days=gun_offset)
        gun_index = tarih.weekday()

        if gun_index == 6:  # Pazar
            continue
        gunun_vardiyalari = ['sabah'] if gun_index == 5 else vardiyalar

        # Haftanın gününe göre temel performans çarpanı (Organik Eğri)
        # Pts: %95, Sal: %100, Çar: %100, Per: %98, Cum: %92, Cts: %85
        gun_performans_carpani = {0: 0.95, 1: 1.0, 2: 1.0, 3: 0.98, 4: 0.92, 5: 0.85}[gun_index]

        for makine in makineler:
            if makine.durum == 'arizali' and gun_offset < 3:
                continue

            for vardiya in gunun_vardiyalari:
                if random.random() > 0.75 and len(gunun_vardiyalari) > 1:
                    continue

                uygun_ops = makine_operator_map.get(makine.id, uretim_operatorleri)
                calisan = random.choice(uygun_ops)

                planlanan = 480
                kayip_dk = random.randint(15, 75)
                gercek = planlanan - kayip_dk

                kapasite = makine.teorik_kapasite

                # Vardiyaya göre performans çarpanı
                vardiya_perf_carpani = {'sabah': 1.0, 'ogleden_sonra': 0.95, 'gece': 0.88}[vardiya]
                
                # Temel performans (0.85 - 0.95 arası) * gün * vardiya
                baz_perf = random.uniform(0.85, 0.95)
                performans_katsayi = baz_perf * gun_performans_carpani * vardiya_perf_carpani
                # Sınırlandırma
                performans_katsayi = min(max(performans_katsayi, 0.50), 0.99)

                uretim = int(kapasite * (gercek / 60) * performans_katsayi)

                # Vardiyaya göre hata oranı eğrisi
                vardiya_hata_carpani = {'sabah': 1.0, 'ogleden_sonra': 1.2, 'gece': 1.8}[vardiya]
                baz_hata = random.uniform(0.005, 0.02)
                hata_orani = baz_hata * vardiya_hata_carpani * (2.0 if gun_index in [0, 4, 5] else 1.0)
                hata_orani = min(hata_orani, 0.15) # En fazla %15

                hatali = max(0, int(uretim * hata_orani))

                notlar_listesi = [
                    None, None, None,
                    'Normal üretim akışı',
                    'Kalıp/takım değişimi sonrası ilk parça onayı alındı',
                    'Hammadde parti değişikliği yapıldı',
                    'Soğutma sıvısı/su debisi kontrol edildi',
                    'Takım/kalıp ömrü doldu, değişim yapıldı',
                    'Müşteri acil siparişi önceliklendirildi',
                ]

                uv = UretimVerisi(
                    makine_id=makine.id,
                    calisan_id=calisan.id,
                    vardiya=vardiya,
                    tarih=tarih,
                    planlanan_sure_dk=planlanan,
                    gercek_calisma_dk=gercek,
                    gercek_uretim=uretim,
                    hatali_uretim=hatali,
                    notlar=random.choice(notlar_listesi),
                )
                uv.hesapla_oee(kapasite)
                db.session.add(uv)

    db.session.flush()
    print('  + 6 aylık (180 günlük) çok vardiyalı üretim verisi oluşturuldu')

    # ── ARIZA KAYITLARI ──
    print('[4/12] Arıza kayıtları...')

    # Makine kodlarını al
    m_kodlari = [m.kod for m in makineler]
    # Kodları rastgele eşleştir, ama belirli arızalar için var olan kodlardan seç.
    def m_sec(idx):
        return m_kodlari[idx % len(m_kodlari)] if m_kodlari else 'BİLİNMEYEN'

    arizalar = [
        # Açık arızalar
        {'makine_kod': m_sec(3), 'ariza_turu': 'mekanik', 'oncelik': 'yuksek', 'aciklama': 'Yağ sızıntısı başladı. Üretim durdu.', 'durum': 'acik', 'gun_once': 2},
        {'makine_kod': m_sec(2), 'ariza_turu': 'mekanik', 'oncelik': 'kritik', 'aciklama': 'Kilitleme ünitesinde aşınma. Kuvvet yetersiz.', 'durum': 'acik', 'gun_once': 1},
        # Çözülmüş arızalar
        {'makine_kod': m_sec(0), 'ariza_turu': 'elektrik', 'oncelik': 'normal', 'aciklama': 'Servo motor sürücüsünde aşırı akım hatası.', 'cozum': 'Servo fanı değiştirildi.', 'durum': 'cozuldu', 'gun_once': 12, 'sure': 145},
        {'makine_kod': m_sec(1), 'ariza_turu': 'yazilim', 'oncelik': 'dusuk', 'aciklama': 'Kontrol ünitesinde offset komutu yanlış değer okuyor.', 'cozum': 'Offset tablosu sıfırlandı.', 'durum': 'cozuldu', 'gun_once': 18, 'sure': 55},
        {'makine_kod': m_sec(4), 'ariza_turu': 'elektrik', 'oncelik': 'normal', 'aciklama': 'Robot eksen servo alarm.', 'cozum': 'Kablo yenilendi.', 'durum': 'cozuldu', 'gun_once': 22, 'sure': 95},
        {'makine_kod': m_sec(5), 'ariza_turu': 'mekanik', 'oncelik': 'normal', 'aciklama': 'Dinamik dengesizlik tespit edildi.', 'cozum': 'Balans ayarı yapıldı.', 'durum': 'cozuldu', 'gun_once': 9, 'sure': 70},
        {'makine_kod': m_sec(0), 'ariza_turu': 'mekanik', 'oncelik': 'normal', 'aciklama': 'Tahliye durdu, zincir koptu.', 'cozum': 'Zincir değiştirildi.', 'durum': 'cozuldu', 'gun_once': 25, 'sure': 40},
        {'makine_kod': m_sec(2), 'ariza_turu': 'elektrik', 'oncelik': 'normal', 'aciklama': 'Isıtıcı band arızası. Sıcaklık düşük.', 'cozum': 'Isıtıcı band değiştirildi.', 'durum': 'cozuldu', 'gun_once': 15, 'sure': 60},
    ]

    for a in arizalar:
        makine = Makine.query.filter_by(kod=a['makine_kod']).first()
        if not makine:
            continue
        bas = datetime.now(timezone.utc) - timedelta(days=a['gun_once'])
        bitis = None
        if a['durum'] == 'cozuldu':
            bitis = bas + timedelta(minutes=a.get('sure', 60))
        bildiren = random.choice(operatorler) if operatorler else None
        teknisyen = random.choice(teknisyenler) if teknisyenler else None

        kayit = ArizaKaydi(
            makine_id=makine.id,
            bildiren_id=bildiren.id if bildiren else 1,
            atanan_teknisyen_id=teknisyen.id if teknisyen else None,
            baslangic_zamani=bas,
            bitis_zamani=bitis,
            ariza_turu=a['ariza_turu'],
            aciklama=a['aciklama'],
            cozum=a.get('cozum'),
            oncelik=a['oncelik'],
            durum=a['durum'],
            mudahale_suresi_dk=a.get('sure'),
        )
        db.session.add(kayit)
        print(f'  + Arıza: {a["makine_kod"]} — {a["ariza_turu"]} ({a["durum"]})')

    db.session.flush()

    # ── BAKIM KAYITLARI ──
    print('[5/12] Bakım kayıtları...')

    bakimlar = [
        {'makine_kod': m_sec(0), 'tur': 'periyodik', 'islem': 'Rulman gres değişimi, eksen yağlama, backlash kontrolü. Soğutma sıvısı konsantrasyon ölçümü yapıldı.', 'tarih': date(2026, 4, 15), 'sure': 210, 'maliyet': 5200.00, 'notlar': 'Sonraki bakımda rulman değişimi planlanmalı.'},
        {'makine_kod': m_sec(1), 'tur': 'periyodik', 'islem': 'Soğutma sistemi temizliği, pnömatik silindir kontrolü.', 'tarih': date(2026, 3, 20), 'sure': 180, 'maliyet': 3800.00, 'notlar': 'Pnömatik valfler kontrol edilmeli.'},
        {'makine_kod': m_sec(2), 'tur': 'korektif', 'islem': 'Aşınmış mekanizma ucu değiştirildi. Geri akış valfi yenilendi. Isıtıcı bantların dirençleri ölçüldü.', 'tarih': date(2026, 4, 28), 'sure': 300, 'maliyet': 18500.00, 'notlar': 'Tolerans değerleri uygun.'},
        {'makine_kod': m_sec(3), 'tur': 'periyodik', 'islem': 'Hidrolik yağ filtresi değişimi (10μ), hortum muayenesi, keçe kontrolü. Hidrolik yağ numunesi analize gönderildi.', 'tarih': date(2026, 2, 10), 'sure': 150, 'maliyet': 3200.00, 'notlar': 'Sızıntı takibe alındı.'},
        {'makine_kod': m_sec(4), 'tur': 'periyodik', 'islem': 'Eksen yağlama. Kablo kanalı muayenesi. Kalibrasyon kontrolü. TCP kalibrasyonu.', 'tarih': date(2026, 4, 1), 'sure': 240, 'maliyet': 7800.00, 'notlar': 'Sapma kabul edilebilir aralıkta.'},
        {'makine_kod': m_sec(5), 'tur': 'periyodik', 'islem': 'Filtre değişimi. Geometrik doğruluk ölçümü yapıldı.', 'tarih': date(2026, 4, 20), 'sure': 120, 'maliyet': 2400.00, 'notlar': 'Kabul edilebilir sınırda.'},
        {'makine_kod': m_sec(0), 'tur': 'korektif', 'islem': 'Servo motor fan değişimi. Sürücü ünitesi üfleme ile temizlendi.', 'tarih': date(2026, 4, 22), 'sure': 65, 'maliyet': 1150.00, 'notlar': None},
        {'makine_kod': m_sec(2), 'tur': 'periyodik', 'islem': 'Kilitleme sistemi kontrolü. Basınç testi. Ejektör mekanizması yağlama.', 'tarih': date(2026, 2, 15), 'sure': 180, 'maliyet': 4100.00, 'notlar': 'İzlemeye alındı.'},
        {'makine_kod': m_sec(1), 'tur': 'korektif', 'islem': 'Firmware güncelleme. Parametre tablosu yeniden oluşturuldu.', 'tarih': date(2026, 4, 16), 'sure': 45, 'maliyet': 650.00, 'notlar': None},
    ]

    for b in bakimlar:
        makine = Makine.query.filter_by(kod=b['makine_kod']).first()
        if not makine:
            continue
        teknisyen = random.choice(teknisyenler) if teknisyenler else None
        kayit = BakimKaydi(
            makine_id=makine.id,
            bakim_turu=b['tur'],
            yapilan_islem=b['islem'],
            teknisyen_id=teknisyen.id if teknisyen else None,
            tarih=b['tarih'],
            sure_dk=b['sure'],
            maliyet=b['maliyet'],
            sonraki_bakim_tarihi=b['tarih'] + timedelta(days=makine.periyodik_bakim_gun),
            notlar=b.get('notlar'),
        )
        db.session.add(kayit)
        print(f'  + Bakım: {b["makine_kod"]} — {b["tur"]}')

    db.session.flush()

    # ── DURUŞ KAYITLARI (Son 14 gün) ──
    print('[6/12] Duruş kayıtları...')

    durus_sablonlari = {
        'ariza': [
            ('Servo motor alarm', 'Servo sürücüden E-07 alarm kodu geldi.'),
            ('Sensör hatası', 'Proksimiti sensör sinyal kaybı yaşandı.'),
            ('Hidrolik sızıntı', 'Basınç hattında yağ damlası tespit edildi.'),
            ('PLC iletişim hatası', 'PLC-HMI arası haberleşme koptu.'),
        ],
        'setup': [
            ('Kalıp/takım değişimi', 'Planlı kalıp/takım seti değişimi yapıldı.'),
            ('Program değişikliği', 'Yeni ürün programı yüklendi ve simülasyon yapıldı.'),
            ('Fikstür ayarı', 'İş parçası bağlama fikstürü değiştirildi.'),
        ],
        'malzeme_bekleme': [
            ('Hammadde gecikmesi', 'Tedarikçi teslimatı planlanandan geç geldi.'),
            ('Yarı mamul bekleme', 'Önceki operasyondan gelen parça hazır değil.'),
            ('Kalite onayı bekleme', 'İlk parça kalite onayı bekleniyor.'),
        ],
        'kalip_degisim': [
            ('Planlı kalıp bakımı', 'Kalıp bakım prosedürü uygulandı.'),
            ('Kalıp temizliği', 'Üretim araçları sökülerek temizlendi.'),
        ],
        'plansiz_mola': [
            ('Personel molası', 'Vardiya ara molası.'),
            ('Vardiya devir teslim', 'Vardiya geçişinde bilgilendirme yapıldı.'),
        ],
        'enerji_kesintisi': [
            ('Elektrik kesintisi', 'Fabrika genelinde plansız elektrik kesintisi.'),
            ('Basınçlı hava düşüşü', 'Kompresör arızası nedeniyle hat basıncı düştü.'),
        ],
    }

    kategoriler = list(durus_sablonlari.keys())
    kategori_agirliklari = [0.25, 0.30, 0.15, 0.10, 0.12, 0.08]

    for gun in range(14, 0, -1):
        tarih = bugun - timedelta(days=gun)
        if tarih.weekday() == 6:  # Pazar
            continue
        durus_sayisi = random.randint(2, 4)
        for _ in range(durus_sayisi):
            makine = random.choice(makineler)
            kat = random.choices(kategoriler, weights=kategori_agirliklari, k=1)[0]
            neden, aciklama = random.choice(durus_sablonlari[kat])
            saat = random.randint(6, 22)
            dakika = random.choice([0, 15, 30, 45])
            bas = datetime(tarih.year, tarih.month, tarih.day, saat, dakika,
                           tzinfo=timezone.utc)
            sure = random.randint(8, 90)
            bit = bas + timedelta(minutes=sure)

            dk = DurusKaydi(
                makine_id=makine.id,
                baslangic=bas,
                bitis=bit,
                sure_dk=sure,
                neden=neden,
                kategori=kat,
                aciklama=f'{aciklama} Toplam {sure} dk duruş kaydedildi.',
            )
            db.session.add(dk)

    db.session.flush()
    print('  + 14 günlük kategorize duruş kayıtları oluşturuldu\n')
