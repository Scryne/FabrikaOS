"""
FabrikaOS — Makine Parkı Demo Verisi
Senaryo: AnadoluTech Metal Sanayi — 6 adet endüstriyel üretim makinesi
Fabrika haritası koordinatları, satın alma fiyatları ve birim satış fiyatları dahil.
"""
from datetime import date
from app.extensions import db
from app.models.makine import Makine


def seed():
    print('[2/12] Makineler...')

    makineler = [
            {
                'ad': 'CNC Torna T-400',
                'kod': 'CNC-001',
                'marka': 'Doosan',
                'model': 'Lynx 2100LY',
                'teorik_kapasite': 48,  # adet/saat
                'hedef_oee': 85.00,
                'satin_alma_tarihi': date(2020, 5, 12),
                'garantisi_bitis': date(2025, 5, 12),
                'son_bakim_tarihi': date(2026, 4, 15),
                'periyodik_bakim_gun': 90,
                'lokasyon': 'A Hattı — Talaşlı İmalat',
                'durum': 'aktif',
                'satin_alma_fiyati': 1850000.00,
                'birim_satis_fiyati': 42.50,
                'konum_x': 80.0, 'konum_y': 80.0, 'konum_w': 150, 'konum_h': 85,
            },
            {
                'ad': 'CNC Freze F-200',
                'kod': 'CNC-002',
                'marka': 'Mazak',
                'model': 'VCN-530C',
                'teorik_kapasite': 32,
                'hedef_oee': 82.00,
                'satin_alma_tarihi': date(2019, 8, 20),
                'garantisi_bitis': date(2024, 8, 20),
                'son_bakim_tarihi': date(2026, 3, 20),
                'periyodik_bakim_gun': 60,
                'lokasyon': 'A Hattı — Talaşlı İmalat',
                'durum': 'aktif',
                'satin_alma_fiyati': 2200000.00,
                'birim_satis_fiyati': 68.00,
                'konum_x': 280.0, 'konum_y': 80.0, 'konum_w': 150, 'konum_h': 85,
            },
            {
                'ad': 'Abkant Pres A-50',
                'kod': 'ABK-001',
                'marka': 'Durmazlar',
                'model': 'AD-R 25100',
                'teorik_kapasite': 120,
                'hedef_oee': 88.00,
                'satin_alma_tarihi': date(2021, 3, 5),
                'garantisi_bitis': date(2026, 3, 5),
                'son_bakim_tarihi': date(2026, 4, 28),
                'periyodik_bakim_gun': 45,
                'lokasyon': 'B Hattı — Sac İşleme',
                'durum': 'aktif',
                'satin_alma_fiyati': 3400000.00,
                'birim_satis_fiyati': 12.80,
                'konum_x': 700.0, 'konum_y': 120.0, 'konum_w': 150, 'konum_h': 85,
            },
            {
                'ad': 'Hidrolik Pres P-200',
                'kod': 'PRS-001',
                'marka': 'Schuler',
                'model': 'MSD-200T',
                'teorik_kapasite': 80,
                'hedef_oee': 80.00,
                'satin_alma_tarihi': date(2018, 11, 10),
                'garantisi_bitis': date(2023, 11, 10),
                'son_bakim_tarihi': date(2026, 2, 10),
                'periyodik_bakim_gun': 90,
                'lokasyon': 'C Hattı — Şekillendirme',
                'durum': 'arizali',
                'satin_alma_fiyati': 1450000.00,
                'birim_satis_fiyati': 28.50,
                'konum_x': 150.0, 'konum_y': 420.0, 'konum_w': 150, 'konum_h': 85,
            },
            {
                'ad': 'Kaynak Robotu R-120',
                'kod': 'KYN-001',
                'marka': 'FANUC',
                'model': 'Arc Mate 120iC/10L',
                'teorik_kapasite': 60,
                'hedef_oee': 90.00,
                'satin_alma_tarihi': date(2022, 6, 15),
                'garantisi_bitis': date(2027, 6, 15),
                'son_bakim_tarihi': date(2026, 4, 1),
                'periyodik_bakim_gun': 30,
                'lokasyon': 'D Hattı — Kaynak ve Montaj',
                'durum': 'aktif',
                'satin_alma_fiyati': 2800000.00,
                'birim_satis_fiyati': 55.00,
                'konum_x': 900.0, 'konum_y': 420.0, 'konum_w': 150, 'konum_h': 85,
            },
            {
                'ad': 'Silindirik Taşlama S-33',
                'kod': 'TSL-001',
                'marka': 'Studer',
                'model': 'S33 CNC',
                'teorik_kapasite': 38,
                'hedef_oee': 78.00,
                'satin_alma_tarihi': date(2017, 2, 1),
                'garantisi_bitis': date(2022, 2, 1),
                'son_bakim_tarihi': date(2026, 4, 20),
                'periyodik_bakim_gun': 60,
                'lokasyon': 'A Hattı — Talaşlı İmalat',
                'durum': 'aktif',
                'satin_alma_fiyati': 1650000.00,
                'birim_satis_fiyati': 85.00,
                'konum_x': 80.0, 'konum_y': 200.0, 'konum_w': 150, 'konum_h': 85,
            },
        ]

    for m_data in makineler:
        if Makine.query.filter_by(kod=m_data['kod']).first():
            continue
        m = Makine(**m_data, aktif=True)
        db.session.add(m)
        print(f'  + {m_data["ad"]} ({m_data["kod"]}) — {m_data["lokasyon"]}')

    db.session.flush()
    print('  OK\n')
