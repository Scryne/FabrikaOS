"""
FDYS — Sözleşme Modülü Testleri
Faz 3
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from app.models.sozlesme import Sozlesme, KiraKontrat, SigortaPolice, StandartMetin
from app.services import sozlesme_servisi

def test_sozlesme_kalan_gun_ve_durum(app_context, session):
    """Sözleşme kalan gün hesaplaması ve durum özellikleri test edilir."""
    bugun = date.today()
    
    s = Sozlesme(
        sozlesme_no="TEST-001",
        baslik="Test Sözleşmesi",
        taraf_tip="ortak",
        taraf_id=1,
        baslangic_tarihi=bugun - timedelta(days=10),
        bitis_tarihi=bugun + timedelta(days=20),
        hatirlatma_gun=30
    )
    session.add(s)
    session.commit()
    
    assert s.kalan_gun == 20
    assert s.suresi_dolmak_uzere == True
    assert s.suresi_doldu == False

def test_kira_artisi_hesaplama(app_context, session):
    """Kira artışı hesaplama servisi test edilir."""
    s = Sozlesme(
        sozlesme_no="KIRA-001",
        baslik="Kira Sözleşmesi",
        taraf_tip="ortak",
        taraf_id=1,
        baslangic_tarihi=date.today(),
        tutar=Decimal('10000.00'),
        tur='kira'
    )
    session.add(s)
    session.flush()
    
    k = KiraKontrat(
        sozlesme_id=s.id,
        kira_tutari=Decimal('10000.00'),
        artis_turu='sabit_yuzde',
        artis_orani=Decimal('25.00')
    )
    session.add(k)
    session.commit()
    
    # Hesaplama yapalım (uygulamadan)
    hesaplama = sozlesme_servisi.kira_artisi_hesapla(k.id)
    assert hesaplama is not None
    assert hesaplama['yeni_kira'] == 12500.0
    assert hesaplama['artis_tutari'] == 2500.0

def test_standart_metin_doldur(app_context, session):
    """Standart metin değişken değiştirme servisi test edilir."""
    m = StandartMetin(
        baslik="Test",
        tur="genel",
        icerik="Merhaba {isim}, kira tutarınız {tutar} TL'dir."
    )
    session.add(m)
    session.commit()
    
    degiskenler = {
        '{isim}': 'Ahmet Yılmaz',
        '{tutar}': '15.000'
    }
    
    doldurulmus = sozlesme_servisi.standart_metin_doldur(m.id, degiskenler)
    assert doldurulmus == "Merhaba Ahmet Yılmaz, kira tutarınız 15.000 TL'dir."

def test_hatirlatma_sistemi(app_context, session):
    """Yaklaşan sözleşme ve poliçelerin tespit edilmesi test edilir."""
    bugun = date.today()
    
    # 1. 20 gün kalmış sözleşme (hatırlatma gününe girmeli, 30 gün default)
    s1 = Sozlesme(
        sozlesme_no="HAT-001",
        baslik="S1",
        taraf_tip="ortak",
        taraf_id=1,
        baslangic_tarihi=bugun - timedelta(days=100),
        bitis_tarihi=bugun + timedelta(days=20),
        hatirlatma_gun=30
    )
    
    # 2. 60 gün kalmış sözleşme (girmemeli)
    s2 = Sozlesme(
        sozlesme_no="HAT-002",
        baslik="S2",
        taraf_tip="ortak",
        taraf_id=1,
        baslangic_tarihi=bugun - timedelta(days=100),
        bitis_tarihi=bugun + timedelta(days=60),
        hatirlatma_gun=30
    )
    
    session.add_all([s1, s2])
    session.commit()
    
    veri = sozlesme_servisi.hatirlatma_kontrol()
    
    assert len(veri['sozlesmeler']) >= 1
    
    bulunan_idler = [x['sozlesme'].id for x in veri['sozlesmeler']]
    assert s1.id in bulunan_idler
    assert s2.id not in bulunan_idler
