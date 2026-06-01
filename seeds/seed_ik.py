"""
FabrikaOS — İK Alt Modülleri Demo Verisi (v2 — Tam Kapsam)
Savunma, Fazla Mesai, Sertifika, Maaş Skalası, Zimmet, Giriş/Çıkış Evrakları
"""
import random
from datetime import date, datetime, timedelta, timezone, time
from app.extensions import db
from app.models.ik import SavunmaTutanak, FazlaMesai, SertifikaTakip, MaasSkalasi, ZimmetKaydi, GirisCikisEvrak
from app.models.personel import Calisan
from app.models.kullanici import Kullanici


def seed():
    print('[17/22] İnsan Kaynakları Alt Modülleri...')
    random.seed(111)

    bugun = date.today()
    calisanlar = Calisan.query.filter_by(aktif=True).all()
    ik_uzmani = Kullanici.query.filter_by(kullanici_adi='zeynep.arslan').first() or Kullanici.query.first()
    admin = Kullanici.query.filter_by(kullanici_adi='admin').first()

    # ── SAVUNMA VE TUTANAKLAR (5) ──
    tutanaklar = [
        {'sicil': 'P005', 'tur': 'tutanak', 'konu': 'İşe Geç Gelme', 'aciklama': 'Pazartesi günü vardiyaya 45 dk geç katılım sağladı.', 'durum': 'kapatildi', 'karar': 'Sözlü Uyarı', 'gun_once': 45},
        {'sicil': 'P012', 'tur': 'savunma', 'konu': 'KKD Kullanmama', 'aciklama': 'Taşlama esnasında yan siperlikli gözlük kullanmadığı İSG uzmanı tarafından tespit edildi.', 'durum': 'acik', 'karar': None, 'gun_once': 2},
        {'sicil': 'P007', 'tur': 'tutanak', 'konu': 'Amirle Tartışma', 'aciklama': 'Vardiya sırasında üretim planı konusunda amiriyle sesli tartışma yaşadı.', 'durum': 'itiraz_edildi', 'karar': 'Yazılı İhtar', 'gun_once': 15},
        {'sicil': 'P016', 'tur': 'savunma', 'konu': 'Hatalı Üretim (Hurda)', 'aciklama': 'Lazer kesimde yanlış parametre girerek 5 adet sacın hurdaya çıkmasına sebep oldu.', 'durum': 'kapatildi', 'karar': 'Eğitim Tekrarı', 'gun_once': 60},
        {'sicil': 'P004', 'tur': 'tutanak', 'konu': 'İzinsiz Görev Yeri Terk', 'aciklama': 'Vardiya bitmeden 15 dk önce atölyeyi izinsiz terk ettiği kamera kayıtlarından tespit edildi.', 'durum': 'acik', 'karar': None, 'gun_once': 5},
    ]

    for t in tutanaklar:
        c = next((x for x in calisanlar if x.sicil_no == t['sicil']), random.choice(calisanlar))
        st = SavunmaTutanak(
            calisan_id=c.id,
            olusturan_id=ik_uzmani.id,
            olusturma_tarihi=datetime.combine(bugun - timedelta(days=t['gun_once']), time(9, 0)).replace(tzinfo=timezone.utc),
            tur=t['tur'],
            konu=t['konu'],
            icerik=t['aciklama'],
            karar=t['karar'],
            durum=t['durum']
        )
        db.session.add(st)

    # ── FAZLA MESAİLER (10) ──
    mesai_nedenleri = ['Acil Müşteri Siparişi', 'Makine Arızası Sebebiyle Gecikme', 'Hafta Sonu Bakım Desteği', 'Sayım Öncesi Hazırlık']
    for _ in range(10):
        c = random.choice(calisanlar)
        gun_once = random.randint(1, 30)
        tarih = bugun - timedelta(days=gun_once)
        saat = random.choice([2, 3, 4, 8])
        durum = random.choices(['bekliyor', 'onaylandi', 'reddedildi'], weights=[0.2, 0.7, 0.1])[0]

        fm = FazlaMesai(
            calisan_id=c.id,
            tarih=tarih,
            baslangic_saati=time(18, 0),
            bitis_saati=time(min(23, 18 + saat), 0),
            toplam_saat=saat,
            neden=random.choice(mesai_nedenleri),
            onaylayan_id=admin.id if durum != 'bekliyor' else None,
            onay_durumu=durum,
        )
        db.session.add(fm)

    # ── SERTİFİKA TAKİBİ (12) ──
    sertifikalar = [
        ('CNC İleri Düzey Programlama', 'Tezmaksan Akademi', 60),
        ('Mesleki Yeterlilik Belgesi (MYK) - Çelik Kaynakçısı', 'TÜV AUSTRIA', 24),
        ('Endüstriyel Robot Programlama', 'FANUC', 36),
        ('İlk Yardım Sertifikası', 'Kızılay', 12),
        ('Forklift Operatörlük Belgesi', 'MEB', 60),
    ]
    for _ in range(12):
        c = random.choice(calisanlar)
        sert, kurum, ay = random.choice(sertifikalar)
        gecmis = random.randint(5, int(ay * 30 * 1.2))
        alim = bugun - timedelta(days=gecmis)
        bitis = alim + timedelta(days=ay * 30)
        durum = 'suresi_doldu' if bitis < bugun else 'gecerli'

        stk = SertifikaTakip(
            calisan_id=c.id,
            sertifika_adi=sert,
            veren_kurum=kurum,
            verilis_tarihi=alim,
            gecerlilik_bitis=bitis,
            durum=durum,
        )
        db.session.add(stk)

    # ── MAAŞ SKALASI (Tüm Çalışanlar) ──
    donem_baslangic = bugun.replace(day=1)
    for c in calisanlar:
        taban = float(c.ucret or 35000)
        mesai = random.randint(0, 5000)
        ikramiye = 0
        if c.departman == 'Yönetim' or (bugun.month in [1, 4, 7, 10]):
            ikramiye = taban * 0.5
        kesinti = 0
        if random.random() < 0.1:
            kesinti = random.randint(500, 2000)

        ms = MaasSkalasi(
            calisan_id=c.id,
            donem_baslangic=donem_baslangic,
            brut_maas=taban * 1.4,
            net_maas=taban + mesai + ikramiye - kesinti,
            ek_odeme=mesai + ikramiye,
            ek_odeme_aciklama="Mesai + İkramiye" if (mesai + ikramiye) > 0 else None
        )
        db.session.add(ms)

    # ── ZİMMET KAYITLARI (10) ──
    zimmetler = [
        ('Laptop', 'Lenovo ThinkPad E15', 'SN: PF2B9Z', 'P014'),
        ('Cep Telefonu', 'Samsung Galaxy A53', 'IMEI: 3546...', 'P007'),
        ('Kumpas', 'Mitutoyo Dijital 150mm', 'Kal.No: 0012', 'P006'),
        ('Araç', 'Fiat Egea (41 ABC 123)', 'Ruhsat', 'P008'),
        ('Tork Anahtarı', 'Gedore Dremometer', '10-100 Nm', 'P003'),
    ]
    for _ in range(10):
        esz, marka, seri, def_sicil = random.choice(zimmetler)
        c = next((x for x in calisanlar if x.sicil_no == def_sicil), random.choice(calisanlar))
        teslim_tarihi = c.ise_baslama + timedelta(days=random.randint(1, 10))
        if teslim_tarihi > bugun:
            teslim_tarihi = bugun - timedelta(days=5)

        iade_durumu = random.choices([False, True], weights=[0.8, 0.2])[0]

        zk = ZimmetKaydi(
            calisan_id=c.id,
            demirbas_adi=esz,
            seri_no=seri,
            teslim_tarihi=teslim_tarihi,
            durum='iade_edildi' if iade_durumu else 'teslim_edildi',
            iade_tarihi=bugun - timedelta(days=random.randint(1, 30)) if iade_durumu else None,
            notlar=marka
        )
        db.session.add(zk)

    # ── GİRİŞ ÇIKIŞ EVRAKLARI ──
    # Yeni giren personellerin evrakları
    for c in calisanlar:
        if (bugun - c.ise_baslama).days < 180:
            evrak_listesi = [
                ('İş Sözleşmesi', 'tamamlandi'),
                ('SGK İşe Giriş Bildirgesi', 'tamamlandi'),
                ('Sağlık Raporu', 'tamamlandi'),
                ('Sabıka Kaydı', 'tamamlandi'),
                ('Diploma Fotokopisi', random.choices(['tamamlandi', 'eksik'], weights=[0.7, 0.3])[0]),
                ('İSG Taahhütnamesi', random.choices(['tamamlandi', 'bekliyor'], weights=[0.8, 0.2])[0]),
            ]

            for e_adi, e_durum in evrak_listesi:
                gce = GirisCikisEvrak(
                    calisan_id=c.id,
                    evrak_adi=e_adi,
                    evrak_turu='ise_giris',
                    durum=e_durum,
                    tamamlama_tarihi=c.ise_baslama if e_durum == 'tamamlandi' else None,
                )
                db.session.add(gce)

    db.session.flush()
    print('  OK\n')
