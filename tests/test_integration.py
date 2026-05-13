import pytest
from app.models.makine import UretimVerisi, Makine
from app.models.stok import Malzeme, StokHareketi
from app.models.kalite import HataKaydi
from datetime import datetime

def test_uretim_stok_entegrasyonu(app, session, temel_veriler):
    """Üretim yapıldığında ilgili stoktan malzemenin düşmesini simüle eden test."""
    m1 = session.get(Makine, temel_veriler['makine_id'])
    
    # 1. Hammadde tanımla
    malzeme = Malzeme(kod='HM-001', ad='Çelik Levha', birim='Adet', mevcut_miktar=1000)
    session.add(malzeme)
    session.commit()
    
    # 2. Üretim gir
    uretim = UretimVerisi(
        makine_id=m1.id,
        calisan_id=temel_veriler['calisan_id'],
        tarih=datetime.now(),
        vardiya='sabah',
        planlanan_sure_dk=480,
        gercek_calisma_dk=480,
        gercek_uretim=100,
        hatali_uretim=0
    )
    uretim.hesapla_oee(m1.teorik_kapasite)
    session.add(uretim)
    
    # 3. Stok hareketi (üretim tüketimi) - Gerçekte bu serviste otomatik yapılır, burada simüle ediyoruz
    hareket = StokHareketi(
        malzeme_id=malzeme.id,
        hareket_turu='cikis',
        miktar=100,
        tarih=datetime.now(),
        neden='Üretim sarfiyatı',
        islem_yapan_id=temel_veriler['kullanici_id']
    )
    malzeme.mevcut_miktar -= 100
    session.add(hareket)
    session.commit()
    
    # 4. Doğrula
    assert malzeme.mevcut_miktar == 900
    assert uretim.oee_yuzde is not None
