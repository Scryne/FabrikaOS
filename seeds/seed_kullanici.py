"""
FabrikaOS — Kullanıcı ve Çalışan Demo Verisi (v2 — Tam Kapsam)
Senaryo: AnadoluTech Metal Sanayi A.Ş. — Otomotiv Yan Sanayi (Kocaeli OSB)

10 sistem kullanıcısı (8 farklı rol), 20 çalışan kadro.
Granüler erişim formatı, zengin İK profilleri.
"""
from datetime import date
from app.extensions import db
from app.models.kullanici import Kullanici
from app.models.personel import Calisan


def seed():
    print('[1/22] Kullanıcılar ve Çalışanlar...')

    # ── Sistem Kullanıcıları (8 farklı rol) ──
    kullanicilar = [
        {
            'ad_soyad': 'Deniz Yazar',
            'kullanici_adi': 'admin',
            'rol': 'yonetici',
            'departman': 'Yönetim',
            'modul_erisim': {},  # Yönetici otomatik tam yetki
        },
        {
            'ad_soyad': 'Ahmet Yılmaz',
            'kullanici_adi': 'ahmet.yilmaz',
            'rol': 'operator',
            'departman': 'Üretim',
            'modul_erisim': {
                'personel': {'okuma': True, 'yazma': False, 'silme': False},
                'makine': {'okuma': True, 'yazma': True, 'silme': False},
                'stok': {'okuma': True, 'yazma': True, 'silme': False},
                'kalite': {'okuma': True, 'yazma': True, 'silme': False},
                'isg': {'okuma': True, 'yazma': False, 'silme': False},
                'duyuru': {'okuma': True, 'yazma': False, 'silme': False},
            },
        },
        {
            'ad_soyad': 'Fatma Demir',
            'kullanici_adi': 'fatma.demir',
            'rol': 'operator',
            'departman': 'Üretim',
            'modul_erisim': {
                'personel': {'okuma': True, 'yazma': False, 'silme': False},
                'makine': {'okuma': True, 'yazma': True, 'silme': False},
                'stok': {'okuma': True, 'yazma': True, 'silme': False},
                'kalite': {'okuma': True, 'yazma': True, 'silme': False},
                'isg': {'okuma': True, 'yazma': False, 'silme': False},
                'duyuru': {'okuma': True, 'yazma': False, 'silme': False},
            },
        },
        {
            'ad_soyad': 'Mehmet Kaya',
            'kullanici_adi': 'mehmet.kaya',
            'rol': 'teknisyen',
            'departman': 'Bakım',
            'modul_erisim': {
                'makine': {'okuma': True, 'yazma': True, 'silme': False},
                'stok': {'okuma': True, 'yazma': True, 'silme': False},
                'enerji': {'okuma': True, 'yazma': True, 'silme': False},
                'isg': {'okuma': True, 'yazma': False, 'silme': False},
                'duyuru': {'okuma': True, 'yazma': False, 'silme': False},
            },
        },
        {
            'ad_soyad': 'Ayşe Özkan',
            'kullanici_adi': 'ayse.ozkan',
            'rol': 'teknisyen',
            'departman': 'Bakım',
            'modul_erisim': {
                'makine': {'okuma': True, 'yazma': True, 'silme': False},
                'stok': {'okuma': True, 'yazma': True, 'silme': False},
                'enerji': {'okuma': True, 'yazma': True, 'silme': False},
                'isg': {'okuma': True, 'yazma': False, 'silme': False},
                'duyuru': {'okuma': True, 'yazma': False, 'silme': False},
            },
        },
        {
            'ad_soyad': 'Selin Aktaş',
            'kullanici_adi': 'selin.aktas',
            'rol': 'isg_uzmani',
            'departman': 'İSG',
            'modul_erisim': {
                'isg': {'okuma': True, 'yazma': True, 'silme': True},
                'personel': {'okuma': True, 'yazma': False, 'silme': False},
                'makine': {'okuma': True, 'yazma': False, 'silme': False},
                'kalite': {'okuma': True, 'yazma': False, 'silme': False},
                'duyuru': {'okuma': True, 'yazma': True, 'silme': False},
                'dys': {'okuma': True, 'yazma': True, 'silme': False},
            },
        },
        {
            'ad_soyad': 'Zeynep Arslan',
            'kullanici_adi': 'zeynep.arslan',
            'rol': 'ik_uzmani',
            'departman': 'İnsan Kaynakları',
            'modul_erisim': {
                'personel': {'okuma': True, 'yazma': True, 'silme': True},
                'ik': {'okuma': True, 'yazma': True, 'silme': True},
                'isg': {'okuma': True, 'yazma': False, 'silme': False},
                'duyuru': {'okuma': True, 'yazma': True, 'silme': False},
                'dys': {'okuma': True, 'yazma': True, 'silme': False},
            },
        },
        {
            'ad_soyad': 'Elif Yıldız',
            'kullanici_adi': 'elif.yildiz',
            'rol': 'muhasebe',
            'departman': 'Muhasebe',
            'modul_erisim': {
                'sozlesme': {'okuma': True, 'yazma': True, 'silme': True},
                'crm': {'okuma': True, 'yazma': True, 'silme': False},
                'stok': {'okuma': True, 'yazma': False, 'silme': False},
                'enerji': {'okuma': True, 'yazma': False, 'silme': False},
                'satin_alma': {'okuma': True, 'yazma': False, 'silme': False},
                'duyuru': {'okuma': True, 'yazma': False, 'silme': False},
            },
        },
        {
            'ad_soyad': 'Deniz Korkmaz',
            'kullanici_adi': 'deniz.korkmaz',
            'rol': 'crm_yetkilisi',
            'departman': 'CRM',
            'modul_erisim': {
                'crm': {'okuma': True, 'yazma': True, 'silme': True},
                'sozlesme': {'okuma': True, 'yazma': True, 'silme': False},
                'talep': {'okuma': True, 'yazma': True, 'silme': False},
                'duyuru': {'okuma': True, 'yazma': True, 'silme': False},
                'dys': {'okuma': True, 'yazma': False, 'silme': False},
            },
        },
        {
            'ad_soyad': 'Mustafa Şahin',
            'kullanici_adi': 'mustafa.sahin',
            'rol': 'satin_alma',
            'departman': 'Satın Alma',
            'modul_erisim': {
                'satin_alma': {'okuma': True, 'yazma': True, 'silme': True},
                'stok': {'okuma': True, 'yazma': True, 'silme': False},
                'sozlesme': {'okuma': True, 'yazma': False, 'silme': False},
                'duyuru': {'okuma': True, 'yazma': False, 'silme': False},
            },
        },
    ]

    for k_data in kullanicilar:
        k = Kullanici(**k_data, aktif=True)
        sifre = 'admin123' if k_data['rol'] == 'yonetici' else 'demo123'
        k.sifre_belirle(sifre)
        db.session.add(k)
        print(f'  + {k_data["ad_soyad"]} ({k_data["kullanici_adi"]} / {sifre}) [{k_data["rol"]}]')

    db.session.flush()

    # ── Çalışan Kadrosu (20 kişi — Zengin Profiller) ──
    # Makine ID'leri: 1=CNC-001, 2=CNC-002, 3=ABK-001, 4=PRS-001, 5=KYN-001, 6=TSL-001, 7=LZR-001, 8=MNT-001
    calisanlar = [
        # ═══ Üretim Departmanı (7 kişi) ═══
        {
            'sicil_no': 'P001', 'ad_soyad': 'Ahmet Yılmaz',
            'departman': 'Üretim', 'pozisyon': 'Kıdemli CNC Operatörü',
            'telefon': '0532 111 22 33', 'eposta': 'ahmet.yilmaz@anadolutech.com.tr',
            'ise_baslama': date(2019, 3, 15), 'ucret': 48500,
            'tc_kimlik': '12345678901', 'dogum_tarihi': date(1988, 5, 12),
            'kan_grubu': 'A+', 'medeni_durum': 'evli', 'askerlik_durumu': 'yapti',
            'egitim_durumu': 'lise', 'il': 'Kocaeli', 'ilce': 'Gebze',
            'adres': 'Güzeller OSB Mah. Sanayi Cad. No:15/A Gebze/Kocaeli',
            'acil_kisi_adi': 'Hatice Yılmaz', 'acil_kisi_tel': '0532 111 22 34',
            'beceri_json': [
                {'makine_id': 1, 'puan': 5}, {'makine_id': 2, 'puan': 4},
                {'makine_id': 6, 'puan': 3}, {'makine_id': 7, 'puan': 2}
            ],
            'kullanici_adi': 'ahmet.yilmaz',
        },
        {
            'sicil_no': 'P002', 'ad_soyad': 'Fatma Demir',
            'departman': 'Üretim', 'pozisyon': 'Abkant Operatörü',
            'telefon': '0533 222 33 44', 'eposta': 'fatma.demir@anadolutech.com.tr',
            'ise_baslama': date(2020, 6, 1), 'ucret': 42000,
            'tc_kimlik': '23456789012', 'dogum_tarihi': date(1992, 11, 3),
            'kan_grubu': 'B+', 'medeni_durum': 'bekar', 'askerlik_durumu': 'muaf',
            'egitim_durumu': 'lisans', 'il': 'Kocaeli', 'ilce': 'Çayırova',
            'adres': 'Atatürk Mah. Cumhuriyet Cad. No:42 Çayırova/Kocaeli',
            'acil_kisi_adi': 'Hasan Demir', 'acil_kisi_tel': '0533 222 33 45',
            'beceri_json': [
                {'makine_id': 3, 'puan': 5}, {'makine_id': 4, 'puan': 3},
                {'makine_id': 7, 'puan': 2}
            ],
            'kullanici_adi': 'fatma.demir',
        },
        {
            'sicil_no': 'P005', 'ad_soyad': 'Ali Çelik',
            'departman': 'Üretim', 'pozisyon': 'Pres Operatörü',
            'telefon': '0536 555 66 77', 'eposta': 'ali.celik@anadolutech.com.tr',
            'ise_baslama': date(2022, 2, 5), 'ucret': 38000,
            'tc_kimlik': '34567890123', 'dogum_tarihi': date(1995, 7, 22),
            'kan_grubu': '0+', 'medeni_durum': 'evli', 'askerlik_durumu': 'yapti',
            'egitim_durumu': 'lise', 'il': 'Kocaeli', 'ilce': 'Gebze',
            'adres': 'Balçık Mah. 4. Sok. No:8 Gebze/Kocaeli',
            'acil_kisi_adi': 'Emine Çelik', 'acil_kisi_tel': '0536 555 66 78',
            'beceri_json': [
                {'makine_id': 4, 'puan': 5}, {'makine_id': 3, 'puan': 2}
            ],
        },
        {
            'sicil_no': 'P007', 'ad_soyad': 'Mustafa Şahin',
            'departman': 'Üretim', 'pozisyon': 'Vardiya Amiri',
            'telefon': '0538 777 88 99', 'eposta': 'mustafa.sahin@anadolutech.com.tr',
            'ise_baslama': date(2017, 5, 20), 'ucret': 58000,
            'tc_kimlik': '45678901234', 'dogum_tarihi': date(1985, 2, 14),
            'kan_grubu': 'AB+', 'medeni_durum': 'evli', 'askerlik_durumu': 'yapti',
            'egitim_durumu': 'lisans', 'il': 'Kocaeli', 'ilce': 'Darıca',
            'adres': 'Bayramoğlu Mah. Lale Sok. No:22/B Darıca/Kocaeli',
            'acil_kisi_adi': 'Nilgün Şahin', 'acil_kisi_tel': '0538 777 89 00',
            'beceri_json': [
                {'makine_id': 1, 'puan': 4}, {'makine_id': 2, 'puan': 4},
                {'makine_id': 3, 'puan': 3}, {'makine_id': 4, 'puan': 3},
                {'makine_id': 5, 'puan': 2}, {'makine_id': 7, 'puan': 3}
            ],
            'kullanici_adi': 'mustafa.sahin',
        },
        {
            'sicil_no': 'P011', 'ad_soyad': 'Emre Aydın',
            'departman': 'Üretim', 'pozisyon': 'Kaynak Operatörü',
            'telefon': '0542 111 33 55', 'eposta': 'emre.aydin@anadolutech.com.tr',
            'ise_baslama': date(2021, 9, 12), 'ucret': 44000,
            'tc_kimlik': '56789012345', 'dogum_tarihi': date(1993, 9, 30),
            'kan_grubu': 'A-', 'medeni_durum': 'evli', 'askerlik_durumu': 'yapti',
            'egitim_durumu': 'lise', 'il': 'İstanbul', 'ilce': 'Tuzla',
            'adres': 'Aydıntepe Mah. Fatih Cad. No:16 Tuzla/İstanbul',
            'acil_kisi_adi': 'Sevgi Aydın', 'acil_kisi_tel': '0542 111 33 56',
            'beceri_json': [
                {'makine_id': 5, 'puan': 5}, {'makine_id': 4, 'puan': 2},
                {'makine_id': 8, 'puan': 4}
            ],
        },
        {
            'sicil_no': 'P012', 'ad_soyad': 'Yusuf Erdoğan',
            'departman': 'Üretim', 'pozisyon': 'Taşlama Operatörü',
            'telefon': '0543 222 44 66', 'eposta': 'yusuf.erdogan@anadolutech.com.tr',
            'ise_baslama': date(2023, 1, 8), 'ucret': 36000,
            'tc_kimlik': '67890123456', 'dogum_tarihi': date(1998, 1, 18),
            'kan_grubu': 'B-', 'medeni_durum': 'bekar', 'askerlik_durumu': 'yapti',
            'egitim_durumu': 'lise', 'il': 'Kocaeli', 'ilce': 'Gebze',
            'adres': 'Eskihisar Mah. İnönü Cad. No:33 Gebze/Kocaeli',
            'acil_kisi_adi': 'Kemal Erdoğan', 'acil_kisi_tel': '0543 222 44 67',
            'beceri_json': [
                {'makine_id': 6, 'puan': 4}, {'makine_id': 1, 'puan': 2}
            ],
        },
        {
            'sicil_no': 'P016', 'ad_soyad': 'Burak Kılıç',
            'departman': 'Üretim', 'pozisyon': 'Lazer Kesim Operatörü',
            'telefon': '0547 888 11 22', 'eposta': 'burak.kilic@anadolutech.com.tr',
            'ise_baslama': date(2024, 3, 1), 'ucret': 40000,
            'tc_kimlik': '78901234567', 'dogum_tarihi': date(1996, 4, 5),
            'kan_grubu': '0-', 'medeni_durum': 'bekar', 'askerlik_durumu': 'tecilli',
            'egitim_durumu': 'lisans', 'il': 'Kocaeli', 'ilce': 'Çayırova',
            'adres': 'Şekerpınar Mah. Mimar Sinan Cad. No:7 Çayırova/Kocaeli',
            'acil_kisi_adi': 'Nurhan Kılıç', 'acil_kisi_tel': '0547 888 11 23',
            'beceri_json': [
                {'makine_id': 7, 'puan': 5}, {'makine_id': 3, 'puan': 3}
            ],
        },

        # ═══ Bakım Departmanı (4 kişi) ═══
        {
            'sicil_no': 'P003', 'ad_soyad': 'Mehmet Kaya',
            'departman': 'Bakım', 'pozisyon': 'Kıdemli Mekanik Teknisyen',
            'telefon': '0534 333 44 55', 'eposta': 'mehmet.kaya@anadolutech.com.tr',
            'ise_baslama': date(2018, 1, 10), 'ucret': 55000,
            'tc_kimlik': '89012345678', 'dogum_tarihi': date(1986, 8, 25),
            'kan_grubu': 'A+', 'medeni_durum': 'evli', 'askerlik_durumu': 'yapti',
            'egitim_durumu': 'lisans', 'il': 'Kocaeli', 'ilce': 'Gebze',
            'adres': 'Pelitli Mah. Fabrika Sok. No:5/C Gebze/Kocaeli',
            'acil_kisi_adi': 'Ayten Kaya', 'acil_kisi_tel': '0534 333 44 56',
            'beceri_json': [
                {'makine_id': 1, 'puan': 5}, {'makine_id': 2, 'puan': 5},
                {'makine_id': 3, 'puan': 4}, {'makine_id': 4, 'puan': 5},
                {'makine_id': 5, 'puan': 3}, {'makine_id': 6, 'puan': 4},
                {'makine_id': 7, 'puan': 3}, {'makine_id': 8, 'puan': 2}
            ],
            'kullanici_adi': 'mehmet.kaya',
        },
        {
            'sicil_no': 'P004', 'ad_soyad': 'Ayşe Özkan',
            'departman': 'Bakım', 'pozisyon': 'Elektrik-Otomasyon Teknisyeni',
            'telefon': '0535 444 55 66', 'eposta': 'ayse.ozkan@anadolutech.com.tr',
            'ise_baslama': date(2021, 9, 20), 'ucret': 46000,
            'tc_kimlik': '90123456789', 'dogum_tarihi': date(1994, 3, 8),
            'kan_grubu': 'AB-', 'medeni_durum': 'bekar', 'askerlik_durumu': 'muaf',
            'egitim_durumu': 'lisans', 'il': 'Kocaeli', 'ilce': 'Dilovası',
            'adres': 'Köseler Mah. Çınar Sok. No:12 Dilovası/Kocaeli',
            'acil_kisi_adi': 'Hüseyin Özkan', 'acil_kisi_tel': '0535 444 55 67',
            'beceri_json': [
                {'makine_id': 1, 'puan': 3}, {'makine_id': 2, 'puan': 3},
                {'makine_id': 3, 'puan': 4}, {'makine_id': 5, 'puan': 5},
                {'makine_id': 7, 'puan': 4}
            ],
            'kullanici_adi': 'ayse.ozkan',
        },
        {
            'sicil_no': 'P009', 'ad_soyad': 'Hasan Koç',
            'departman': 'Bakım', 'pozisyon': 'Mekanik Teknisyen',
            'telefon': '0540 999 00 11', 'eposta': 'hasan.koc@anadolutech.com.tr',
            'ise_baslama': date(2023, 7, 10), 'ucret': 40000,
            'tc_kimlik': '01234567890', 'dogum_tarihi': date(1997, 12, 1),
            'kan_grubu': 'B+', 'medeni_durum': 'bekar', 'askerlik_durumu': 'yapti',
            'egitim_durumu': 'lise', 'il': 'İstanbul', 'ilce': 'Pendik',
            'adres': 'Yenişehir Mah. Sanayi Cad. No:45 Pendik/İstanbul',
            'acil_kisi_adi': 'Gülşen Koç', 'acil_kisi_tel': '0540 999 00 12',
            'beceri_json': [
                {'makine_id': 4, 'puan': 4}, {'makine_id': 6, 'puan': 3},
                {'makine_id': 3, 'puan': 2}, {'makine_id': 8, 'puan': 3}
            ],
        },
        {
            'sicil_no': 'P017', 'ad_soyad': 'Okan Yılmaz',
            'departman': 'Bakım', 'pozisyon': 'Otomasyon Teknisyeni',
            'telefon': '0548 333 22 11', 'eposta': 'okan.yilmaz@anadolutech.com.tr',
            'ise_baslama': date(2024, 6, 15), 'ucret': 42000,
            'tc_kimlik': '11223344556', 'dogum_tarihi': date(1999, 6, 20),
            'kan_grubu': '0+', 'medeni_durum': 'bekar', 'askerlik_durumu': 'tecilli',
            'egitim_durumu': 'lisans', 'il': 'Kocaeli', 'ilce': 'Gebze',
            'adres': 'Güzeller Mah. Teknik Sok. No:3 Gebze/Kocaeli',
            'acil_kisi_adi': 'Selma Yılmaz', 'acil_kisi_tel': '0548 333 22 12',
            'beceri_json': [
                {'makine_id': 5, 'puan': 4}, {'makine_id': 7, 'puan': 3},
                {'makine_id': 1, 'puan': 2}
            ],
        },

        # ═══ Kalite Kontrol (2 kişi) ═══
        {
            'sicil_no': 'P006', 'ad_soyad': 'Zeynep Arslan',
            'departman': 'Kalite Kontrol', 'pozisyon': 'Kalite Kontrol Mühendisi',
            'telefon': '0537 666 77 88', 'eposta': 'zeynep.arslan@anadolutech.com.tr',
            'ise_baslama': date(2020, 11, 15), 'ucret': 52000,
            'tc_kimlik': '22334455667', 'dogum_tarihi': date(1991, 10, 17),
            'kan_grubu': 'A+', 'medeni_durum': 'evli', 'askerlik_durumu': 'muaf',
            'egitim_durumu': 'yuksek_lisans', 'il': 'Kocaeli', 'ilce': 'Gebze',
            'adres': 'Osman Yılmaz Mah. Üniversite Cad. No:28 Gebze/Kocaeli',
            'acil_kisi_adi': 'Serkan Arslan', 'acil_kisi_tel': '0537 666 77 89',
            'beceri_json': [],
            'kullanici_adi': 'zeynep.arslan',
        },
        {
            'sicil_no': 'P013', 'ad_soyad': 'Burak Yıldırım',
            'departman': 'Kalite Kontrol', 'pozisyon': 'Kalite Kontrol Teknisyeni',
            'telefon': '0544 333 55 77', 'eposta': 'burak.yildirim@anadolutech.com.tr',
            'ise_baslama': date(2022, 4, 3), 'ucret': 39000,
            'tc_kimlik': '33445566778', 'dogum_tarihi': date(1996, 8, 9),
            'kan_grubu': 'B+', 'medeni_durum': 'bekar', 'askerlik_durumu': 'yapti',
            'egitim_durumu': 'lisans', 'il': 'Kocaeli', 'ilce': 'Çayırova',
            'adres': 'Akse Mah. Kıbrıs Cad. No:14 Çayırova/Kocaeli',
            'acil_kisi_adi': 'Süleyman Yıldırım', 'acil_kisi_tel': '0544 333 55 78',
            'beceri_json': [],
        },

        # ═══ Depo / Lojistik (1 kişi) ═══
        {
            'sicil_no': 'P008', 'ad_soyad': 'Elif Yıldız',
            'departman': 'Depo', 'pozisyon': 'Depo ve Lojistik Sorumlusu',
            'telefon': '0539 888 99 00', 'eposta': 'elif.yildiz@anadolutech.com.tr',
            'ise_baslama': date(2021, 3, 1), 'ucret': 42000,
            'tc_kimlik': '44556677889', 'dogum_tarihi': date(1990, 5, 28),
            'kan_grubu': '0+', 'medeni_durum': 'evli', 'askerlik_durumu': 'muaf',
            'egitim_durumu': 'lisans', 'il': 'Kocaeli', 'ilce': 'Gebze',
            'adres': 'Sultançiftliği Mah. Pazar Sok. No:9 Gebze/Kocaeli',
            'acil_kisi_adi': 'Cemal Yıldız', 'acil_kisi_tel': '0539 888 99 01',
            'beceri_json': [],
            'kullanici_adi': 'elif.yildiz',
        },

        # ═══ İSG (1 kişi) ═══
        {
            'sicil_no': 'P010', 'ad_soyad': 'Selin Aktaş',
            'departman': 'İSG', 'pozisyon': 'İSG Uzmanı (C Sınıfı)',
            'telefon': '0541 000 11 22', 'eposta': 'selin.aktas@anadolutech.com.tr',
            'ise_baslama': date(2019, 9, 1), 'ucret': 54000,
            'tc_kimlik': '55667788990', 'dogum_tarihi': date(1989, 12, 10),
            'kan_grubu': 'AB+', 'medeni_durum': 'evli', 'askerlik_durumu': 'muaf',
            'egitim_durumu': 'yuksek_lisans', 'il': 'Kocaeli', 'ilce': 'Gebze',
            'adres': 'Arapçeşme Mah. Atatürk Bulvarı No:55/A Gebze/Kocaeli',
            'acil_kisi_adi': 'Volkan Aktaş', 'acil_kisi_tel': '0541 000 11 23',
            'beceri_json': [],
            'kullanici_adi': 'selin.aktas',
        },

        # ═══ Planlama (2 kişi) ═══
        {
            'sicil_no': 'P014', 'ad_soyad': 'Deniz Korkmaz',
            'departman': 'Planlama', 'pozisyon': 'Üretim Planlama Uzmanı',
            'telefon': '0545 444 66 88', 'eposta': 'deniz.korkmaz@anadolutech.com.tr',
            'ise_baslama': date(2022, 8, 15), 'ucret': 50000,
            'tc_kimlik': '66778899001', 'dogum_tarihi': date(1993, 4, 22),
            'kan_grubu': 'A-', 'medeni_durum': 'evli', 'askerlik_durumu': 'yapti',
            'egitim_durumu': 'lisans', 'il': 'İstanbul', 'ilce': 'Kartal',
            'adres': 'Soğanlık Mah. İstasyon Cad. No:72 Kartal/İstanbul',
            'acil_kisi_adi': 'Esra Korkmaz', 'acil_kisi_tel': '0545 444 66 89',
            'beceri_json': [],
            'kullanici_adi': 'deniz.korkmaz',
        },
        {
            'sicil_no': 'P015', 'ad_soyad': 'Canan Erdem',
            'departman': 'Planlama', 'pozisyon': 'Üretim Planlama Asistanı',
            'telefon': '0546 555 77 99', 'eposta': 'canan.erdem@anadolutech.com.tr',
            'ise_baslama': date(2025, 10, 1), 'ucret': 32000,
            'tc_kimlik': '77889900112', 'dogum_tarihi': date(2001, 7, 15),
            'kan_grubu': 'B-', 'medeni_durum': 'bekar', 'askerlik_durumu': 'muaf',
            'egitim_durumu': 'lisans', 'il': 'Kocaeli', 'ilce': 'Gebze',
            'adres': 'Güzeller Mah. Üniversite Sok. No:18 Gebze/Kocaeli',
            'acil_kisi_adi': 'Tülay Erdem', 'acil_kisi_tel': '0546 555 78 00',
            'beceri_json': [],
        },

        # ═══ İnsan Kaynakları (1 kişi) ═══
        {
            'sicil_no': 'P018', 'ad_soyad': 'Gizem Toprak',
            'departman': 'İnsan Kaynakları', 'pozisyon': 'İK Asistanı',
            'telefon': '0549 444 55 66', 'eposta': 'gizem.toprak@anadolutech.com.tr',
            'ise_baslama': date(2024, 1, 15), 'ucret': 35000,
            'tc_kimlik': '88990011223', 'dogum_tarihi': date(2000, 2, 28),
            'kan_grubu': '0+', 'medeni_durum': 'bekar', 'askerlik_durumu': 'muaf',
            'egitim_durumu': 'lisans', 'il': 'Kocaeli', 'ilce': 'Gebze',
            'adres': 'Beylikbağı Mah. Eski İstanbul Cad. No:7 Gebze/Kocaeli',
            'acil_kisi_adi': 'Ayla Toprak', 'acil_kisi_tel': '0549 444 55 67',
            'beceri_json': [],
        },

        # ═══ Muhasebe (1 kişi — ek) ═══
        {
            'sicil_no': 'P019', 'ad_soyad': 'Serhat Acar',
            'departman': 'Muhasebe', 'pozisyon': 'Muhasebe Uzmanı',
            'telefon': '0550 666 77 88', 'eposta': 'serhat.acar@anadolutech.com.tr',
            'ise_baslama': date(2020, 4, 1), 'ucret': 47000,
            'tc_kimlik': '99001122334', 'dogum_tarihi': date(1991, 11, 5),
            'kan_grubu': 'A+', 'medeni_durum': 'evli', 'askerlik_durumu': 'yapti',
            'egitim_durumu': 'lisans', 'il': 'Kocaeli', 'ilce': 'Darıca',
            'adres': 'Nenehatun Mah. Atatürk Cad. No:31 Darıca/Kocaeli',
            'acil_kisi_adi': 'Dilek Acar', 'acil_kisi_tel': '0550 666 77 89',
            'beceri_json': [],
        },
    ]

    for c_data in calisanlar:
        kadi = c_data.pop('kullanici_adi', None)
        kullanici_id = None
        if kadi:
            k = Kullanici.query.filter_by(kullanici_adi=kadi).first()
            if k:
                kullanici_id = k.id
        c = Calisan(**c_data, kullanici_id=kullanici_id, aktif=True)
        db.session.add(c)
        print(f'  + Çalışan: {c_data["ad_soyad"]} ({c_data["sicil_no"]}) — {c_data["departman"]}')

    db.session.flush()
    print('  OK\n')
