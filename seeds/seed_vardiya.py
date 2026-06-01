"""
FabrikaOS — Vardiya Planı ve İzin Talebi Demo Verisi (v2 — 20 Çalışan)
3 haftalık vardiya planı, 12 izin talebi (tüm durum ve türler)
"""
from datetime import date, time, timedelta, datetime, timezone
from app.extensions import db
from app.models.personel import Calisan, VardiyaPlani, IzinTalebi
from app.models.kullanici import Kullanici


def seed():
    print('[8/22] Vardiyalar ve İzinler...')

    calisanlar = Calisan.query.filter_by(aktif=True).all()
    bugun = date.today()
    admin = Kullanici.query.filter_by(kullanici_adi='admin').first()

    vardiya_map = {
        'sabah': (time(6, 0), time(14, 0)),
        'ogleden_sonra': (time(14, 0), time(22, 0)),
        'gece': (time(22, 0), time(6, 0)),
    }
    turler = ['sabah', 'ogleden_sonra', 'gece']

    # ── 3 HAFTALIK VARDİYA PLANI ──
    # Geçmiş 7 gün + gelecek 14 gün
    for gun in range(-7, 14):
        tarih = bugun + timedelta(days=gun)
        if tarih.weekday() == 6:  # Pazar
            continue
        for i, calisan in enumerate(calisanlar):
            if tarih.weekday() == 5:
                tur = 'sabah'
            else:
                tur = turler[(i + gun) % 3]

            bas, bit = vardiya_map[tur]

            notlar = None
            if gun == 0 and i == 0:
                notlar = 'Bugünkü vardiya — fazla mesai planlandı (+2 saat)'
            elif gun == 1 and i == 2:
                notlar = 'Müşteri denetimi — özel dikkat'
            elif gun == -1 and i == 3:
                notlar = 'Fazla mesai tamamlandı (2 saat)'

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
    print('  + 3 haftalık vardiya planı oluşturuldu (20 çalışan)')

    # ── İZİN TALEPLERİ (12 adet — 4 bekliyor, 5 onaylandı, 3 reddedildi) ──
    izinler = [
        # Bekleyen talepler (4)
        {
            'sicil': 'P001', 'bas': bugun + timedelta(days=15), 'bit': bugun + timedelta(days=21),
            'tur': 'yillik', 'aciklama': 'Ailece tatil planı — Antalya', 'durum': 'bekliyor',
        },
        {
            'sicil': 'P005', 'bas': bugun + timedelta(days=8), 'bit': bugun + timedelta(days=8),
            'tur': 'mazeret', 'aciklama': 'Kardeş nikah töreni — İstanbul', 'durum': 'bekliyor',
        },
        {
            'sicil': 'P012', 'bas': bugun + timedelta(days=12), 'bit': bugun + timedelta(days=14),
            'tur': 'yillik', 'aciklama': 'Kişisel işler — Karabük seyahati', 'durum': 'bekliyor',
        },
        {
            'sicil': 'P016', 'bas': bugun + timedelta(days=5), 'bit': bugun + timedelta(days=5),
            'tur': 'saglik', 'aciklama': 'Hastane randevusu — göz muayenesi', 'durum': 'bekliyor',
        },

        # Onaylanmış talepler (5)
        {
            'sicil': 'P002', 'bas': bugun - timedelta(days=5), 'bit': bugun - timedelta(days=3),
            'tur': 'saglik', 'aciklama': 'Diş ameliyatı ve istirahat raporu (3 gün)', 'durum': 'onaylandi',
        },
        {
            'sicil': 'P003', 'bas': bugun - timedelta(days=22), 'bit': bugun - timedelta(days=16),
            'tur': 'yillik', 'aciklama': 'Yıllık izin kullanımı — memleket ziyareti (Trabzon)', 'durum': 'onaylandi',
        },
        {
            'sicil': 'P009', 'bas': bugun + timedelta(days=3), 'bit': bugun + timedelta(days=4),
            'tur': 'mazeret', 'aciklama': 'Ev taşınma — taşınma firması organizasyonu', 'durum': 'onaylandi',
        },
        {
            'sicil': 'P011', 'bas': bugun - timedelta(days=10), 'bit': bugun - timedelta(days=9),
            'tur': 'mazeret', 'aciklama': 'Eşinin hastane randevusuna refakat', 'durum': 'onaylandi',
        },
        {
            'sicil': 'P017', 'bas': bugun - timedelta(days=3), 'bit': bugun - timedelta(days=1),
            'tur': 'yillik', 'aciklama': 'Kısa tatil — Bolu Abant', 'durum': 'onaylandi',
        },

        # Reddedilmiş talepler (3)
        {
            'sicil': 'P006', 'bas': bugun + timedelta(days=30), 'bit': bugun + timedelta(days=44),
            'tur': 'ucretsiz', 'aciklama': 'Kişisel nedenler — yurt dışı seyahat',
            'durum': 'reddedildi',
            'red_nedeni': 'Mayıs-Haziran dönemi üretim yoğunluğu nedeniyle 15 günlük ücretsiz izin uygun bulunmamıştır. Daha kısa süreli yıllık izin değerlendirilebilir.',
        },
        {
            'sicil': 'P007', 'bas': bugun + timedelta(days=10), 'bit': bugun + timedelta(days=17),
            'tur': 'yillik', 'aciklama': 'Aile düğünü — İzmir',
            'durum': 'reddedildi',
            'red_nedeni': 'Müşteri denetimi dönemine denk gelmektedir. Bir hafta sonrası için yeniden başvurabilirsiniz.',
        },
        {
            'sicil': 'P013', 'bas': bugun + timedelta(days=20), 'bit': bugun + timedelta(days=20),
            'tur': 'mazeret', 'aciklama': 'Arkadaş düğünü',
            'durum': 'reddedildi',
            'red_nedeni': 'Aynı tarihte kalite kontrol departmanından başka izinli yoktur. Departmanda en az 1 kişi bulunmalıdır.',
        },
    ]

    for iz in izinler:
        calisan = Calisan.query.filter_by(sicil_no=iz['sicil']).first()
        if not calisan:
            continue
        onaylayan_id = admin.id if admin and iz['durum'] != 'bekliyor' else None
        onay_tarihi = None
        if onaylayan_id:
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
