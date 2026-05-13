import pytest
from app.models.makine import UretimVerisi
from app.services.isg_risk_puani import isg_risk_puani
from decimal import Decimal

def test_oee_hesaplama():
    """OEE hesaplama formülünün farklı durumlar için testi."""
    # Durum 1: İdeal durum
    uretim = UretimVerisi(planlanan_sure_dk=480, gercek_calisma_dk=480, gercek_uretim=1600, hatali_uretim=0)
    oee = uretim.hesapla_oee(200) # 200/saat -> 8 saatte 1600 adet
    assert oee == 100.0

    # Durum 2: Normal üretim
    uretim2 = UretimVerisi(planlanan_sure_dk=480, gercek_calisma_dk=400, gercek_uretim=1000, hatali_uretim=50)
    oee2 = uretim2.hesapla_oee(200)
    assert 59.0 <= oee2 <= 60.0

    # Durum 3: Sıfır çalışma süresi
    uretim3 = UretimVerisi(planlanan_sure_dk=480, gercek_calisma_dk=0, gercek_uretim=0, hatali_uretim=0)
    oee3 = uretim3.hesapla_oee(200)
    assert oee3 == 0.0

def test_isg_risk_puani():
    """İSG risk puanı ve seviyesi hesaplama testi."""
    sonuc = isg_risk_puani.hesapla(3, 4) # 12 -> ORTA
    assert sonuc['puan'] == 12
    assert sonuc['seviye'] == 'orta'

    sonuc = isg_risk_puani.hesapla(5, 5) # 25 -> KRİTİK
    assert sonuc['puan'] == 25
    assert sonuc['seviye'] == 'kritik'

    sonuc = isg_risk_puani.hesapla(1, 2) # 2 -> DÜŞÜK
    assert sonuc['puan'] == 2
    assert sonuc['seviye'] == 'dusuk'
