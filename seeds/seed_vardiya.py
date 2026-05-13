"""
FabrikaOS — Vardiya Planı ve İzin Talebi Demo Verisi
Senaryo: AnadoluTech Metal Sanayi — 3 vardiya sistemi, 15 çalışan

- 2 haftalık vardiya planı (geçmiş 3 gün + gelecek 11 gün)
- 8 izin talebi (yıllık, mazeret, sağlık, ücretsiz — çeşitli durumlar)
"""
from datetime import date, time, timedelta, datetime, timezone
from app.extensions import db
from app.models.personel import Calisan, VardiyaPlani, IzinTalebi
from app.models.kullanici import Kullanici


def seed():
    print('[8/12] Vardiyalar ve İzinler...')

    calisanlar = Calisan.query.filter_by(aktif=True).all()
    bugun = date.today()
    admin = Kullanici.query.filter_by(kullanici_adi='admin').first()

    vardiya_map = {
        'sabah': (time(6, 0), time(14, 0)),
        'ogleden_sonra': (time(14, 0), time(22, 0)),
        'gece': (time(22, 0), time(6, 0)),
    }
    turler = ['sabah', 'ogleden_sonra', 'gece']

    # ── 2 HAFTALIK VARDİYA PLANI ──
    # Geçmiş 3 gün + gelecek 11 gün
    for gun in range(-3, 11):
        tarih = bugun + timedelta(days=gun)
        # Pazar: üretim yok
        if tarih.weekday() == 6:
            continue
        for i, calisan in enumerate(calisanlar):
            # Cumartesi sadece sabah vardiyası
            if tarih.weekday() == 5:
                tur = 'sabah'
            else:
                # Rotasyonlu vardiya dağılımı
                tur = turler[(i + gun) % 3]

            bas, bit = vardiya_map[tur]

            mevcut = VardiyaPlani.query.filter_by(
                calisan_id=calisan.id, tarih=tarih, vardiya_turu=tur
            ).first()
            if mevcut:
                continue

            # Bazı vardiyalara not ekle
            notlar = None
            if gun == 0:
                notlar = 'Bugünkü vardiya'
            elif gun == -1 and i == 0:
                notlar = 'Fazla mesai (2 saat)'

            vp = VardiyaPlani(
                calisan_id=calisan.id,
                tarih=tarih,
                vardiya_turu=tur,
                baslangic=bas,
                bitis=bit,
                notlar=notlar,
            )
            db.session.add(vp)

    db.session.flush()
    print('  + 2 haftalık vardiya planı oluşturuldu')

    # ── İZİN TALEPLERİ (8 adet) ──
    izinler = [
        # Bekleyen talepler
        {
            'sicil': 'P001',
            'bas': bugun + timedelta(days=15),
            'bit': bugun + timedelta(days=21),
            'tur': 'yillik',
            'aciklama': 'Ailece tatil planı — Antalya',
            'durum': 'bekliyor',
        },
        {
            'sicil': 'P005',
            'bas': bugun + timedelta(days=8),
            'bit': bugun + timedelta(days=8),
            'tur': 'mazeret',
            'aciklama': 'Kardeş nikah töreni',
            'durum': 'bekliyor',
        },
        {
            'sicil': 'P012',
            'bas': bugun + timedelta(days=12),
            'bit': bugun + timedelta(days=14),
            'tur': 'yillik',
            'aciklama': 'Kişisel işler — Karabük seyahati',
            'durum': 'bekliyor',
        },

        # Onaylanmış talepler
        {
            'sicil': 'P002',
            'bas': bugun - timedelta(days=5),
            'bit': bugun - timedelta(days=3),
            'tur': 'saglik',
            'aciklama': 'Diş ameliyatı ve istirahat raporu (3 gün)',
            'durum': 'onaylandi',
        },
        {
            'sicil': 'P003',
            'bas': bugun - timedelta(days=22),
            'bit': bugun - timedelta(days=16),
            'tur': 'yillik',
            'aciklama': 'Yıllık izin kullanımı — memleket ziyareti',
            'durum': 'onaylandi',
        },
        {
            'sicil': 'P009',
            'bas': bugun + timedelta(days=3),
            'bit': bugun + timedelta(days=4),
            'tur': 'mazeret',
            'aciklama': 'Ev taşınma',
            'durum': 'onaylandi',
        },

        # Reddedilmiş talep
        {
            'sicil': 'P006',
            'bas': bugun + timedelta(days=30),
            'bit': bugun + timedelta(days=44),
            'tur': 'ucretsiz',
            'aciklama': 'Kişisel nedenler — yurt dışı seyahat',
            'durum': 'reddedildi',
            'red_nedeni': 'Mayıs-Haziran dönemi üretim yoğunluğu nedeniyle '
                          '15 günlük ücretsiz izin uygun bulunmamıştır. '
                          'Daha kısa süreli yıllık izin değerlendirilebilir.',
        },

        # Ek onaylı talep
        {
            'sicil': 'P011',
            'bas': bugun - timedelta(days=10),
            'bit': bugun - timedelta(days=9),
            'tur': 'mazeret',
            'aciklama': 'Eşinin hastane randevusuna refakat',
            'durum': 'onaylandi',
        },
    ]

    for iz in izinler:
        calisan = Calisan.query.filter_by(sicil_no=iz['sicil']).first()
        if not calisan:
            continue
        onaylayan_id = admin.id if admin and iz['durum'] != 'bekliyor' else None
        onay_tarihi = None
        if onaylayan_id:
            # Onay tarihi başvurudan 1 gün sonra
            onay_tarihi = datetime.combine(
                iz['bas'] - timedelta(days=2), time(10, 0)
            ).replace(tzinfo=timezone.utc)

        it = IzinTalebi(
            calisan_id=calisan.id,
            baslangic_tarihi=iz['bas'],
            bitis_tarihi=iz['bit'],
            tur=iz['tur'],
            aciklama=iz['aciklama'],
            durum=iz['durum'],
            onaylayan_id=onaylayan_id,
            onay_tarihi=onay_tarihi,
            red_nedeni=iz.get('red_nedeni'),
        )
        db.session.add(it)
        print(f'  + İzin: {iz["sicil"]} — {iz["tur"]} ({iz["durum"]})')

    db.session.flush()
    print('  OK\n')
