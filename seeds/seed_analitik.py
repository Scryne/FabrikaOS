"""
FabrikaOS — KPI ve Analitik Demo Verisi (v2)
Fabrika geneli KPI hedefleri
"""
from datetime import date
from app.extensions import db
from app.models.analitik import KpiHedef


def seed():
    print('[20/22] Analitik (KPI Hedefleri)...')

    bugun = date.today()
    yil = bugun.year
    ay = bugun.month

    # Son 3 ay için hedefler
    hedefler = [
        # OEE Hedefleri
        {'kpi_kodu': 'ort_oee', 'kpi_adi': 'Fabrika Geneli OEE', 'hedef_deger': 85.0, 'birim': '%', 'modul': 'makine', 'yonu': 'yukari'},
        {'kpi_kodu': 'hata_orani', 'kpi_adi': 'Hata Oranı', 'hedef_deger': 2.5, 'birim': '%', 'modul': 'kalite', 'yonu': 'asagi'},
        {'kpi_kodu': 'ariza_sayisi', 'kpi_adi': 'Arıza Sayısı', 'hedef_deger': 15.0, 'birim': 'adet', 'modul': 'makine', 'yonu': 'asagi'},
        {'kpi_kodu': 'bakim_maliyeti', 'kpi_adi': 'Bakım Maliyeti', 'hedef_deger': 25000.0, 'birim': 'TL', 'modul': 'makine', 'yonu': 'asagi'},
        {'kpi_kodu': 'toplam_maliyet', 'kpi_adi': 'Enerji Maliyeti', 'hedef_deger': 45000.0, 'birim': 'TL', 'modul': 'enerji', 'yonu': 'asagi'},
        {'kpi_kodu': 'kaza_sayisi', 'kpi_adi': 'İş Kazası Sayısı', 'hedef_deger': 0.0, 'birim': 'adet', 'modul': 'isg', 'yonu': 'asagi'},
        {'kpi_kodu': 'devamsizlik', 'kpi_adi': 'Devamsızlık Oranı', 'hedef_deger': 2.0, 'birim': '%', 'modul': 'personel', 'yonu': 'asagi'},
        {'kpi_kodu': 'kritik_malzeme', 'kpi_adi': 'Kritik Stok Malzeme Sayısı', 'hedef_deger': 5.0, 'birim': 'adet', 'modul': 'stok', 'yonu': 'asagi'},
    ]

    for offset in range(3):
        m = ay - offset
        y = yil
        if m <= 0:
            m += 12
            y -= 1

        for h in hedefler:
            kpi = KpiHedef(
                yil=y,
                ay=m,
                kpi_kodu=h['kpi_kodu'],
                kpi_adi=h['kpi_adi'],
                hedef_deger=h['hedef_deger'],
                birim=h['birim'],
                modul=h['modul'],
                yonu=h['yonu'],
                periyot='aylik'
            )
            db.session.add(kpi)

    db.session.flush()
    print('  + KPI Hedefleri eklendi\n')
