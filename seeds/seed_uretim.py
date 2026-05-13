"""
FabrikaOS — Üretim, Arıza, Bakım, Duruş Demo Verisi
Senaryo: AnadoluTech Metal Sanayi — 30 günlük gerçekçi üretim verileri

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

    # ── SON 30 GÜN ÜRETİM VERİSİ ──
    # Her makine her iş gününde en az 1 vardiya çalışır
    makine_operator_map = {}
    for m in makineler:
        # Her makineye uygun operatör ata
        uygun = [c for c in uretim_operatorleri if c.beceri_json and
                 any(b.get('makine_id') == m.id for b in (c.beceri_json or []))]
        if not uygun:
            uygun = uretim_operatorleri
        makine_operator_map[m.id] = uygun

    for gun_offset in range(30, 0, -1):
        tarih = bugun - timedelta(days=gun_offset)
        # Pazar günü üretim yok
        if tarih.weekday() == 6:
            continue
        # Cumartesi sadece sabah vardiyası
        gunun_vardiyalari = ['sabah'] if tarih.weekday() == 5 else vardiyalar

        for makine in makineler:
            # Arızalı makine son 3 gün çalışmaz
            if makine.durum == 'arizali' and gun_offset < 3:
                continue

            for vardiya in gunun_vardiyalari:
                # Her vardiya her makine çalışmaz — %75 olasılık
                if random.random() > 0.75 and len(gunun_vardiyalari) > 1:
                    continue

                uygun_ops = makine_operator_map.get(makine.id, uretim_operatorleri)
                calisan = random.choice(uygun_ops)

                # Vardiya süreleri (dakika)
                if vardiya == 'sabah':
                    planlanan = 480  # 06:00-14:00
                elif vardiya == 'ogleden_sonra':
                    planlanan = 480  # 14:00-22:00
                else:
                    planlanan = 480  # 22:00-06:00

                # Gerçek çalışma: planlı duruşlar çıkarılır
                kayip_dk = random.randint(15, 75)
                gercek = planlanan - kayip_dk

                kapasite = makine.teorik_kapasite
                # Üretim miktarı = kapasite × çalışma saati × performans katsayısı
                performans_katsayi = random.uniform(0.78, 0.97)
                uretim = int(kapasite * (gercek / 60) * performans_katsayi)

                # Hatalı üretim: genelde %1-4 arası
                hata_orani = random.uniform(0.005, 0.04)
                hatali = max(0, int(uretim * hata_orani))

                notlar_listesi = [
                    None, None, None,  # Çoğunlukla not yok
                    'Normal üretim akışı',
                    'Kalıp değişimi sonrası ilk parça onayı alındı',
                    'Hammadde parti değişikliği yapıldı',
                    'Soğutma sıvısı seviyesi kontrol edildi',
                    'Takım ömrü doldu, değişim yapıldı',
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
    print('  + 30 günlük çok vardiyalı üretim verisi oluşturuldu')

    # ── ARIZA KAYITLARI ──
    print('[4/12] Arıza kayıtları...')

    arizalar = [
        # Açık arızalar (şu an devam eden)
        {
            'makine_kod': 'PRS-001',
            'ariza_turu': 'mekanik',
            'oncelik': 'yuksek',
            'aciklama': 'Hidrolik silindir rod keçesinden yağ sızıntısı başladı. '
                        'Basınç 180 bar yerine 145 bara düştü. Üretim durdu.',
            'durum': 'acik',
            'gun_once': 2,
        },
        {
            'makine_kod': 'ENJ-001',
            'ariza_turu': 'mekanik',
            'oncelik': 'kritik',
            'aciklama': 'Kalıp kilitleme ünitesinde toggle mekanizması aşınması. '
                        'Kilitleme kuvveti yetersiz, ürünlerde çapak oluşuyor.',
            'durum': 'acik',
            'gun_once': 1,
        },

        # Çözülmüş arızalar (geçmiş)
        {
            'makine_kod': 'CNC-001',
            'ariza_turu': 'elektrik',
            'oncelik': 'normal',
            'aciklama': 'X ekseni servo motor sürücüsünde E-07 (aşırı akım) hatası. '
                        'Makine acil duruma geçti.',
            'cozum': 'Servo sürücü fan motoru arızalıydı. Fan değiştirildi, '
                     'sürücü soğutma hattı temizlendi. Parametre sıfırlaması yapıldı.',
            'durum': 'cozuldu',
            'gun_once': 12,
            'sure': 145,
        },
        {
            'makine_kod': 'CNC-002',
            'ariza_turu': 'yazilim',
            'oncelik': 'dusuk',
            'aciklama': 'FANUC 0i-MF kontrol ünitesinde G43 tool length offset komutu '
                        'yanlış değer okuyor. Parça yüksekliği hatalı çıkıyor.',
            'cozum': 'Tool offset tablosu sıfırlandı ve kalibrasyon yapıldı. '
                     'FANUC firmware 30iB+ sürümüne güncellendi.',
            'durum': 'cozuldu',
            'gun_once': 18,
            'sure': 55,
        },
        {
            'makine_kod': 'KYN-001',
            'ariza_turu': 'elektrik',
            'oncelik': 'normal',
            'aciklama': 'Robot 4. eksen (wrist) servo motor alarm: SRVO-023 (aşırı '
                        'akım). Kaynak sırasında pozisyon kaybı yaşanıyor.',
            'cozum': 'Kablo tesisatı kontrol edildi, J4 eksen kablosu ezilme tespit '
                     'edildi. Kablo yenilendi, torç ucu değiştirildi.',
            'durum': 'cozuldu',
            'gun_once': 22,
            'sure': 95,
        },
        {
            'makine_kod': 'TSL-001',
            'ariza_turu': 'mekanik',
            'oncelik': 'normal',
            'aciklama': 'Taşlama taşı dinamik dengesizlik tespit edildi. '
                        'Yüzey pürüzlülüğü Ra 0.8 yerine Ra 1.6 çıkıyor.',
            'cozum': 'Taşlama taşı balans ayarı yapıldı. Mil rulmanı muayene edildi, '
                     'gres değişimi uygulandı.',
            'durum': 'cozuldu',
            'gun_once': 9,
            'sure': 70,
        },
        {
            'makine_kod': 'CNC-001',
            'ariza_turu': 'mekanik',
            'oncelik': 'normal',
            'aciklama': 'Talaş konveyörü zincir kopması. Talaş tahliye durdu.',
            'cozum': 'Konveyör zinciri 3 bakla değiştirildi, gerginlik ayarı yapıldı.',
            'durum': 'cozuldu',
            'gun_once': 25,
            'sure': 40,
        },
        {
            'makine_kod': 'ENJ-001',
            'ariza_turu': 'elektrik',
            'oncelik': 'normal',
            'aciklama': 'Kovan ısıtıcı band 3. bölge arızası. Eriyik sıcaklığı hedefin '
                        'altında kalıyor.',
            'cozum': 'Isıtıcı band değiştirildi (800W seramik tip). '
                     'Termocouple kalibrasyonu yapıldı.',
            'durum': 'cozuldu',
            'gun_once': 15,
            'sure': 60,
        },
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
        {
            'makine_kod': 'CNC-001', 'tur': 'periyodik',
            'islem': 'Spindle rulman gres değişimi, X/Y/Z eksenleri yağlama, '
                     'ball screw backlash kontrolü ve kalibrasyonu. '
                     'Soğutma sıvısı konsantrasyon ölçümü yapıldı (pH: 9.2).',
            'tarih': date(2026, 4, 15), 'sure': 210, 'maliyet': 5200.00,
            'notlar': 'Bir sonraki bakımda spindle rulman değişimi planlanmalı.',
        },
        {
            'makine_kod': 'CNC-002', 'tur': 'periyodik',
            'islem': 'Spindle soğutma çilleri temizliği, ATC (Otomatik Takım Değiştirici) '
                     'pnömatik silindir kontrolü. Way cover ve teleskopik kapak muayenesi.',
            'tarih': date(2026, 3, 20), 'sure': 180, 'maliyet': 3800.00,
            'notlar': 'ATC gripper pençeleri sonraki bakımda değiştirilecek.',
        },
        {
            'makine_kod': 'ENJ-001', 'tur': 'korektif',
            'islem': 'Enjeksiyon vidası (screw) ve silindir (barrel) iç yüzey kontrolü. '
                     'Aşınmış vida ucu (tip) değiştirildi. Geri akış valfi (check ring) yenilendi. '
                     'Isıtıcı bantların dirençleri ölçüldü.',
            'tarih': date(2026, 4, 28), 'sure': 300, 'maliyet': 18500.00,
            'notlar': 'Vida ve silindir arası boşluk 0.08mm — tolerans dahilinde.',
        },
        {
            'makine_kod': 'PRS-001', 'tur': 'periyodik',
            'islem': 'Hidrolik yağ filtresi değişimi (10μ), basınç hattı hortum muayenesi, '
                     'silindir keçe kontrolü. Hidrolik yağ numunesi alınarak analiz laboratuvarına gönderildi.',
            'tarih': date(2026, 2, 10), 'sure': 150, 'maliyet': 3200.00,
            'notlar': 'Yağ analiz raporu bekleniyor. Silindirdeki sızıntı takibe alındı.',
        },
        {
            'makine_kod': 'KYN-001', 'tur': 'periyodik',
            'islem': 'Robot 6 eksen reducer yağlama (Nabtesco RV reducer). '
                     'Kablo kanalı muayenesi. Teaching pendant kalibrasyon kontrolü. '
                     'TCP (Tool Center Point) kalibrasyonu.',
            'tarih': date(2026, 4, 1), 'sure': 240, 'maliyet': 7800.00,
            'notlar': 'J2 eksen reducer sesi normale döndü. TCP sapması 0.02mm.',
        },
        {
            'makine_kod': 'TSL-001', 'tur': 'periyodik',
            'islem': 'Taşlama taşı değişimi (Norton 46 grit). Hidrostatik yatak yağ seviyesi kontrolü. '
                     'Soğutma sıvısı filtresi değişimi. Geometrik doğruluk ölçümü yapıldı.',
            'tarih': date(2026, 4, 20), 'sure': 120, 'maliyet': 2400.00,
            'notlar': 'Silindiriklik sapması 0.003mm — kabul edilebilir sınırda.',
        },
        {
            'makine_kod': 'CNC-001', 'tur': 'korektif',
            'islem': 'X ekseni servo motor fan değişimi (arıza #3 sonrası). '
                     'Sürücü ünitesi üfleme ile temizlendi.',
            'tarih': date(2026, 4, 22), 'sure': 65, 'maliyet': 1150.00,
            'notlar': None,
        },
        {
            'makine_kod': 'ENJ-001', 'tur': 'periyodik',
            'islem': 'Kalıp kilitleme sistemi toggle pin kontrolü. '
                     'Hidrolik pompa basınç testi. Ejektör mekanizması yağlama.',
            'tarih': date(2026, 2, 15), 'sure': 180, 'maliyet': 4100.00,
            'notlar': 'Toggle pinlerde aşınma başlangıcı görüldü — izlemeye alındı.',
        },
        {
            'makine_kod': 'CNC-002', 'tur': 'korektif',
            'islem': 'Firmware güncelleme (G43 offset sorunu). '
                     'Tool offset tablosu yeniden oluşturuldu.',
            'tarih': date(2026, 4, 16), 'sure': 45, 'maliyet': 650.00,
            'notlar': None,
        },
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
            ('Kalıp temizliği', 'Enjeksiyon kalıbı sökülerek temizlendi.'),
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
    # Kategori ağırlıkları (gerçekçi dağılım)
    kategori_agirliklari = [0.25, 0.30, 0.15, 0.10, 0.12, 0.08]

    for gun in range(14, 0, -1):
        tarih = bugun - timedelta(days=gun)
        if tarih.weekday() == 6:  # Pazar
            continue
        # Günlük duruş sayısı: 2-4 arası
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
