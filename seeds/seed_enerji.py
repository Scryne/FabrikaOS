"""
FabrikaOS — Enerji Tüketim Demo Verisi
Senaryo: AnadoluTech Metal Sanayi — 5 aylık enerji takibi (Ocak-Mayıs 2026)

- 5 ay aylık elektrik (departman bazlı)
- 5 ay doğalgaz (mevsimsel değişimli)
- 5 ay su tüketimi
- Makine bazlı Nisan+Mayıs elektrik detayı
- Basınçlı hava kayıtları
- Toplam 35+ kayıt
"""
from datetime import date
from app.extensions import db
from app.models.enerji import EnerjiTuketimi
from app.models.makine import Makine
from app.models.kullanici import Kullanici


def seed():
    print('[10/12] Enerji tüketimi...')

    makineler = {m.kod: m.id for m in Makine.query.all()}
    admin = Kullanici.query.filter_by(kullanici_adi='admin').first()
    admin_id = admin.id if admin else 1

    kayitlar = [
        # ══════════════════════════════════════════════════════════════
        # ELEKTRİK — Departman bazlı aylık (Ocak → Mayıs)
        # ══════════════════════════════════════════════════════════════
        # Ocak — kış, ısıtma yükü var
        {'dept': 'Üretim', 'tur': 'elektrik', 'miktar': 52400, 'birim': 'kWh',
         'fiyat': 2.85, 'hedef': 48000, 'fatura': 'ELK-2026-01',
         'bas': date(2026, 1, 1), 'bit': date(2026, 1, 31),
         'not': 'Kış ayı — yoğun ısıtma + aydınlatma'},
        {'dept': 'İdari', 'tur': 'elektrik', 'miktar': 4200, 'birim': 'kWh',
         'fiyat': 2.85, 'hedef': 4000, 'fatura': 'ELK-2026-01-ID',
         'bas': date(2026, 1, 1), 'bit': date(2026, 1, 31)},

        # Şubat
        {'dept': 'Üretim', 'tur': 'elektrik', 'miktar': 49800, 'birim': 'kWh',
         'fiyat': 2.85, 'hedef': 48000, 'fatura': 'ELK-2026-02',
         'bas': date(2026, 2, 1), 'bit': date(2026, 2, 28),
         'not': '1 gün planlı üretim durma (bayram)'},
        {'dept': 'İdari', 'tur': 'elektrik', 'miktar': 3800, 'birim': 'kWh',
         'fiyat': 2.85, 'hedef': 4000, 'fatura': 'ELK-2026-02-ID',
         'bas': date(2026, 2, 1), 'bit': date(2026, 2, 28)},

        # Mart — bahar, ısıtma azalıyor
        {'dept': 'Üretim', 'tur': 'elektrik', 'miktar': 46500, 'birim': 'kWh',
         'fiyat': 2.90, 'hedef': 47000, 'fatura': 'ELK-2026-03',
         'bas': date(2026, 3, 1), 'bit': date(2026, 3, 31),
         'not': 'Hedefe yakın performans — enerji verimliliği projeleri etkili'},
        {'dept': 'İdari', 'tur': 'elektrik', 'miktar': 3500, 'birim': 'kWh',
         'fiyat': 2.90, 'hedef': 3800, 'fatura': 'ELK-2026-03-ID',
         'bas': date(2026, 3, 1), 'bit': date(2026, 3, 31)},

        # Nisan — sipariş artışı
        {'dept': 'Üretim', 'tur': 'elektrik', 'miktar': 51200, 'birim': 'kWh',
         'fiyat': 2.90, 'hedef': 47000, 'fatura': 'ELK-2026-04',
         'bas': date(2026, 4, 1), 'bit': date(2026, 4, 30),
         'not': 'Sipariş artışı — fazla mesai üretimleri'},
        {'dept': 'İdari', 'tur': 'elektrik', 'miktar': 3900, 'birim': 'kWh',
         'fiyat': 2.90, 'hedef': 3800, 'fatura': 'ELK-2026-04-ID',
         'bas': date(2026, 4, 1), 'bit': date(2026, 4, 30)},

        # Mayıs — devam eden yoğunluk
        {'dept': 'Üretim', 'tur': 'elektrik', 'miktar': 48900, 'birim': 'kWh',
         'fiyat': 2.95, 'hedef': 47000, 'fatura': 'ELK-2026-05',
         'bas': date(2026, 5, 1), 'bit': date(2026, 5, 13),
         'not': 'Mayıs ilk yarısı — soğutma ihtiyacı başladı'},
        {'dept': 'İdari', 'tur': 'elektrik', 'miktar': 3650, 'birim': 'kWh',
         'fiyat': 2.95, 'hedef': 3800, 'fatura': 'ELK-2026-05-ID',
         'bas': date(2026, 5, 1), 'bit': date(2026, 5, 13)},

        # ══════════════════════════════════════════════════════════════
        # DOĞALGAZ — Mevsimsel değişim (kıştan yaza azalma)
        # ══════════════════════════════════════════════════════════════
        {'dept': 'Üretim', 'tur': 'dogalgaz', 'miktar': 4200, 'birim': 'm3',
         'fiyat': 8.50, 'hedef': 3800, 'fatura': 'DGZ-2026-01',
         'bas': date(2026, 1, 1), 'bit': date(2026, 1, 31),
         'not': 'Kış dönemi — fabrika ısıtma yoğun'},
        {'dept': 'Üretim', 'tur': 'dogalgaz', 'miktar': 3600, 'birim': 'm3',
         'fiyat': 8.50, 'hedef': 3500, 'fatura': 'DGZ-2026-02',
         'bas': date(2026, 2, 1), 'bit': date(2026, 2, 28)},
        {'dept': 'Üretim', 'tur': 'dogalgaz', 'miktar': 2400, 'birim': 'm3',
         'fiyat': 8.75, 'hedef': 2800, 'fatura': 'DGZ-2026-03',
         'bas': date(2026, 3, 1), 'bit': date(2026, 3, 31),
         'not': 'Bahar — ısıtma ihtiyacı azaldı'},
        {'dept': 'Üretim', 'tur': 'dogalgaz', 'miktar': 1650, 'birim': 'm3',
         'fiyat': 8.75, 'hedef': 2000, 'fatura': 'DGZ-2026-04',
         'bas': date(2026, 4, 1), 'bit': date(2026, 4, 30),
         'not': 'Nisan — yalnızca proses ısıtma'},
        {'dept': 'Üretim', 'tur': 'dogalgaz', 'miktar': 1100, 'birim': 'm3',
         'fiyat': 8.90, 'hedef': 1500, 'fatura': 'DGZ-2026-05',
         'bas': date(2026, 5, 1), 'bit': date(2026, 5, 13),
         'not': 'Mayıs — minimal ısıtma, yalnızca proses'},

        # ══════════════════════════════════════════════════════════════
        # SU — Sabit endüstriyel tüketim + mevsimsel artış
        # ══════════════════════════════════════════════════════════════
        {'dept': 'Genel', 'tur': 'su', 'miktar': 380, 'birim': 'm3',
         'fiyat': 32.50, 'hedef': 400, 'fatura': 'SU-2026-01',
         'bas': date(2026, 1, 1), 'bit': date(2026, 1, 31)},
        {'dept': 'Genel', 'tur': 'su', 'miktar': 365, 'birim': 'm3',
         'fiyat': 32.50, 'hedef': 400, 'fatura': 'SU-2026-02',
         'bas': date(2026, 2, 1), 'bit': date(2026, 2, 28)},
        {'dept': 'Genel', 'tur': 'su', 'miktar': 420, 'birim': 'm3',
         'fiyat': 33.00, 'hedef': 400, 'fatura': 'SU-2026-03',
         'bas': date(2026, 3, 1), 'bit': date(2026, 3, 31),
         'not': 'Soğutma havuzları dolumu (mevsimsel bakım)'},
        {'dept': 'Genel', 'tur': 'su', 'miktar': 445, 'birim': 'm3',
         'fiyat': 33.00, 'hedef': 420, 'fatura': 'SU-2026-04',
         'bas': date(2026, 4, 1), 'bit': date(2026, 4, 30),
         'not': 'Hava sıcaklığı artışı — soğutma suyu tüketimi arttı'},
        {'dept': 'Genel', 'tur': 'su', 'miktar': 470, 'birim': 'm3',
         'fiyat': 33.50, 'hedef': 420, 'fatura': 'SU-2026-05',
         'bas': date(2026, 5, 1), 'bit': date(2026, 5, 13),
         'not': 'Mayıs — soğutma suyu tüketimi artmaya devam ediyor'},

        # ══════════════════════════════════════════════════════════════
        # BASINÇLI HAVA — Kompresör tüketimi
        # ══════════════════════════════════════════════════════════════
        {'dept': 'Üretim', 'tur': 'basincli_hava', 'miktar': 8500, 'birim': 'm3',
         'fiyat': 0.42, 'hedef': 8000,
         'bas': date(2026, 3, 1), 'bit': date(2026, 3, 31),
         'not': 'Pnömatik tüketim — hidrolik pres ve abkant hatları'},
        {'dept': 'Üretim', 'tur': 'basincli_hava', 'miktar': 9200, 'birim': 'm3',
         'fiyat': 0.42, 'hedef': 8000,
         'bas': date(2026, 4, 1), 'bit': date(2026, 4, 30),
         'not': 'Sipariş artışı ile basınçlı hava tüketimi arttı'},
        {'dept': 'Üretim', 'tur': 'basincli_hava', 'miktar': 8800, 'birim': 'm3',
         'fiyat': 0.43, 'hedef': 8000,
         'bas': date(2026, 5, 1), 'bit': date(2026, 5, 13),
         'not': 'Mayıs — yoğun üretim devam ediyor'},

        # ══════════════════════════════════════════════════════════════
        # MAKİNE BAZLI ELEKTRİK (Nisan ayı detayı)
        # ══════════════════════════════════════════════════════════════
        {'dept': 'Üretim', 'tur': 'elektrik', 'miktar': 8900, 'birim': 'kWh',
         'fiyat': 2.90, 'hedef': 8200, 'makine': 'CNC-001',
         'bas': date(2026, 4, 1), 'bit': date(2026, 4, 30),
         'not': 'CNC Torna — yoğun sipariş dönemi'},
        {'dept': 'Üretim', 'tur': 'elektrik', 'miktar': 6400, 'birim': 'kWh',
         'fiyat': 2.90, 'hedef': 6800, 'makine': 'CNC-002',
         'bas': date(2026, 4, 1), 'bit': date(2026, 4, 30),
         'not': 'CNC Freze — hedefin altında (verimli)'},
        {'dept': 'Üretim', 'tur': 'elektrik', 'miktar': 14200, 'birim': 'kWh',
         'fiyat': 2.90, 'hedef': 13000, 'makine': 'ABK-001',
         'bas': date(2026, 4, 1), 'bit': date(2026, 4, 30),
         'not': 'Abkant — hidrolik ünite yüksek tüketim'},
        {'dept': 'Üretim', 'tur': 'elektrik', 'miktar': 9800, 'birim': 'kWh',
         'fiyat': 2.90, 'hedef': 10500, 'makine': 'PRS-001',
         'bas': date(2026, 4, 1), 'bit': date(2026, 4, 30),
         'not': 'Pres — arıza nedeniyle kapasite altında çalıştı'},
        {'dept': 'Üretim', 'tur': 'elektrik', 'miktar': 5600, 'birim': 'kWh',
         'fiyat': 2.90, 'hedef': 5500, 'makine': 'KYN-001',
         'bas': date(2026, 4, 1), 'bit': date(2026, 4, 30),
         'not': 'Kaynak robotu — normal tüketim seviyesi'},
        {'dept': 'Üretim', 'tur': 'elektrik', 'miktar': 4100, 'birim': 'kWh',
         'fiyat': 2.90, 'hedef': 4200, 'makine': 'TSL-001',
         'bas': date(2026, 4, 1), 'bit': date(2026, 4, 30),
         'not': 'Taşlama — hedefin altında (iyi performans)'},

        # Mayıs ayı makine bazlı detay
        {'dept': 'Üretim', 'tur': 'elektrik', 'miktar': 4500, 'birim': 'kWh',
         'fiyat': 2.95, 'hedef': 4100, 'makine': 'CNC-001',
         'bas': date(2026, 5, 1), 'bit': date(2026, 5, 13),
         'not': 'Mayıs ilk yarısı — yoğun sipariş devam'},
        {'dept': 'Üretim', 'tur': 'elektrik', 'miktar': 3400, 'birim': 'kWh',
         'fiyat': 2.95, 'hedef': 3400, 'makine': 'CNC-002',
         'bas': date(2026, 5, 1), 'bit': date(2026, 5, 13),
         'not': 'Hedefe tam uyum'},
        {'dept': 'Üretim', 'tur': 'elektrik', 'miktar': 7800, 'birim': 'kWh',
         'fiyat': 2.95, 'hedef': 6500, 'makine': 'ABK-001',
         'bas': date(2026, 5, 1), 'bit': date(2026, 5, 13),
         'not': 'Abkant — enerji anomalisi araştırılıyor'},
        {'dept': 'Üretim', 'tur': 'elektrik', 'miktar': 3200, 'birim': 'kWh',
         'fiyat': 2.95, 'hedef': 5250, 'makine': 'PRS-001',
         'bas': date(2026, 5, 1), 'bit': date(2026, 5, 13),
         'not': 'Pres arızalı — düşük kapasite'},
        {'dept': 'Üretim', 'tur': 'elektrik', 'miktar': 2900, 'birim': 'kWh',
         'fiyat': 2.95, 'hedef': 2750, 'makine': 'KYN-001',
         'bas': date(2026, 5, 1), 'bit': date(2026, 5, 13),
         'not': 'Normal seviye'},
        {'dept': 'Üretim', 'tur': 'elektrik', 'miktar': 2100, 'birim': 'kWh',
         'fiyat': 2.95, 'hedef': 2100, 'makine': 'TSL-001',
         'bas': date(2026, 5, 1), 'bit': date(2026, 5, 13),
         'not': 'Verimli çalışma'},
    ]

    for k in kayitlar:
        makine_id = makineler.get(k.get('makine')) if k.get('makine') else None
        et = EnerjiTuketimi(
            makine_id=makine_id,
            departman=k['dept'],
            enerji_turu=k['tur'],
            miktar=k['miktar'],
            birim=k['birim'],
            birim_fiyat=k['fiyat'],
            hedef_miktar=k['hedef'],
            fatura_no=k.get('fatura'),
            donem_baslangic=k['bas'],
            donem_bitis=k['bit'],
            notlar=k.get('not'),
            kaydeden_id=admin_id,
        )
        et.hesapla_maliyet_ve_karbon()
        db.session.add(et)

    db.session.flush()
    toplam = len(kayitlar)
    print(f'  + {toplam} enerji kaydı oluşturuldu (elektrik, doğalgaz, su, basınçlı hava)\n')
