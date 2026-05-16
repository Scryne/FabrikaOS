"""
FabrikaOS — Stok, Malzeme ve Tedarikçi Demo Verisi
Senaryo: AnadoluTech Metal Sanayi — Gerçekçi endüstriyel stok yönetimi

- 7 tedarikçi (Türkiye'nin bilinen sanayi firmaları)
- 12 malzeme (Kesici takım, yağ, rulman, elektrik, KKD, hammadde...)
- 18+ stok hareketi (giriş/çıkış, fatura numaralı)
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from app.extensions import db
from app.models.stok import Malzeme, StokHareketi, Tedarikci
from app.models.kullanici import Kullanici


def seed():
    print('[7/12] Tedarikçiler ve Stok...')

    # ── TEDARİKÇİLER ──
    tedarikciler = [
        {
            'ad': 'Borusan Mannesmann',
            'yetkili_kisi': 'Kemal Yıldırım',
            'telefon': '0262 677 30 00',
            'eposta': 'kemal.yildirim@borusan.com.tr',
            'adres': 'Kocaeli Gebze Organize Sanayi Bölgesi, D-101 Cad. No:15',
            'ortalama_teslimat_gun': 5,
            'performans_puani': 4.5,
        },
        {
            'ad': 'Kardemir Karabük Demir Çelik',
            'yetkili_kisi': 'Sevda Akın',
            'telefon': '0370 418 90 00',
            'eposta': 'sevda.akin@kardemir.com',
            'adres': 'Karabük OSB, 2. Cadde No:15',
            'ortalama_teslimat_gun': 7,
            'performans_puani': 4.0,
        },
        {
            'ad': 'Petrol Ofisi Endüstriyel Yağlar',
            'yetkili_kisi': 'Burak Demirtaş',
            'telefon': '0216 578 70 00',
            'eposta': 'burak.demirtas@poas.com.tr',
            'adres': 'İstanbul Kartal, Yakacık Cad. No:111',
            'ortalama_teslimat_gun': 3,
            'performans_puani': 4.7,
        },
        {
            'ad': 'SKF Türkiye',
            'yetkili_kisi': 'Derya Korkmaz',
            'telefon': '0216 578 40 00',
            'eposta': 'derya.korkmaz@skf.com',
            'adres': 'İstanbul Dudullu OSB, 2. Sanayi Cad. No:8',
            'ortalama_teslimat_gun': 4,
            'performans_puani': 4.8,
        },
        {
            'ad': 'Siemens Türkiye',
            'yetkili_kisi': 'Cenk Aydın',
            'telefon': '0216 459 20 00',
            'eposta': 'cenk.aydin@siemens.com.tr',
            'adres': 'İstanbul Yakacık, Siemens Fabrikası',
            'ortalama_teslimat_gun': 6,
            'performans_puani': 4.6,
        },
        {
            'ad': 'Sandvik Coromant Türkiye',
            'yetkili_kisi': 'Tuğrul Kaya',
            'telefon': '0216 574 31 00',
            'eposta': 'tugrul.kaya@sandvik.com',
            'adres': 'İstanbul Tuzla OSB',
            'ortalama_teslimat_gun': 3,
            'performans_puani': 4.9,
        },
        {
            'ad': 'Atlas Copco Kompresör',
            'yetkili_kisi': 'Sinem Çetin',
            'telefon': '0262 648 58 00',
            'eposta': 'sinem.cetin@atlascopco.com',
            'adres': 'Kocaeli Gebze OSB, 3. Bölge',
            'ortalama_teslimat_gun': 5,
            'performans_puani': 4.3,
        },
        {
            'ad': 'Erdemir Demir Çelik',
            'yetkili_kisi': 'Ali Vefa',
            'telefon': '0372 329 30 00',
            'eposta': 'ali.vefa@erdemir.com.tr',
            'adres': 'Zonguldak Karadeniz Ereğli',
            'ortalama_teslimat_gun': 4,
            'performans_puani': 4.6,
        }
    ]

    for t_data in tedarikciler:
        if Tedarikci.query.filter_by(ad=t_data['ad']).first():
            continue
        t = Tedarikci(**t_data, aktif=True)
        db.session.add(t)
        print(f'  + Tedarikçi: {t_data["ad"]}')

    db.session.flush()
    ted_ids = {t.ad: t.id for t in Tedarikci.query.all()}

    # ── MALZEMELER (12 kalem) ──
    malzemeler = [
            {'ad': 'CNC Kesici Uç CNMG 120408', 'kod': 'MLZ-001', 'birim': 'adet', 'kategori': 'Kesici Takım', 'lokasyon': 'Raf A-01', 'birim_fiyat': 92.50, 'mevcut_miktar': 145, 'minimum_stok': 50, 'tedarikci_id': ted_ids.get('Sandvik Coromant Türkiye')},
            {'ad': 'Parmak Freze Ø12 (HSS-Co)', 'kod': 'MLZ-010', 'birim': 'adet', 'kategori': 'Kesici Takım', 'lokasyon': 'Raf A-02', 'birim_fiyat': 185.00, 'mevcut_miktar': 28, 'minimum_stok': 15, 'tedarikci_id': ted_ids.get('Sandvik Coromant Türkiye')},
            {'ad': 'Hidrolik Yağ (ISO VG 46)', 'kod': 'MLZ-002', 'birim': 'litre', 'kategori': 'Endüstriyel Yağ', 'lokasyon': 'Depo B-03', 'birim_fiyat': 45.80, 'mevcut_miktar': 280, 'minimum_stok': 100, 'tedarikci_id': ted_ids.get('Petrol Ofisi Endüstriyel Yağlar')},
            {'ad': 'CNC Soğutma Sıvısı (Emülsiyon)', 'kod': 'MLZ-007', 'birim': 'litre', 'kategori': 'Endüstriyel Yağ', 'lokasyon': 'Depo B-05', 'birim_fiyat': 62.00, 'mevcut_miktar': 95, 'minimum_stok': 50, 'tedarikci_id': ted_ids.get('Petrol Ofisi Endüstriyel Yağlar')},
            {'ad': 'Bilyalı Rulman SKF 6205-2RS', 'kod': 'MLZ-003', 'birim': 'adet', 'kategori': 'Rulman/Yatak', 'lokasyon': 'Raf C-02', 'birim_fiyat': 148.00, 'mevcut_miktar': 22, 'minimum_stok': 10, 'tedarikci_id': ted_ids.get('SKF Türkiye')},
            {'ad': 'MIG Kaynak Teli ER70S-6 (Ø1.0mm)', 'kod': 'MLZ-004', 'birim': 'kg', 'kategori': 'Kaynak Malzemesi', 'lokasyon': 'Raf D-01', 'birim_fiyat': 105.00, 'mevcut_miktar': 42, 'minimum_stok': 25, 'tedarikci_id': ted_ids.get('Borusan Mannesmann')},
            {'ad': 'Siemens S7-1200 PLC CPU Modülü', 'kod': 'MLZ-005', 'birim': 'adet', 'kategori': 'Otomasyon / Elektronik', 'lokasyon': 'Raf E-01', 'birim_fiyat': 4250.00, 'mevcut_miktar': 2, 'minimum_stok': 1, 'tedarikci_id': ted_ids.get('Siemens Türkiye')},
            {'ad': 'Proksimiti Sensör (M12, NPN)', 'kod': 'MLZ-009', 'birim': 'adet', 'kategori': 'Otomasyon / Elektronik', 'lokasyon': 'Raf E-03', 'birim_fiyat': 320.00, 'mevcut_miktar': 8, 'minimum_stok': 5, 'tedarikci_id': ted_ids.get('Siemens Türkiye')},
            {'ad': 'Nitril Kesim Dirençli Eldiven', 'kod': 'MLZ-006', 'birim': 'adet', 'kategori': 'KKD', 'lokasyon': 'Raf F-02', 'birim_fiyat': 38.50, 'mevcut_miktar': 12, 'minimum_stok': 40, 'tedarikci_id': ted_ids.get('Kardemir Karabük Demir Çelik')},
            {'ad': 'St37 Çelik Levha (2mm, 1500×3000)', 'kod': 'MLZ-008', 'birim': 'kg', 'kategori': 'Hammadde', 'lokasyon': 'Depo A-01', 'birim_fiyat': 24.80, 'mevcut_miktar': 1200, 'minimum_stok': 500, 'tedarikci_id': ted_ids.get('Kardemir Karabük Demir Çelik')},
            {'ad': 'Alüminyum Çubuk (Ø25, 6082-T6)', 'kod': 'MLZ-011', 'birim': 'kg', 'kategori': 'Hammadde', 'lokasyon': 'Depo A-03', 'birim_fiyat': 85.00, 'mevcut_miktar': 180, 'minimum_stok': 80, 'tedarikci_id': ted_ids.get('Borusan Mannesmann')},
            {'ad': 'Kompresör Yağ Filtresi (Atlas Copco)', 'kod': 'MLZ-012', 'birim': 'adet', 'kategori': 'Filtre / Sarf', 'lokasyon': 'Raf G-01', 'birim_fiyat': 520.00, 'mevcut_miktar': 3, 'minimum_stok': 2, 'tedarikci_id': ted_ids.get('Atlas Copco Kompresör')},
        ]
    hareketler = [
        ('MLZ-001', 'giris', 80, 92.50, 'FTR-2026-0412', 'Sandvik sipariş teslimatı — 80 adet CNMG uç', 28),
        ('MLZ-001', 'cikis', 15, None, None, 'CNC-001 ve CNC-002 için takım değişimi', 20),
        ('MLZ-001', 'cikis', 8, None, None, 'Müşteri acil sipariş — ek takım tüketimi', 10),
        ('MLZ-010', 'giris', 20, 185.00, 'FTR-2026-0445', 'Parmak freze haftalık sipariş', 14),
        ('MLZ-002', 'giris', 200, 45.80, 'FTR-2026-0398', 'Petrol Ofisi aylık teslimat — 200L HLP 46', 25),
        ('MLZ-002', 'cikis', 35, None, None, 'PRS-001 hidrolik yağ ikmali', 15),
        ('MLZ-007', 'giris', 50, 62.00, 'FTR-2026-0430', 'CNC soğutma sıvısı ikmali', 12),
        ('MLZ-003', 'giris', 15, 148.00, 'FTR-2026-0401', 'SKF rulman sipariş teslimatı', 22),
        ('MLZ-003', 'cikis', 3, None, None, 'TSL-001 taşlama mil rulmanı değişimi', 8),
        ('MLZ-004', 'giris', 30, 105.00, 'FTR-2026-0410', 'Borusan kaynak teli teslimatı — 30 kg', 21),
        ('MLZ-004', 'cikis', 18, None, None, 'KYN-001 kaynak robotu aylık tüketim', 7),
        ('MLZ-006', 'giris', 100, 38.50, 'FTR-2026-0420', 'KKD yenileme siparişi — 100 çift eldiven', 18),
        ('MLZ-006', 'cikis', 88, None, None, 'Tüm departmanlara dağıtım (üretim + bakım)', 5),
        ('MLZ-008', 'giris', 800, 24.80, 'FTR-2026-0415', 'Kardemir haftalık çelik levha siparişi', 16),
        ('MLZ-008', 'cikis', 350, None, None, 'PRS-001 pres hattı — aylık levha tüketimi', 9),
        ('MLZ-008', 'cikis', 180, None, None, 'KYN-001 kaynak hattı — şase üretimi', 3),
        ('MLZ-011', 'giris', 100, 85.00, 'FTR-2026-0440', 'Alüminyum çubuk sipariş teslimatı', 11),
        ('MLZ-012', 'giris', 2, 520.00, 'FTR-2026-0425', 'Atlas Copco kompresör filtresi', 13),
    ]

    for m_data in malzemeler:
        if Malzeme.query.filter_by(kod=m_data['kod']).first():
            continue
        m = Malzeme(**m_data, aktif=True)
        db.session.add(m)
        print(f'  + Malzeme: {m_data["ad"]} ({m_data["kod"]})')

    db.session.flush()

    # ── STOK HAREKETLERİ (18 işlem) ──
    admin = Kullanici.query.filter_by(kullanici_adi='admin').first()
    admin_id = admin.id if admin else 1

    for kod, tur, miktar, fiyat, fatura, neden, gun_once in hareketler:
        malzeme = Malzeme.query.filter_by(kod=kod).first()
        if not malzeme:
            continue
        h = StokHareketi(
            malzeme_id=malzeme.id,
            hareket_turu=tur,
            miktar=miktar,
            birim_fiyat=fiyat,
            fatura_no=fatura,
            neden=neden,
            islem_yapan_id=admin_id,
            tarih=datetime.now(timezone.utc) - timedelta(days=gun_once),
        )
        db.session.add(h)

    db.session.flush()
    print('  + Stok hareketleri oluşturuldu\n')
