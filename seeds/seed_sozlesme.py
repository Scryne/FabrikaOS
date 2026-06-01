"""
FabrikaOS — Sözleşme Yönetimi Demo Verisi (v2)
Sözleşme, Kira, Sigorta, ve Kurumsal Metinler
"""
import random
from datetime import datetime, timedelta, timezone
from app.extensions import db
from app.models.sozlesme import Sozlesme, KiraKontrat, SigortaPolice
from app.models.crm import Firma
from app.models.kullanici import Kullanici


def seed():
    print('[23/22] Sözleşmeler...') # Bu numara genel sayaç için sembolik, asıl sayaç task.md'de

    muhasebe = Kullanici.query.filter_by(rol='muhasebe').first() or Kullanici.query.first()
    ortaklar = Firma.query.all()
    bugun = datetime.now(timezone.utc)

    # ── GENEL SÖZLEŞMELER ──
    sozlesmeler = [
        {'adi': 'Yıllık Bakım Anlaşması', 'tur': 'bakim', 'tutar': 120000.0, 'para_birimi': 'TL', 'sure_ay': 12, 'durum': 'aktif'},
        {'adi': 'Hammadde Tedarik Çerçeve Sözleşmesi', 'tur': 'diger', 'tutar': 5000000.0, 'para_birimi': 'TL', 'sure_ay': 24, 'durum': 'aktif'},
        {'adi': 'ERP Yazılım Lisans Sözleşmesi', 'tur': 'diger', 'tutar': 15000.0, 'para_birimi': 'USD', 'sure_ay': 12, 'durum': 'aktif'},
        {'adi': 'Lojistik Taşıma Sözleşmesi', 'tur': 'hizmet', 'tutar': 250000.0, 'para_birimi': 'TL', 'sure_ay': 12, 'durum': 'aktif'},
        {'adi': 'Güvenlik Hizmet Alımı', 'tur': 'hizmet', 'tutar': 360000.0, 'para_birimi': 'TL', 'sure_ay': 12, 'durum': 'aktif'},
    ]

    for s in sozlesmeler:
        baslangic = bugun - timedelta(days=random.randint(30, 300))
        bitis = baslangic + timedelta(days=s['sure_ay'] * 30)
        
        ortak = random.choice(ortaklar) if ortaklar else None

        soz = Sozlesme(
            sozlesme_no=f"SZL-{bugun.year}-{random.randint(100, 999)}",
            baslik=s['adi'],
            tur=s['tur'],
            taraf_tip=Sozlesme.TARAF_FIRMA,
            taraf_id=ortak.id if ortak else 1,
            baslangic_tarihi=baslangic,
            bitis_tarihi=bitis,
            tutar=s['tutar'],
            para_birimi=s['para_birimi'],
            durum=s['durum'],
            aciklama='Standart sözleşme metni',
        )
        db.session.add(soz)

    # ── KİRA SÖZLEŞMELERİ ──
    kira_listesi = [
        {'mulk': 'Gebze OSB Fabrika Binası', 'tur': 'kira', 'tutar': 150000.0, 'doviz': 'TL', 'bas': bugun - timedelta(days=500), 'sure': 60, 'zam_orani': 65.0, 'blok': 'A'},
        {'mulk': 'Tuzla Depo Alanı', 'tur': 'kira', 'tutar': 45000.0, 'doviz': 'TL', 'bas': bugun - timedelta(days=200), 'sure': 24, 'zam_orani': 55.0, 'blok': 'B'},
    ]

    for k in kira_listesi:
        ortak = random.choice(ortaklar) if ortaklar else None
        soz = Sozlesme(
            sozlesme_no=f"KRA-{bugun.year}-{random.randint(100, 999)}",
            baslik=f"Kira Sözleşmesi - {k['mulk']}",
            tur='kira',
            taraf_tip=Sozlesme.TARAF_FIRMA,
            taraf_id=ortak.id if ortak else 1,
            baslangic_tarihi=k['bas'],
            bitis_tarihi=k['bas'] + timedelta(days=k['sure'] * 30),
            tutar=k['tutar'],
            para_birimi=k['doviz'],
            durum='aktif',
        )
        db.session.add(soz)
        db.session.flush()

        ks = KiraKontrat(
            sozlesme_id=soz.id,
            blok=k['blok'],
            kira_tutari=k['tutar'],
            artis_turu='tufe',
            artis_orani=k['zam_orani']
        )
        db.session.add(ks)

    # ── SİGORTA POLİÇELERİ ──
    sigortalar = [
        {'tur': 'yangin', 'sirket': 'Allianz Sigorta', 'police_no': 'ALZ-987654321', 'bedel': 50000000.0, 'prim': 120000.0},
        {'tur': 'genel_sorumluluk', 'sirket': 'Anadolu Sigorta', 'police_no': 'AND-123456789', 'bedel': 10000000.0, 'prim': 45000.0},
        {'tur': 'kasko', 'sirket': 'Axa Sigorta', 'police_no': 'AXA-456123789', 'bedel': 3000000.0, 'prim': 25000.0},
        {'tur': 'genel_sorumluluk', 'sirket': 'Mapfre Sigorta', 'police_no': 'MPF-321654987', 'bedel': 5000000.0, 'prim': 35000.0},
    ]

    for sg in sigortalar:
        bas = bugun - timedelta(days=random.randint(10, 300))
        bit = bas + timedelta(days=365)
        
        ortak = random.choice(ortaklar) if ortaklar else None
        soz = Sozlesme(
            sozlesme_no=f"SGR-{bugun.year}-{random.randint(100, 999)}",
            baslik=f"{sg['sirket']} - {sg['tur']} Poliçesi",
            tur='sigorta',
            taraf_tip=Sozlesme.TARAF_FIRMA,
            taraf_id=ortak.id if ortak else 1,
            baslangic_tarihi=bas,
            bitis_tarihi=bit,
            tutar=sg['prim'],
            para_birimi='TL',
            durum='aktif' if bit > bugun else 'sona_erdi',
        )
        db.session.add(soz)
        db.session.flush()

        pol = SigortaPolice(
            sozlesme_id=soz.id,
            police_no=sg['police_no'],
            sigorta_sirketi=sg['sirket'],
            sigorta_turu=sg['tur'],
            police_baslangic=bas,
            police_bitis=bit,
            teminat_tutari=sg['bedel'],
            prim_tutari=sg['prim'],
            durum='aktif' if bit > bugun else 'suresi_doldu'
        )
        db.session.add(pol)

    db.session.flush()
    print('  OK\n')
