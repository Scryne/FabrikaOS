"""
FabrikaOS — Stok Yönetimi Demo Verisi (v2 — Genişletilmiş)
10 tedarikçi, 18 malzeme (5 kritik stok), 30+ stok hareketi
"""
import random
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from app.extensions import db
from app.models.stok import Tedarikci, Malzeme, StokHareketi
from app.models.kullanici import Kullanici


def seed():
    print('[7/22] Stok yönetimi...')
    random.seed(42)

    admin = Kullanici.query.filter_by(kullanici_adi='admin').first()
    bugun = date.today()

    # ── TEDARİKÇİLER (10) ──
    tedarikciler = [
        {'ad': 'Borusan Mannesmann', 'yetkili_kisi': 'Ercan Koçak', 'telefon': '0216 581 00 00', 'eposta': 'satis@borusan.com', 'adres': 'İstanbul, Kadıköy', 'ortalama_teslimat_gun': 3, 'performans_puani': 4.8},
        {'ad': 'Kardemir Çelik', 'yetkili_kisi': 'Hakan Demir', 'telefon': '0370 418 60 00', 'eposta': 'siparis@kardemir.com.tr', 'adres': 'Karabük', 'ortalama_teslimat_gun': 5, 'performans_puani': 4.2},
        {'ad': 'Castrol Türkiye', 'yetkili_kisi': 'Seda Akçay', 'telefon': '0212 366 11 00', 'eposta': 'satis@castrol.com.tr', 'adres': 'İstanbul, Beylikdüzü', 'ortalama_teslimat_gun': 2, 'performans_puani': 4.9},
        {'ad': 'SKF Türkiye', 'yetkili_kisi': 'Murat Çetin', 'telefon': '0262 679 78 00', 'eposta': 'siparis@skf.com.tr', 'adres': 'Kocaeli, Gebze', 'ortalama_teslimat_gun': 7, 'performans_puani': 4.5},
        {'ad': 'Festo Türkiye', 'yetkili_kisi': 'Aylin Ertürk', 'telefon': '0212 622 65 30', 'eposta': 'satis@festo.com.tr', 'adres': 'İstanbul, Esenyurt', 'ortalama_teslimat_gun': 10, 'performans_puani': 4.0},
        {'ad': 'İzocam', 'yetkili_kisi': 'Selim Boran', 'telefon': '0262 648 74 00', 'eposta': 'siparis@izocam.com.tr', 'adres': 'Kocaeli, Gebze', 'ortalama_teslimat_gun': 4, 'performans_puani': 3.8},
        {'ad': 'Lincoln Electric Türkiye', 'yetkili_kisi': 'Kenan Yavuz', 'telefon': '0216 544 16 00', 'eposta': 'satis@lincolnelectric.com.tr', 'adres': 'İstanbul, Tuzla', 'ortalama_teslimat_gun': 5, 'performans_puani': 4.6},
        {'ad': 'IGUS Türkiye', 'yetkili_kisi': 'Banu Kılıç', 'telefon': '0216 394 52 00', 'eposta': 'siparis@igus.com.tr', 'adres': 'İstanbul, Maltepe', 'ortalama_teslimat_gun': 8, 'performans_puani': 4.3},
        {'ad': 'Misumi Türkiye', 'yetkili_kisi': 'Taner Öz', 'telefon': '0212 320 98 00', 'eposta': 'satis@misumi.com.tr', 'adres': 'İstanbul, Beylikdüzü', 'ortalama_teslimat_gun': 12, 'performans_puani': 4.1},
        {'ad': 'Linde Gaz', 'yetkili_kisi': 'Pınar Şen', 'telefon': '0212 444 56 54', 'eposta': 'siparis@lindegaz.com.tr', 'adres': 'İstanbul, Gebze', 'ortalama_teslimat_gun': 3, 'performans_puani': 4.7},
    ]

    for t_data in tedarikciler:
        t = Tedarikci(**t_data, aktif=True)
        db.session.add(t)
        print(f'  + Tedarikçi: {t_data["ad"]} (⭐{t_data["performans_puani"]})')

    db.session.flush()

    # Tedarikçi ID'lerini al
    teds = {t.ad: t.id for t in Tedarikci.query.all()}

    # ── MALZEMELER (18 — 5'i kritik stok altında) ──
    malzemeler = [
        # Talaşlı imalat malzemeleri
        {'ad': 'CNC Tornalama Ucu (CNMG 120408)', 'kod': 'MLZ-001', 'birim': 'adet', 'kategori': 'Kesici Takım', 'lokasyon': 'Raf A1-01', 'birim_fiyat': 85.00, 'mevcut_miktar': 45, 'minimum_stok': 20, 'tedarikci_id': teds.get('Misumi Türkiye')},
        {'ad': 'CNC Freze Ucu Ø10 HSS', 'kod': 'MLZ-002', 'birim': 'adet', 'kategori': 'Kesici Takım', 'lokasyon': 'Raf A1-02', 'birim_fiyat': 120.00, 'mevcut_miktar': 8, 'minimum_stok': 15, 'tedarikci_id': teds.get('Misumi Türkiye')},  # KRİTİK
        {'ad': 'Taşlama Taşı Ø300 (Alumina)', 'kod': 'MLZ-003', 'birim': 'adet', 'kategori': 'Aşındırıcı', 'lokasyon': 'Raf A2-01', 'birim_fiyat': 450.00, 'mevcut_miktar': 3, 'minimum_stok': 5, 'tedarikci_id': teds.get('Misumi Türkiye')},  # KRİTİK
        # Sac işleme malzemeleri
        {'ad': 'Sac Levha DKP 2mm (1250×2500)', 'kod': 'MLZ-004', 'birim': 'adet', 'kategori': 'Hammadde', 'lokasyon': 'Depo B-Raf 1', 'birim_fiyat': 2800.00, 'mevcut_miktar': 42, 'minimum_stok': 10, 'tedarikci_id': teds.get('Kardemir Çelik')},
        {'ad': 'Sac Levha HRP 3mm (1500×3000)', 'kod': 'MLZ-005', 'birim': 'adet', 'kategori': 'Hammadde', 'lokasyon': 'Depo B-Raf 2', 'birim_fiyat': 4200.00, 'mevcut_miktar': 28, 'minimum_stok': 8, 'tedarikci_id': teds.get('Kardemir Çelik')},
        {'ad': 'Çelik Çubuk Ø45 (Ç1040)', 'kod': 'MLZ-006', 'birim': 'metre', 'kategori': 'Hammadde', 'lokasyon': 'Depo B-Raf 3', 'birim_fiyat': 185.00, 'mevcut_miktar': 120, 'minimum_stok': 30, 'tedarikci_id': teds.get('Borusan Mannesmann')},
        # Sarf malzemeler
        {'ad': 'Soğutma Sıvısı (Henkel Bonderite)', 'kod': 'MLZ-007', 'birim': 'litre', 'kategori': 'Sarf Malzeme', 'lokasyon': 'Raf C1-01', 'birim_fiyat': 42.00, 'mevcut_miktar': 15, 'minimum_stok': 50, 'tedarikci_id': teds.get('Castrol Türkiye')},  # KRİTİK
        {'ad': 'Hidrolik Yağ (Shell Tellus S2 46)', 'kod': 'MLZ-008', 'birim': 'litre', 'kategori': 'Sarf Malzeme', 'lokasyon': 'Raf C1-02', 'birim_fiyat': 68.00, 'mevcut_miktar': 80, 'minimum_stok': 30, 'tedarikci_id': teds.get('Castrol Türkiye')},
        {'ad': 'Gres Yağ (SKF LGMT 2)', 'kod': 'MLZ-009', 'birim': 'kg', 'kategori': 'Sarf Malzeme', 'lokasyon': 'Raf C1-03', 'birim_fiyat': 175.00, 'mevcut_miktar': 12, 'minimum_stok': 5, 'tedarikci_id': teds.get('SKF Türkiye')},
        # Yedek parçalar
        {'ad': 'SKF Rulman 6205-2RS', 'kod': 'MLZ-010', 'birim': 'adet', 'kategori': 'Yedek Parça', 'lokasyon': 'Raf D1-01', 'birim_fiyat': 320.00, 'mevcut_miktar': 6, 'minimum_stok': 4, 'tedarikci_id': teds.get('SKF Türkiye')},
        {'ad': 'Pnömatik Silindir Ø32×100', 'kod': 'MLZ-011', 'birim': 'adet', 'kategori': 'Yedek Parça', 'lokasyon': 'Raf D1-02', 'birim_fiyat': 890.00, 'mevcut_miktar': 2, 'minimum_stok': 3, 'tedarikci_id': teds.get('Festo Türkiye')},  # KRİTİK
        {'ad': 'Servo Motor Fan (80×80mm)', 'kod': 'MLZ-012', 'birim': 'adet', 'kategori': 'Yedek Parça', 'lokasyon': 'Raf D1-03', 'birim_fiyat': 245.00, 'mevcut_miktar': 4, 'minimum_stok': 2, 'tedarikci_id': teds.get('IGUS Türkiye')},
        # Kaynak malzemeleri
        {'ad': 'MIG Kaynak Teli Ø1.0 (ER70S-6)', 'kod': 'MLZ-013', 'birim': 'kg', 'kategori': 'Kaynak Malzeme', 'lokasyon': 'Raf E1-01', 'birim_fiyat': 45.00, 'mevcut_miktar': 75, 'minimum_stok': 25, 'tedarikci_id': teds.get('Lincoln Electric Türkiye')},
        {'ad': 'Argon Gazı (50 lt tüp)', 'kod': 'MLZ-014', 'birim': 'adet', 'kategori': 'Kaynak Malzeme', 'lokasyon': 'Gaz Deposu', 'birim_fiyat': 1200.00, 'mevcut_miktar': 1, 'minimum_stok': 2, 'tedarikci_id': teds.get('Linde Gaz')},  # KRİTİK
        # Lazer malzemeleri
        {'ad': 'Lazer Koruyucu Cam (Trumpf Uyumlu)', 'kod': 'MLZ-015', 'birim': 'adet', 'kategori': 'Lazer Sarf', 'lokasyon': 'Raf F1-01', 'birim_fiyat': 650.00, 'mevcut_miktar': 5, 'minimum_stok': 3, 'tedarikci_id': teds.get('Misumi Türkiye')},
        {'ad': 'Lazer Kesim Nozulu Ø1.5', 'kod': 'MLZ-016', 'birim': 'adet', 'kategori': 'Lazer Sarf', 'lokasyon': 'Raf F1-02', 'birim_fiyat': 380.00, 'mevcut_miktar': 8, 'minimum_stok': 4, 'tedarikci_id': teds.get('Misumi Türkiye')},
        # Genel
        {'ad': 'Emniyet Eldiveni (Mekanik)', 'kod': 'MLZ-017', 'birim': 'adet', 'kategori': 'KKD', 'lokasyon': 'Raf G1-01', 'birim_fiyat': 28.00, 'mevcut_miktar': 50, 'minimum_stok': 20, 'tedarikci_id': teds.get('İzocam')},
        {'ad': 'Yalıtım Bandı (Isıya Dayanıklı)', 'kod': 'MLZ-018', 'birim': 'adet', 'kategori': 'Genel', 'lokasyon': 'Raf G1-02', 'birim_fiyat': 65.00, 'mevcut_miktar': 15, 'minimum_stok': 5, 'tedarikci_id': teds.get('İzocam')},
    ]

    for m_data in malzemeler:
        m = Malzeme(**m_data, aktif=True)
        db.session.add(m)
        kritik = ' ⚠️ KRİTİK' if m_data['mevcut_miktar'] <= m_data['minimum_stok'] else ''
        print(f'  + {m_data["ad"]} ({m_data["kod"]}) — Stok: {m_data["mevcut_miktar"]}/{m_data["minimum_stok"]}{kritik}')

    db.session.flush()

    # ── STOK HAREKETLERİ (30+) ──
    malzeme_kayitlari = Malzeme.query.all()
    fatura_prefix = ['FTR-2026-', 'IRS-2026-', 'SAS-2026-']

    for i, mlz in enumerate(malzeme_kayitlari):
        # Her malzeme için 1-3 giriş, 1-2 çıkış hareketi
        giris_sayisi = random.randint(1, 3)
        for j in range(giris_sayisi):
            gun_once = random.randint(5, 150)
            miktar = random.randint(5, 50) if mlz.birim == 'adet' else random.randint(10, 100)
            sh = StokHareketi(
                malzeme_id=mlz.id,
                hareket_turu='giris',
                miktar=miktar,
                birim_fiyat=float(mlz.birim_fiyat) * random.uniform(0.95, 1.05),
                fatura_no=f'{random.choice(fatura_prefix)}{1000 + i * 3 + j:05d}',
                neden='Tedarikçi siparişi teslim alındı',
                islem_yapan_id=admin.id if admin else 1,
                tarih=datetime.now(timezone.utc) - timedelta(days=gun_once),
            )
            db.session.add(sh)

        cikis_sayisi = random.randint(1, 2)
        for j in range(cikis_sayisi):
            gun_once = random.randint(1, 60)
            miktar = random.randint(1, 10) if mlz.birim == 'adet' else random.randint(5, 30)
            nedenler = [
                'Üretim hattına malzeme çıkışı',
                'Bakım operasyonu için çıkış',
                'Kalıp/takım değişimi',
                'Arıza onarımı için kullanıldı',
                'Vardiya sarf malzeme dağıtımı',
            ]
            sh = StokHareketi(
                malzeme_id=mlz.id,
                hareket_turu='cikis',
                miktar=miktar,
                neden=random.choice(nedenler),
                islem_yapan_id=admin.id if admin else 1,
                tarih=datetime.now(timezone.utc) - timedelta(days=gun_once),
            )
            db.session.add(sh)

    db.session.flush()
    print(f'  + {len(malzeme_kayitlari)} malzeme için stok hareketleri oluşturuldu\n')
