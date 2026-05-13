"""
FabrikaOS — KPI Hedef Demo Verileri
Senaryo: AnadoluTech Metal Sanayi A.Ş.
"""

from datetime import datetime, timezone
from app.extensions import db
from app.models.analitik import KpiHedef
from app.models.kullanici import Kullanici


def seed():
    print('[11/12] KPI Hedef demo verileri yükleniyor...')

    admin = Kullanici.query.filter_by(kullanici_adi='admin').first()
    yil = datetime.now(timezone.utc).year

    # Varsayılan hedef değerleri (endüstriyel standartlar)
    hedef_verileri = [
        {'modul': 'makine', 'kpi_kodu': 'ort_oee', 'kpi_adi': 'Ortalama OEE', 'birim': '%', 'yonu': 'yukari',
         'hedef': 85, 'alt_limit': 75, 'ust_limit': None},
        {'modul': 'makine', 'kpi_kodu': 'ariza_sayisi', 'kpi_adi': 'Arıza Sayısı', 'birim': 'adet', 'yonu': 'asagi',
         'hedef': 5, 'alt_limit': None, 'ust_limit': 10},
        {'modul': 'makine', 'kpi_kodu': 'bakim_maliyeti', 'kpi_adi': 'Bakım Maliyeti', 'birim': 'TL', 'yonu': 'asagi',
         'hedef': 50000, 'alt_limit': None, 'ust_limit': 75000},
        {'modul': 'kalite', 'kpi_kodu': 'hata_orani', 'kpi_adi': 'Hata Oranı', 'birim': '%', 'yonu': 'asagi',
         'hedef': 2.0, 'alt_limit': None, 'ust_limit': 3.5},
        {'modul': 'kalite', 'kpi_kodu': 'fire_orani', 'kpi_adi': 'Fire Oranı', 'birim': '%', 'yonu': 'asagi',
         'hedef': 1.5, 'alt_limit': None, 'ust_limit': 2.5},
        {'modul': 'enerji', 'kpi_kodu': 'toplam_maliyet', 'kpi_adi': 'Enerji Maliyeti', 'birim': 'TL', 'yonu': 'asagi',
         'hedef': 120000, 'alt_limit': None, 'ust_limit': 150000},
        {'modul': 'enerji', 'kpi_kodu': 'birim_tuketim', 'kpi_adi': 'Birim Enerji Tüketimi', 'birim': 'kWh/adet', 'yonu': 'asagi',
         'hedef': 1.0, 'alt_limit': None, 'ust_limit': 1.5},
        {'modul': 'isg', 'kpi_kodu': 'kaza_sayisi', 'kpi_adi': 'İş Kazası Sayısı', 'birim': 'adet', 'yonu': 'asagi',
         'hedef': 0, 'alt_limit': None, 'ust_limit': 2},
        {'modul': 'isg', 'kpi_kodu': 'kayip_gun', 'kpi_adi': 'Kayıp İş Günü', 'birim': 'gün', 'yonu': 'asagi',
         'hedef': 0, 'alt_limit': None, 'ust_limit': 5},
        {'modul': 'stok', 'kpi_kodu': 'kritik_malzeme', 'kpi_adi': 'Kritik Stok Malzeme', 'birim': 'adet', 'yonu': 'asagi',
         'hedef': 3, 'alt_limit': None, 'ust_limit': 6},
        {'modul': 'personel', 'kpi_kodu': 'devamsizlik', 'kpi_adi': 'Devamsızlık Oranı', 'birim': '%', 'yonu': 'asagi',
         'hedef': 5, 'alt_limit': None, 'ust_limit': 8},
    ]

    eklenen = 0
    for veri in hedef_verileri:
        # Her KPI için 12 aylık hedef oluştur
        for ay in range(1, 13):
            mevcut = KpiHedef.query.filter_by(
                modul=veri['modul'], kpi_kodu=veri['kpi_kodu'], yil=yil, ay=ay
            ).first()
            if not mevcut:
                hedef = KpiHedef(
                    modul=veri['modul'],
                    kpi_adi=veri['kpi_adi'],
                    kpi_kodu=veri['kpi_kodu'],
                    birim=veri['birim'],
                    hedef_deger=veri['hedef'],
                    alt_limit=veri['alt_limit'],
                    ust_limit=veri['ust_limit'],
                    yonu=veri['yonu'],
                    periyot='aylik',
                    yil=yil,
                    ay=ay,
                    olusturan_id=admin.id if admin else None,
                )
                db.session.add(hedef)
                eklenen += 1

    print(f'  OK {eklenen} KPI hedefi oluşturuldu ({len(hedef_verileri)} KPI × 12 ay)')
