"""
FabrikaOS — Üretim, Arıza, Bakım, Duruş Demo Verisi (v2 — 8 Makine, 6 Ay)
Senaryo: AnadoluTech Metal Sanayi — Gerçekçi endüstriyel üretim verileri

- Üretim verileri: 8 makine, vardiya bazlı, OEE hesaplamalı
- Arıza kayıtları: 12 arıza (4 açık, 2 araştırılıyor, 6 çözüldü)
- Bakım kayıtları: 15 bakım (periyodik + korektif + acil)
- Duruş kayıtları: 21 günlük, 6 kategori
"""
import random
from datetime import date, datetime, timedelta, timezone
from app.extensions import db
from app.models.makine import Makine, UretimVerisi, ArizaKaydi, BakimKaydi, DurusKaydi
from app.models.personel import Calisan
from app.models.kullanici import Kullanici


def seed():
    print('[3/22] Üretim verileri...')
    random.seed(2026)

    makineler = Makine.query.filter_by(aktif=True).all()
    uretim_operatorleri = Calisan.query.filter_by(departman='Üretim', aktif=True).all()
    teknisyenler = Kullanici.query.filter_by(rol='teknisyen').all()
    operatorler = Kullanici.query.filter_by(rol='operator').all()

    bugun = date.today()
    vardiyalar = ['sabah', 'ogleden_sonra', 'gece']

    # ── SON 6 AY ÜRETİM VERİSİ ──
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

        gun_performans_carpani = {0: 0.95, 1: 1.0, 2: 1.0, 3: 0.98, 4: 0.92, 5: 0.85}[gun_index]

        for makine in makineler:
            if makine.durum in ('arizali', 'bakimda') and gun_offset < 3:
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
                vardiya_perf_carpani = {'sabah': 1.0, 'ogleden_sonra': 0.95, 'gece': 0.88}[vardiya]
                baz_perf = random.uniform(0.85, 0.95)
                performans_katsayi = baz_perf * gun_performans_carpani * vardiya_perf_carpani
                performans_katsayi = min(max(performans_katsayi, 0.50), 0.99)

                uretim = int(kapasite * (gercek / 60) * performans_katsayi)

                vardiya_hata_carpani = {'sabah': 1.0, 'ogleden_sonra': 1.2, 'gece': 1.8}[vardiya]
                baz_hata = random.uniform(0.005, 0.02)
                hata_orani = baz_hata * vardiya_hata_carpani * (2.0 if gun_index in [0, 4, 5] else 1.0)
                hata_orani = min(hata_orani, 0.15)
                hatali = max(0, int(uretim * hata_orani))

                notlar_listesi = [
                    None, None, None,
                    'Normal üretim akışı',
                    'Kalıp/takım değişimi sonrası ilk parça onayı alındı',
                    'Hammadde parti değişikliği yapıldı',
                    'Soğutma sıvısı/su debisi kontrol edildi',
                    'Takım/kalıp ömrü doldu, değişim yapıldı',
                    'Müşteri acil siparişi önceliklendirildi',
                    'Lazer rezonatör temizliği yapıldı',
                    'Montaj hattı bant hızı optimize edildi',
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
    print('  + 6 aylık çok vardiyalı üretim verisi (8 makine) oluşturuldu')

    # ── ARIZA KAYITLARI (12 arıza) ──
    print('[4/22] Arıza kayıtları...')

    m_kodlari = {m.kod: m for m in makineler}

    arizalar = [
        # Açık arızalar (4)
        {'makine_kod': 'PRS-001', 'ariza_turu': 'mekanik', 'oncelik': 'kritik',
         'aciklama': 'Hidrolik pistondan ciddi yağ sızıntısı başladı. Üretim durdu, zemin yağlı.', 'durum': 'acik', 'gun_once': 1},
        {'makine_kod': 'ABK-001', 'ariza_turu': 'mekanik', 'oncelik': 'yuksek',
         'aciklama': 'Kilitleme ünitesinde aşınma tespit edildi. Bükme kuvveti yetersiz, tolerans dışı parçalar üretiliyor.',
         'durum': 'acik', 'gun_once': 2},
        {'makine_kod': 'TSL-001', 'ariza_turu': 'elektrik', 'oncelik': 'normal',
         'aciklama': 'Taşlama taşı motor frekans invertörü zaman zaman alarm veriyor. E-05 hata kodu.', 'durum': 'acik', 'gun_once': 3},
        {'makine_kod': 'MNT-001', 'ariza_turu': 'pnomatik', 'oncelik': 'dusuk',
         'aciklama': 'Montaj hattı pnömatik silindirlerde hava kaçağı var. Hareket yavaşladı.', 'durum': 'acik', 'gun_once': 5},

        # Araştırılıyor (2)
        {'makine_kod': 'LZR-001', 'ariza_turu': 'optik', 'oncelik': 'yuksek',
         'aciklama': 'Lazer kesim kalitesinde düşüş gözleniyor. Kenar pürüzlülüğü artmış. Lens/ayna kontaminasyonu şüphesi.',
         'durum': 'arastiriliyor', 'gun_once': 4},
        {'makine_kod': 'CNC-002', 'ariza_turu': 'mekanik', 'oncelik': 'normal',
         'aciklama': 'Z ekseninde anormal titreşim ve gürültü. Rulman problemi olabilir.',
         'durum': 'arastiriliyor', 'gun_once': 6},

        # Çözülmüş arızalar (6)
        {'makine_kod': 'CNC-001', 'ariza_turu': 'elektrik', 'oncelik': 'normal',
         'aciklama': 'Servo motor sürücüsünde aşırı akım hatası (E-12). Makine aniden durdu.',
         'cozum': 'Servo motor fan grubu değiştirildi. Sürücü ünitesi basınçlı hava ile temizlendi. Test üretimde sorun gözlenmedi.',
         'durum': 'cozuldu', 'gun_once': 12, 'sure': 145},
        {'makine_kod': 'CNC-002', 'ariza_turu': 'yazilim', 'oncelik': 'dusuk',
         'aciklama': 'Kontrol ünitesinde offset komutu yanlış değer okuyor. Operatör kompanzasyon yapamıyor.',
         'cozum': 'Offset tablosu sıfırlandı, firmware güncellendi. Kalibrasyon testi yapıldı.',
         'durum': 'cozuldu', 'gun_once': 18, 'sure': 55},
        {'makine_kod': 'KYN-001', 'ariza_turu': 'elektrik', 'oncelik': 'normal',
         'aciklama': 'Robot 3. eksen servo alarm. Hareket esnasında ani duruş.',
         'cozum': 'Encoder kablosu hasar görmüş, kablo yenilendi. Kalibrasyon tamamlandı.',
         'durum': 'cozuldu', 'gun_once': 22, 'sure': 95},
        {'makine_kod': 'TSL-001', 'ariza_turu': 'mekanik', 'oncelik': 'normal',
         'aciklama': 'Taşlama mili dinamik dengesizlik tespit edildi. Yüzey kalitesi etkilendi.',
         'cozum': 'Mil balans ayarı yapıldı, taş dengesi kontrol edildi. Ra değerleri tolerans içinde.',
         'durum': 'cozuldu', 'gun_once': 9, 'sure': 70},
        {'makine_kod': 'CNC-001', 'ariza_turu': 'mekanik', 'oncelik': 'normal',
         'aciklama': 'Talaş tahliye konveyörü durdu. Zincir kopmuş.',
         'cozum': 'Zincir değiştirildi, gergi ayarı yapıldı. Talaş birikimine karşı koruyucu kafes eklendi.',
         'durum': 'cozuldu', 'gun_once': 25, 'sure': 40},
        {'makine_kod': 'LZR-001', 'ariza_turu': 'mekanik', 'oncelik': 'yuksek',
         'aciklama': 'Kesim tablası doğrusal kızak aşırı ısınma. Hareket zorlaştı.',
         'cozum': 'Kızak yağlama sistemi arızalı pompa değiştirildi. Kızak temizlendi ve yağlandı.',
         'durum': 'cozuldu', 'gun_once': 15, 'sure': 120},
    ]

    for a in arizalar:
        makine = m_kodlari.get(a['makine_kod'])
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
        print(f'  + Arıza: {a["makine_kod"]} — {a["ariza_turu"]} ({a["durum"]}) [{a["oncelik"]}]')

    db.session.flush()

    # ── BAKIM KAYITLARI (15 bakım) ──
    print('[5/22] Bakım kayıtları...')

    bakimlar = [
        # CNC-001
        {'makine_kod': 'CNC-001', 'tur': 'periyodik', 'islem': 'Rulman gres değişimi, tüm eksen yağlama, backlash kontrolü. Soğutma sıvısı konsantrasyon ölçümü: %6.2 (ideal aralıkta).', 'tarih': date(2026, 4, 15), 'sure': 210, 'maliyet': 5200.00, 'notlar': 'Sonraki bakımda X ekseni rulman değişimi planlanmalı. Aşınma %70 seviyesinde.'},
        {'makine_kod': 'CNC-001', 'tur': 'korektif', 'islem': 'Servo motor fan değişimi. Sürücü ünitesi üfleme ile temizlendi. Termal macun yenilendi.', 'tarih': date(2026, 4, 22), 'sure': 65, 'maliyet': 1150.00, 'notlar': None},
        # CNC-002
        {'makine_kod': 'CNC-002', 'tur': 'periyodik', 'islem': 'Soğutma sistemi tam temizlik, pnömatik silindir kontrolü. ATC (otomatik takım değiştirici) mekanizma yağlama.', 'tarih': date(2026, 3, 20), 'sure': 180, 'maliyet': 3800.00, 'notlar': 'Pnömatik valflerden biri sızıntı yapıyor — takibe alındı.'},
        {'makine_kod': 'CNC-002', 'tur': 'korektif', 'islem': 'CNC firmware güncelleme (v5.2 → v5.4). Parametre tablosu yeniden oluşturuldu. Offset kalibrasyonu tamamlandı.', 'tarih': date(2026, 4, 16), 'sure': 45, 'maliyet': 650.00, 'notlar': None},
        # ABK-001
        {'makine_kod': 'ABK-001', 'tur': 'periyodik', 'islem': 'Kilitleme sistemi kontrolü. Basınç testi (280 bar — nominal). Ejektör mekanizması yağlama.', 'tarih': date(2026, 2, 15), 'sure': 180, 'maliyet': 4100.00, 'notlar': 'Kilitleme pimi %45 aşınmış — izlemeye alındı.'},
        {'makine_kod': 'ABK-001', 'tur': 'korektif', 'islem': 'Aşınmış bükme ucu değiştirildi. Geri akış valfi yenilendi. Isıtıcı bantların dirençleri ölçüldü (hepsi tolerans içinde).', 'tarih': date(2026, 4, 28), 'sure': 300, 'maliyet': 18500.00, 'notlar': 'Yeni bükme ucu malzemesi: DC53 takım çeliği. Ömür takibi başlatıldı.'},
        # PRS-001
        {'makine_kod': 'PRS-001', 'tur': 'periyodik', 'islem': 'Hidrolik yağ filtresi değişimi (10μm). Hortum muayenesi, keçe kontrolü. Yağ numunesi laboratuvara gönderildi.', 'tarih': date(2026, 2, 10), 'sure': 150, 'maliyet': 3200.00, 'notlar': 'Sol silindir keçesinde başlangıç sızıntısı — acil değişim planlı.'},
        {'makine_kod': 'PRS-001', 'tur': 'acil', 'islem': 'Hidrolik piston keçe seti acil değişimi. Sistem yağı filtrelenerek temizlendi. Basınç testi yapıldı.', 'tarih': date(2026, 5, 1), 'sure': 360, 'maliyet': 12800.00, 'notlar': 'Keçe ömrü beklenenden kısa — yağ kalitesi araştırılacak.'},
        # KYN-001
        {'makine_kod': 'KYN-001', 'tur': 'periyodik', 'islem': 'Tüm eksen yağlama. Kablo kanalı muayenesi. TCP kalibrasyonu. Ark sensörü temizliği.', 'tarih': date(2026, 4, 1), 'sure': 240, 'maliyet': 7800.00, 'notlar': 'TCP sapması 0.08mm — kabul edilebilir (limit: 0.1mm).'},
        # TSL-001
        {'makine_kod': 'TSL-001', 'tur': 'periyodik', 'islem': 'Taşlama mili filtre değişimi. Geometrik doğruluk ölçümü. Soğutma suyu debisi kontrolü.', 'tarih': date(2026, 4, 20), 'sure': 120, 'maliyet': 2400.00, 'notlar': 'Silindiriklik sapması: 1.2μm — kabul edilebilir (limit: 2μm).'},
        # LZR-001
        {'makine_kod': 'LZR-001', 'tur': 'periyodik', 'islem': 'Lazer lens temizliği, koruyucu cam değişimi. Nozul kontrol ve kalibrasyon. Kesim gazı basınç testi.', 'tarih': date(2026, 5, 5), 'sure': 180, 'maliyet': 9500.00, 'notlar': 'Lens kontaminasyonu normal seviyede. 6000W çıkış gücü: 5980W (normal).'},
        {'makine_kod': 'LZR-001', 'tur': 'korektif', 'islem': 'Kesim tablası kızak yağlama pompası değişimi. Kızak temizliği ve yeniden gres uygulaması.', 'tarih': date(2026, 4, 10), 'sure': 150, 'maliyet': 4200.00, 'notlar': None},
        # MNT-001
        {'makine_kod': 'MNT-001', 'tur': 'periyodik', 'islem': 'Konveyör bant gergi ayarı. Pnömatik silindir muayenesi. Sensör kalibrasyonu. Motor yağlama.', 'tarih': date(2026, 3, 15), 'sure': 90, 'maliyet': 1800.00, 'notlar': 'Bant aşınması %30 — bir sonraki bakımda değişim gerekebilir.'},
        {'makine_kod': 'MNT-001', 'tur': 'periyodik', 'islem': 'Montaj tablası titreşim ölçümü. Vidalar torklama kontrolü. Bant gerginliği yeniden ayarlandı.', 'tarih': date(2026, 5, 15), 'sure': 120, 'maliyet': 2100.00, 'notlar': 'Pnömatik silindir 3 ve 7 hava kaçağı var. Conta değişimi planlandı.'},
    ]

    for b in bakimlar:
        makine = m_kodlari.get(b['makine_kod'])
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
        print(f'  + Bakım: {b["makine_kod"]} — {b["tur"]} (₺{b["maliyet"]:,.0f})')

    db.session.flush()

    # ── DURUŞ KAYITLARI (Son 21 gün) ──
    print('[6/22] Duruş kayıtları...')

    durus_sablonlari = {
        'ariza': [
            ('Servo motor alarm', 'Servo sürücüden E-07 alarm kodu geldi. Makine acil durduruldu.'),
            ('Sensör hatası', 'Proksimiti sensör sinyal kaybı yaşandı. Parça tespiti yapılamıyor.'),
            ('Hidrolik sızıntı', 'Basınç hattında yağ damlası tespit edildi. Güvenlik protokolü uygulandı.'),
            ('PLC iletişim hatası', 'PLC-HMI arası haberleşme koptu. Operatör panel kararıyor.'),
            ('Lazer güç düşüşü', 'Rezonatör çıkış gücü nominal altına düştü. Otomatik koruma devreye girdi.'),
        ],
        'setup': [
            ('Kalıp/takım değişimi', 'Planlı kalıp/takım seti değişimi. SMED prosedürü uygulandı.'),
            ('Program değişikliği', 'Yeni ürün programı yüklendi, simülasyon ve ilk parça onayı alındı.'),
            ('Fikstür ayarı', 'İş parçası bağlama fikstürü değiştirildi. Referans noktası sıfırlandı.'),
            ('Lazer nozul değişimi', 'Kesim nozulu aşındı, yenisi takıldı. Odak mesafesi ayarlandı.'),
        ],
        'malzeme_bekleme': [
            ('Hammadde gecikmesi', 'Tedarikçi teslimatı planlanandan 2 saat geç geldi.'),
            ('Yarı mamul bekleme', 'Önceki operasyondan gelen parça hazır değil. Hat dengesizliği.'),
            ('Kalite onayı bekleme', 'İlk parça kalite onayı bekleniyor. Ölçüm laboratuvarı yoğun.'),
        ],
        'kalip_degisim': [
            ('Planlı kalıp bakımı', 'Kalıp bakım prosedürü uygulandı. Parlatma ve temizlik yapıldı.'),
            ('Kalıp temizliği', 'Üretim araçları sökülerek kimyasal temizlik yapıldı.'),
        ],
        'plansiz_mola': [
            ('Personel molası', 'Vardiya ara molası (öğle yemeği).'),
            ('Vardiya devir teslim', 'Vardiya geçişinde bilgilendirme ve devir teslim yapıldı.'),
            ('Acil toplantı', 'Kalite sorunu nedeniyle acil üretim toplantısı yapıldı.'),
        ],
        'enerji_kesintisi': [
            ('Elektrik kesintisi', 'Fabrika genelinde plansız elektrik kesintisi (TEDAŞ kaynaklı).'),
            ('Basınçlı hava düşüşü', 'Kompresör arızası nedeniyle hat basıncı 4 bar altına düştü.'),
            ('Soğutma suyu kesintisi', 'Chiller ünitesi arızası nedeniyle soğutma suyu devresi durdu.'),
        ],
    }

    kategoriler = list(durus_sablonlari.keys())
    kategori_agirliklari = [0.25, 0.25, 0.15, 0.10, 0.15, 0.10]

    for gun in range(21, 0, -1):
        tarih = bugun - timedelta(days=gun)
        if tarih.weekday() == 6:  # Pazar
            continue
        durus_sayisi = random.randint(2, 5)
        for _ in range(durus_sayisi):
            makine = random.choice(makineler)
            kat = random.choices(kategoriler, weights=kategori_agirliklari, k=1)[0]
            neden, aciklama = random.choice(durus_sablonlari[kat])
            saat = random.randint(6, 22)
            dakika = random.choice([0, 15, 30, 45])
            bas = datetime(tarih.year, tarih.month, tarih.day, saat, dakika, tzinfo=timezone.utc)
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
    print('  + 21 günlük kategorize duruş kayıtları (6 kategori) oluşturuldu\n')
