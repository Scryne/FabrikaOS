"""
FabrikaOS — Enerji Yönetimi Demo Verisi (v2 — 6 Ay, 5 Enerji Türü)
Makine bazlı detay, hedef-gerçekleşen karşılaştırması, karbon ayak izi
"""
import random
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from app.extensions import db
from app.models.enerji import EnerjiTuketimi
from app.models.makine import Makine


def seed():
    print('[11/22] Enerji yönetimi...')
    random.seed(7890)

    bugun = date.today()
    makineler = Makine.query.filter_by(aktif=True).all()

    # Enerji türleri ve birim bilgileri
    enerji_turleri = [
        {'tur': 'elektrik', 'birim': 'kWh', 'birim_fiyat': 4.85, 'karbon_katsayi': 0.47},
        {'tur': 'dogalgaz', 'birim': 'm³', 'birim_fiyat': 8.20, 'karbon_katsayi': 2.01},
        {'tur': 'su', 'birim': 'm³', 'birim_fiyat': 32.50, 'karbon_katsayi': 0.0},
        {'tur': 'basinclihava', 'birim': 'm³', 'birim_fiyat': 0.65, 'karbon_katsayi': 0.0},
        {'tur': 'buhar', 'birim': 'ton', 'birim_fiyat': 450.00, 'karbon_katsayi': 0.18},
    ]

    # Makine bazlı tüketim profilleri (aylık temel tüketim)
    makine_tuketim = {}
    for m in makineler:
        if 'CNC' in m.kod:
            makine_tuketim[m.id] = {'elektrik': 8500, 'dogalgaz': 0, 'su': 45, 'basinclihava': 1200, 'buhar': 0}
        elif 'ABK' in m.kod:
            makine_tuketim[m.id] = {'elektrik': 12000, 'dogalgaz': 0, 'su': 30, 'basinclihava': 800, 'buhar': 0}
        elif 'PRS' in m.kod:
            makine_tuketim[m.id] = {'elektrik': 15000, 'dogalgaz': 200, 'su': 120, 'basinclihava': 2000, 'buhar': 0}
        elif 'KYN' in m.kod:
            makine_tuketim[m.id] = {'elektrik': 6000, 'dogalgaz': 0, 'su': 20, 'basinclihava': 500, 'buhar': 0}
        elif 'TSL' in m.kod:
            makine_tuketim[m.id] = {'elektrik': 5500, 'dogalgaz': 0, 'su': 80, 'basinclihava': 300, 'buhar': 0}
        elif 'LZR' in m.kod:
            makine_tuketim[m.id] = {'elektrik': 18000, 'dogalgaz': 0, 'su': 200, 'basinclihava': 1500, 'buhar': 0}
        elif 'MNT' in m.kod:
            makine_tuketim[m.id] = {'elektrik': 3500, 'dogalgaz': 0, 'su': 15, 'basinclihava': 600, 'buhar': 0}
        else:
            makine_tuketim[m.id] = {'elektrik': 5000, 'dogalgaz': 0, 'su': 30, 'basinclihava': 400, 'buhar': 0}

    # Genel fabrika tüketimi (makine dışı — aydınlatma, ısıtma, ofis vs.)
    fabrika_genel = {'elektrik': 25000, 'dogalgaz': 1500, 'su': 500, 'basinclihava': 0, 'buhar': 8}

    # ── 6 AYLIK ENERJİ VERİSİ ──
    for ay_once in range(6, 0, -1):
        ay_bas = date(bugun.year, bugun.month - ay_once if bugun.month > ay_once else bugun.month - ay_once + 12,
                      1) if bugun.month > ay_once else date(bugun.year - 1, bugun.month - ay_once + 12, 1)
        # Ay sonu hesapla
        if ay_bas.month == 12:
            ay_son = date(ay_bas.year + 1, 1, 1) - timedelta(days=1)
        else:
            ay_son = date(ay_bas.year, ay_bas.month + 1, 1) - timedelta(days=1)

        # Mevsimsel çarpan (kış aylarında enerji tüketimi artar)
        mevsim_carpan = {1: 1.15, 2: 1.12, 3: 1.05, 4: 0.95, 5: 0.90, 6: 0.92,
                         7: 1.00, 8: 1.02, 9: 0.95, 10: 1.00, 11: 1.08, 12: 1.15}
        carpan = mevsim_carpan.get(ay_bas.month, 1.0)

        for enerji in enerji_turleri:
            tur = enerji['tur']

            # Makine bazlı tüketim kayıtları
            for makine in makineler:
                temel = makine_tuketim.get(makine.id, {}).get(tur, 0)
                if temel == 0:
                    continue

                gercek = temel * carpan * random.uniform(0.85, 1.15)
                hedef = temel * carpan * 0.95  # Hedef: %5 altında

                maliyet = gercek * enerji['birim_fiyat']
                karbon = gercek * enerji['karbon_katsayi'] / 1000  # ton CO2

                et = EnerjiTuketimi(
                    makine_id=makine.id,
                    enerji_turu=tur,
                    birim=enerji['birim'],
                    miktar=round(gercek, 2),
                    hedef_miktar=round(hedef, 2),
                    birim_fiyat=enerji['birim_fiyat'],
                    toplam_maliyet=round(maliyet, 2),
                    karbon_salinimi=round(karbon, 4),
                    donem_baslangic=ay_bas,
                    donem_bitis=ay_son,
                    notlar=None,
                )
                db.session.add(et)

            # Fabrika genel tüketim
            genel = fabrika_genel.get(tur, 0)
            if genel > 0:
                gercek = genel * carpan * random.uniform(0.90, 1.10)
                hedef = genel * carpan * 0.92

                et = EnerjiTuketimi(
                    enerji_turu=tur,
                    birim=enerji['birim'],
                    miktar=round(gercek, 2),
                    hedef_miktar=round(hedef, 2),
                    birim_fiyat=enerji['birim_fiyat'],
                    toplam_maliyet=round(gercek * enerji['birim_fiyat'], 2),
                    karbon_salinimi=round(gercek * enerji['karbon_katsayi'] / 1000, 4),
                    donem_baslangic=ay_bas,
                    donem_bitis=ay_son,
                    notlar='Fabrika genel tüketim (aydınlatma, ısıtma, ofis)',
                )
                db.session.add(et)

    db.session.flush()
    print(f'  + 6 aylık enerji verisi oluşturuldu (5 tür × {len(makineler)} makine + fabrika genel)\n')
