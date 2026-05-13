"""
FabrikaOS — Kapsamlı Demo Verisi Yükleyici
Senaryo: AnadoluTech Metal Sanayi A.Ş. (Otomotiv Yan Sanayi — Kocaeli OSB)

Tüm 18+ tabloyu gerçekçi endüstriyel demo verileriyle doldurur.
Satış demolarında ve müşteri sunumlarında sistemin tam kapasitesini sergilemek için
tasarlanmıştır.

Kullanım:
    python seed_data.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db


def run_seed():
    """Tüm seed modüllerini sırasıyla çalıştırır."""
    app = create_app('development')

    with app.app_context():
        print('\n' + '=' * 60)
        print('  FabrikaOS — Kapsamlı Demo Verisi Yükleme')
        print('  Senaryo: AnadoluTech Metal Sanayi A.Ş.')
        print('=' * 60 + '\n')

        # Mevcut verileri temizle
        print('[0/13] Mevcut veriler temizleniyor...')
        meta = db.metadata
        for table in reversed(meta.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        print('  OK Tüm tablolar temizlendi\n')

        # Tabloları oluştur
        print('[0/13] Veritabanı tabloları kontrol ediliyor...')
        db.create_all()
        print('  OK Tablolar hazır\n')

        # Modülleri sırasıyla çalıştır
        from seeds import seed_kullanici
        seed_kullanici.seed()

        from seeds import seed_makine
        seed_makine.seed()

        from seeds import seed_uretim
        seed_uretim.seed()

        from seeds import seed_stok
        seed_stok.seed()

        from seeds import seed_vardiya
        seed_vardiya.seed()

        from seeds import seed_kalite
        seed_kalite.seed()

        from seeds import seed_enerji
        seed_enerji.seed()

        from seeds import seed_isg
        seed_isg.seed()

        from seeds import seed_bildirim
        seed_bildirim.seed()

        from seeds import seed_is_emri
        seed_is_emri.seed()

        from seeds import seed_analitik
        seed_analitik.seed()

        from seeds import seed_tahmin
        seed_tahmin.seed()

        # Kaydet
        db.session.commit()

        print('=' * 60)
        print('  OK Demo verisi başarıyla yüklendi!')
        print('=' * 60)
        print()
        print('  +--------------------------------------------------+')
        print('  |  AnadoluTech Metal Sanayi A.S. — Giris Bilgileri |')
        print('  +------------------+-----------------+-------------+')
        print('  | Rol              | Kullanici       | Sifre       |')
        print('  +------------------+-----------------+-------------+')
        print('  | Yonetici         | admin           | admin123    |')
        print('  | Operator         | ahmet.yilmaz    | demo123     |')
        print('  | Operator         | fatma.demir     | demo123     |')
        print('  | Teknisyen        | mehmet.kaya     | demo123     |')
        print('  | Teknisyen        | ayse.ozkan      | demo123     |')
        print('  +------------------+-----------------+-------------+')
        print()
        print('  Yuklenen Modüller:')
        print('  ------------------')
        print('  [x] Kullanicilar ve Calisanlar (5 kullanici, 15 calisan)')
        print('  [x] Makine Parki (6 makine, maliyet bilgileri dahil)')
        print('  [x] Uretim Verileri (30 gunluk, 3 vardiya, OEE hesaplamali)')
        print('  [x] Ariza Kayitlari (8 ariza — acik + cozulmus)')
        print('  [x] Bakim Kayitlari (9 bakim — periyodik + korektif)')
        print('  [x] Durus Kayitlari (14 gunluk, 6 kategori)')
        print('  [x] Stok Yonetimi (7 tedarikci, 12 malzeme, 18 hareket)')
        print('  [x] Vardiya Planlari (2 haftalik, 15 calisan)')
        print('  [x] Izin Talepleri (8 talep — bekliyor/onaylandi/reddedildi)')
        print('  [x] Kalite Kontrol (8 hata, 5 CAPA duzeltici faaliyet)')
        print('  [x] Enerji Tuketimi (5 ay, 5 tur, makine bazli detay)')
        print('  [x] ISG (5 kaza/ramak kala, 8 risk, 12 egitim)')
        print('  [x] Bildirimler (15+ bildirim, 12 denetim izi)')
        print('  [x] Is Emirleri (10 is emri, 5 yorum, SLA takipli)')
        print('  [x] KPI Hedefleri (11 KPI × 12 ay)')
        print('  [x] AI Tahminleme (14 tahmin — bakim/oee/stok/anomali)')
        print()
        print('  > python run.py ile uygulamayi baslatin')
        print('  > http://localhost:5000\n')


if __name__ == '__main__':
    run_seed()
