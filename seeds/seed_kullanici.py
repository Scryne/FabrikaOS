"""
FabrikaOS — Kullanıcı ve Çalışan Demo Verisi
Senaryo: AnadoluTech Metal Sanayi A.Ş. — Otomotiv Yan Sanayi (Kocaeli OSB)

15 çalışan kadro, 5 sistem kullanıcısı, çapraz departman becerileri.
"""
from datetime import date
from app.extensions import db
from app.models.kullanici import Kullanici
from app.models.personel import Calisan


def seed():
    print('[1/12] Kullanıcılar ve Çalışanlar...')

    # ── Sistem Kullanıcıları ──
    kullanicilar = [
        {
            'ad_soyad': 'Deniz Yazar',
            'kullanici_adi': 'admin',
            'rol': 'yonetici',
            'modul_erisim': {
                'personel': True, 'makine': True, 'stok': True,
                'kalite': True, 'enerji': True, 'isg': True
            },
        },
        {
            'ad_soyad': 'Ahmet Yılmaz',
            'kullanici_adi': 'ahmet.yilmaz',
            'rol': 'operator',
            'modul_erisim': {
                'personel': True, 'makine': True, 'stok': True,
                'kalite': True, 'isg': True
            },
        },
        {
            'ad_soyad': 'Fatma Demir',
            'kullanici_adi': 'fatma.demir',
            'rol': 'operator',
            'modul_erisim': {
                'personel': True, 'makine': True, 'stok': True,
                'kalite': True, 'isg': True
            },
        },
        {
            'ad_soyad': 'Mehmet Kaya',
            'kullanici_adi': 'mehmet.kaya',
            'rol': 'teknisyen',
            'modul_erisim': {
                'makine': True, 'stok': True, 'enerji': True, 'isg': True
            },
        },
        {
            'ad_soyad': 'Ayşe Özkan',
            'kullanici_adi': 'ayse.ozkan',
            'rol': 'teknisyen',
            'modul_erisim': {
                'makine': True, 'stok': True, 'enerji': True, 'isg': True
            },
        },
    ]

    for k_data in kullanicilar:
        if Kullanici.query.filter_by(kullanici_adi=k_data['kullanici_adi']).first():
            continue
        k = Kullanici(**k_data, aktif=True)
        sifre = 'admin123' if k_data['rol'] == 'yonetici' else 'demo123'
        k.sifre_belirle(sifre)
        db.session.add(k)
        print(f'  + {k_data["ad_soyad"]} ({k_data["kullanici_adi"]} / {sifre})')

    db.session.flush()

    # ── Çalışan Kadrosu (15 kişi) ──
    # Makine ID'leri: 1=CNC-001, 2=CNC-002, 3=ABK-001, 4=PRS-001, 5=KYN-001, 6=TSL-001
    calisanlar = [
        # Üretim Departmanı
        {
            'sicil_no': 'P001', 'ad_soyad': 'Ahmet Yılmaz',
            'departman': 'Üretim', 'pozisyon': 'Kıdemli CNC Operatörü',
            'telefon': '0532 111 22 33', 'eposta': 'ahmet.yilmaz@anadolutech.com.tr',
            'ise_baslama': date(2019, 3, 15), 'ucret': 48500,
            'beceri_json': [
                {'makine_id': 1, 'puan': 5}, {'makine_id': 2, 'puan': 4},
                {'makine_id': 6, 'puan': 3}
            ],
            'kullanici_adi': 'ahmet.yilmaz',
        },
        {
            'sicil_no': 'P002', 'ad_soyad': 'Fatma Demir',
            'departman': 'Üretim', 'pozisyon': 'Abkant Operatörü',
            'telefon': '0533 222 33 44', 'eposta': 'fatma.demir@anadolutech.com.tr',
            'ise_baslama': date(2020, 6, 1), 'ucret': 42000,
            'beceri_json': [
                {'makine_id': 3, 'puan': 5}, {'makine_id': 4, 'puan': 3}
            ],
            'kullanici_adi': 'fatma.demir',
        },
        {
            'sicil_no': 'P005', 'ad_soyad': 'Ali Çelik',
            'departman': 'Üretim', 'pozisyon': 'Pres Operatörü',
            'telefon': '0536 555 66 77', 'eposta': 'ali.celik@anadolutech.com.tr',
            'ise_baslama': date(2022, 2, 5), 'ucret': 38000,
            'beceri_json': [
                {'makine_id': 4, 'puan': 5}, {'makine_id': 3, 'puan': 2}
            ],
        },
        {
            'sicil_no': 'P007', 'ad_soyad': 'Mustafa Şahin',
            'departman': 'Üretim', 'pozisyon': 'Vardiya Amiri',
            'telefon': '0538 777 88 99', 'eposta': 'mustafa.sahin@anadolutech.com.tr',
            'ise_baslama': date(2017, 5, 20), 'ucret': 58000,
            'beceri_json': [
                {'makine_id': 1, 'puan': 4}, {'makine_id': 2, 'puan': 4},
                {'makine_id': 3, 'puan': 3}, {'makine_id': 4, 'puan': 3},
                {'makine_id': 5, 'puan': 2}
            ],
        },
        {
            'sicil_no': 'P011', 'ad_soyad': 'Emre Aydın',
            'departman': 'Üretim', 'pozisyon': 'Kaynak Operatörü',
            'telefon': '0542 111 33 55', 'eposta': 'emre.aydin@anadolutech.com.tr',
            'ise_baslama': date(2021, 9, 12), 'ucret': 44000,
            'beceri_json': [
                {'makine_id': 5, 'puan': 5}, {'makine_id': 4, 'puan': 2}
            ],
        },
        {
            'sicil_no': 'P012', 'ad_soyad': 'Yusuf Erdoğan',
            'departman': 'Üretim', 'pozisyon': 'Taşlama Operatörü',
            'telefon': '0543 222 44 66', 'eposta': 'yusuf.erdogan@anadolutech.com.tr',
            'ise_baslama': date(2023, 1, 8), 'ucret': 36000,
            'beceri_json': [
                {'makine_id': 6, 'puan': 4}, {'makine_id': 1, 'puan': 2}
            ],
        },

        # Bakım Departmanı
        {
            'sicil_no': 'P003', 'ad_soyad': 'Mehmet Kaya',
            'departman': 'Bakım', 'pozisyon': 'Kıdemli Mekanik Teknisyen',
            'telefon': '0534 333 44 55', 'eposta': 'mehmet.kaya@anadolutech.com.tr',
            'ise_baslama': date(2018, 1, 10), 'ucret': 55000,
            'beceri_json': [
                {'makine_id': 1, 'puan': 5}, {'makine_id': 2, 'puan': 5},
                {'makine_id': 3, 'puan': 4}, {'makine_id': 4, 'puan': 5},
                {'makine_id': 5, 'puan': 3}, {'makine_id': 6, 'puan': 4}
            ],
            'kullanici_adi': 'mehmet.kaya',
        },
        {
            'sicil_no': 'P004', 'ad_soyad': 'Ayşe Özkan',
            'departman': 'Bakım', 'pozisyon': 'Elektrik-Otomasyon Teknisyeni',
            'telefon': '0535 444 55 66', 'eposta': 'ayse.ozkan@anadolutech.com.tr',
            'ise_baslama': date(2021, 9, 20), 'ucret': 46000,
            'beceri_json': [
                {'makine_id': 1, 'puan': 3}, {'makine_id': 2, 'puan': 3},
                {'makine_id': 3, 'puan': 4}, {'makine_id': 5, 'puan': 5}
            ],
            'kullanici_adi': 'ayse.ozkan',
        },
        {
            'sicil_no': 'P009', 'ad_soyad': 'Hasan Koç',
            'departman': 'Bakım', 'pozisyon': 'Mekanik Teknisyen',
            'telefon': '0540 999 00 11', 'eposta': 'hasan.koc@anadolutech.com.tr',
            'ise_baslama': date(2023, 7, 10), 'ucret': 40000,
            'beceri_json': [
                {'makine_id': 4, 'puan': 4}, {'makine_id': 6, 'puan': 3},
                {'makine_id': 3, 'puan': 2}
            ],
        },

        # Kalite Kontrol Departmanı
        {
            'sicil_no': 'P006', 'ad_soyad': 'Zeynep Arslan',
            'departman': 'Kalite Kontrol', 'pozisyon': 'Kalite Kontrol Mühendisi',
            'telefon': '0537 666 77 88', 'eposta': 'zeynep.arslan@anadolutech.com.tr',
            'ise_baslama': date(2020, 11, 15), 'ucret': 52000,
            'beceri_json': [],
        },
        {
            'sicil_no': 'P013', 'ad_soyad': 'Burak Yıldırım',
            'departman': 'Kalite Kontrol', 'pozisyon': 'Kalite Kontrol Teknisyeni',
            'telefon': '0544 333 55 77', 'eposta': 'burak.yildirim@anadolutech.com.tr',
            'ise_baslama': date(2022, 4, 3), 'ucret': 39000,
            'beceri_json': [],
        },

        # Depo / Lojistik
        {
            'sicil_no': 'P008', 'ad_soyad': 'Elif Yıldız',
            'departman': 'Depo', 'pozisyon': 'Depo ve Lojistik Sorumlusu',
            'telefon': '0539 888 99 00', 'eposta': 'elif.yildiz@anadolutech.com.tr',
            'ise_baslama': date(2021, 3, 1), 'ucret': 42000,
            'beceri_json': [],
        },

        # İSG Departmanı
        {
            'sicil_no': 'P010', 'ad_soyad': 'Selin Aktaş',
            'departman': 'İSG', 'pozisyon': 'İSG Uzmanı (C Sınıfı)',
            'telefon': '0541 000 11 22', 'eposta': 'selin.aktas@anadolutech.com.tr',
            'ise_baslama': date(2019, 9, 1), 'ucret': 54000,
            'beceri_json': [],
        },

        # Planlama
        {
            'sicil_no': 'P014', 'ad_soyad': 'Deniz Korkmaz',
            'departman': 'Planlama', 'pozisyon': 'Üretim Planlama Uzmanı',
            'telefon': '0545 444 66 88', 'eposta': 'deniz.korkmaz@anadolutech.com.tr',
            'ise_baslama': date(2022, 8, 15), 'ucret': 50000,
            'beceri_json': [],
        },
        {
            'sicil_no': 'P015', 'ad_soyad': 'Canan Erdem',
            'departman': 'Planlama', 'pozisyon': 'Staj Mühendis',
            'telefon': '0546 555 77 99', 'eposta': 'canan.erdem@anadolutech.com.tr',
            'ise_baslama': date(2025, 10, 1), 'ucret': 28000,
            'beceri_json': [],
        },
    ]

    for c_data in calisanlar:
        if Calisan.query.filter_by(sicil_no=c_data['sicil_no']).first():
            continue
        kadi = c_data.pop('kullanici_adi', None)
        kullanici_id = None
        if kadi:
            k = Kullanici.query.filter_by(kullanici_adi=kadi).first()
            if k:
                kullanici_id = k.id
        c = Calisan(**c_data, kullanici_id=kullanici_id, aktif=True)
        db.session.add(c)
        print(f'  + Çalışan: {c_data["ad_soyad"]} ({c_data["sicil_no"]})')

    db.session.flush()
    print('  OK\n')
