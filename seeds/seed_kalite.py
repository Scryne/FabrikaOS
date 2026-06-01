"""
FabrikaOS — Kalite Kontrol Demo Verisi (v2 — Genişletilmiş)
12 hata kaydı (tüm kategoriler), 8 CAPA düzeltici faaliyet (tüm durumlar)
"""
import random
from datetime import date, datetime, timedelta, timezone
from app.extensions import db
from app.models.kalite import HataKaydi, DuzelticiFaaliyet
from app.models.makine import Makine
from app.models.personel import Calisan
from app.models.kullanici import Kullanici


def seed():
    print('[9/22] Kalite kontrol...')
    random.seed(1234)

    bugun = date.today()
    makineler = Makine.query.filter_by(aktif=True).all()
    kk_calisanlar = Calisan.query.filter_by(departman='Kalite Kontrol', aktif=True).all()
    admin = Kullanici.query.filter_by(kullanici_adi='admin').first()

    makine_map = {m.kod: m for m in makineler}

    # ── HATA KAYITLARI (12) ──
    hatalar = [
        # Ölçüsel hatalar
        {'makine_kod': 'CNC-001', 'hata_turu': 'olcusel',
         'urun': 'Çap tolerans aşımı — Ø45 mil parçası',
         'kategori': 'olcusel', 'kaynak': 'makine',
         'parti_no': 'LOT-2026-04-0182', 'red_miktari': 7, 'toplam_miktar': 200, 'gun_once': 5, 'durum': 'acik'},
        {'makine_kod': 'CNC-002', 'hata_turu': 'olcusel',
         'urun': 'Delik pozisyon sapması — Motor bağlantı plakası',
         'kategori': 'olcusel', 'kaynak': 'metot',
         'parti_no': 'LOT-2026-04-0195', 'red_miktari': 4, 'toplam_miktar': 150, 'gun_once': 8, 'durum': 'acik'},
        {'makine_kod': 'TSL-001', 'hata_turu': 'olcusel',
         'urun': 'Silindiriklik sapması — Rulman mili',
         'kategori': 'olcusel', 'kaynak': 'makine',
         'parti_no': 'LOT-2026-05-0210', 'red_miktari': 3, 'toplam_miktar': 80, 'gun_once': 3, 'durum': 'acik'},

        # Yüzey hataları
        {'makine_kod': 'LZR-001', 'hata_turu': 'yuzey',
         'urun': 'Lazer kesim kenar kalitesi düşük',
         'kategori': 'yuzey', 'kaynak': 'makine',
         'parti_no': 'LOT-2026-05-0225', 'red_miktari': 15, 'toplam_miktar': 300, 'gun_once': 4, 'durum': 'acik'},
        {'makine_kod': 'ABK-001', 'hata_turu': 'yuzey',
         'urun': 'Bükme izleri — Paslanmaz panel',
         'kategori': 'yuzey', 'kaynak': 'makine',
         'parti_no': 'LOT-2026-04-0188', 'red_miktari': 2, 'toplam_miktar': 100, 'gun_once': 15, 'durum': 'kapandi'},

        # Montaj hataları
        {'makine_kod': 'MNT-001', 'hata_turu': 'montaj',
         'urun': 'Yanlış vida torku — Motor bağlantısı',
         'kategori': 'montaj', 'kaynak': 'iscilik',
         'parti_no': 'LOT-2026-05-0232', 'red_miktari': 3, 'toplam_miktar': 50, 'gun_once': 2, 'durum': 'acik'},
        {'makine_kod': 'KYN-001', 'hata_turu': 'montaj',
         'urun': 'Kaynak dikiş pozisyon sapması',
         'kategori': 'montaj', 'kaynak': 'makine',
         'parti_no': 'LOT-2026-04-0201', 'red_miktari': 5, 'toplam_miktar': 120, 'gun_once': 12, 'durum': 'kapandi'},

        # Malzeme hataları
        {'makine_kod': 'PRS-001', 'hata_turu': 'malzeme',
         'urun': 'Hammadde sertlik sapması — HRP Sac',
         'kategori': 'malzeme', 'kaynak': 'malzeme',
         'parti_no': 'LOT-2026-04-0175', 'red_miktari': 0, 'toplam_miktar': 40, 'gun_once': 18, 'durum': 'kapandi'},
        {'makine_kod': 'CNC-001', 'hata_turu': 'malzeme',
         'urun': 'Çelik çubukta iç çatlak',
         'kategori': 'malzeme', 'kaynak': 'malzeme',
         'parti_no': 'LOT-2026-05-0218', 'red_miktari': 8, 'toplam_miktar': 60, 'gun_once': 6, 'durum': 'acik'},

        # Boyut dışı hatalar
        {'makine_kod': 'LZR-001', 'hata_turu': 'olcusel',
         'urun': 'Lazer kesim boyut sapması — Flanş parçası',
         'kategori': 'olcusel', 'kaynak': 'makine',
         'parti_no': 'LOT-2026-05-0228', 'red_miktari': 6, 'toplam_miktar': 200, 'gun_once': 7, 'durum': 'acik'},
        {'makine_kod': 'ABK-001', 'hata_turu': 'olcusel',
         'urun': 'Bükme açısı sapması — Braket',
         'kategori': 'olcusel', 'kaynak': 'metot',
         'parti_no': 'LOT-2026-03-0165', 'red_miktari': 10, 'toplam_miktar': 500, 'gun_once': 30, 'durum': 'kapandi'},
    ]

    hata_objeleri = []
    for h in hatalar:
        makine = makine_map.get(h['makine_kod'])
        if not makine:
            continue
        raporlayan = random.choice(kk_calisanlar) if kk_calisanlar else None

        hk = HataKaydi(
            makine_id=makine.id,
            urun_adi=h['urun'],
            hata_turu=h['hata_turu'],
            hata_kategorisi=h['kategori'],
            hata_kaynagi=h['kaynak'],
            parti_no=h.get('parti_no'),
            adet=random.randint(1, 15),
            fire_orani=random.uniform(0.5, 5.0),
            kaydeden_id=1,
            tarih=datetime.now(timezone.utc) - timedelta(days=h['gun_once']),
            olusturma_tarihi=datetime.now(timezone.utc) - timedelta(days=h['gun_once']),
        )
        db.session.add(hk)
        hata_objeleri.append(hk)

    db.session.flush()

    # ── DÜZELTİCİ FAALİYETLER / CAPA (8) ──
    print('[10/22] CAPA / Düzeltici faaliyetler...')

    capalar = [
        {'faaliyet': 'Takım aşınma izleme sistemi kurulumu',
         'kok_neden': 'Takım aşınmasının zamanında tespit edilememesi. Operatör deneyimine bağımlılık.',
         'durum': 'devam', 'hedef_gun': 30},
        {'faaliyet': 'Lazer nozul temizlik prosedürü iyileştirme',
         'kok_neden': 'Nozul kontaminasyonu nedeniyle odak mesafesi sapması.',
         'durum': 'acik', 'hedef_gun': 14},
        {'faaliyet': 'Tork kontrol kalibrasyon programı',
         'kok_neden': 'Tork anahtarı kalibrasyonunun düzenli yapılmaması. Son kalibrasyon 8 ay önce.',
         'durum': 'dogrulama', 'hedef_gun': 7},
        {'faaliyet': 'Tedarikçi giriş kalite kontrolü sıkılaştırma',
         'kok_neden': 'Tedarikçi kalite sertifikalarına güvenilmesi, giriş kontrolünün atlanması.',
         'durum': 'kapandi', 'hedef_gun': 21},
        {'faaliyet': 'Robot TCP kalibrasyon periyodu kısaltma',
         'kok_neden': 'TCP sapmasının periyodik bakım döngüsü içinde büyümesi.',
         'durum': 'kapandi', 'hedef_gun': 14},
        {'faaliyet': 'Spring-back kompanzasyon tablosu güncelleme',
         'kok_neden': 'Mevcut kompanzasyon değerleri güncel malzeme partileri için yeterli değil.',
         'durum': 'devam', 'hedef_gun': 21},
        {'faaliyet': 'Ultrasonik test prosedürü oluşturma',
         'kok_neden': 'İç çatlak kusurlarının talaşlı işlem sırasında ortaya çıkması — %100 kontrol yapılmaması.',
         'durum': 'acik', 'hedef_gun': 45},
        {'faaliyet': 'Taşlama taşı ömür takip sistemi',
         'kok_neden': 'Taşlama taşının aşırı kullanılması nedeniyle yüzey kalitesinde düşüş.',
         'durum': 'dogrulama', 'hedef_gun': 21},
    ]

    for i, c in enumerate(capalar):
        hata = hata_objeleri[i] if i < len(hata_objeleri) else hata_objeleri[0]

        df = DuzelticiFaaliyet(
            hata_kaydi_id=hata.id,
            faaliyet=c['faaliyet'],
            kok_neden=c['kok_neden'],
            durum=c['durum'],
            sorumlu_id=1,
            hedef_tarih=bugun + timedelta(days=c['hedef_gun']),
            olusturma_tarihi=datetime.now(timezone.utc) - timedelta(days=random.randint(3, 20)),
        )
        db.session.add(df)

    db.session.flush()
    print('  OK\n')
