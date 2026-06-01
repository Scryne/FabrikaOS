"""
FabrikaOS — Satın Alma Modülü Testleri
"""
import pytest
from datetime import datetime, timezone
from app.models.satin_alma import SatinAlmaTalebi, SatinAlmaSiparis, TeklifKarsilastirma
from app.models.kullanici import Kullanici
from app.services.satin_alma_servisi import (
    talep_olustur, talep_onayla, talep_reddet, talep_iptal,
    siparis_olustur, siparis_teslim_al, teklif_ekle, teklif_sec
)
from decimal import Decimal

@pytest.fixture
def test_kullanici(session, temel_veriler):
    return Kullanici.query.get(temel_veriler['kullanici_id'])

def test_talep_olustur(app_context, session, test_kullanici):
    """Talep oluşturma servisi testi"""
    talep = talep_olustur(
        test_kullanici,
        kalem_adi='Test Kalem',
        miktar=10,
        birim='adet',
        aciliyet='normal'
    )
    assert talep.id is not None
    assert talep.durum == 'bekliyor'
    assert talep.kalem_adi == 'Test Kalem'
    assert talep.miktar == 10
    assert talep.talep_eden_id == test_kullanici.id
    assert talep.talep_no.startswith('SA-')

def test_talep_onayla(app_context, session, test_kullanici):
    """Talep onaylama testi"""
    talep = talep_olustur(test_kullanici, kalem_adi='Test Kalem', miktar=5)
    
    onayli_talep, err = talep_onayla(talep.id, test_kullanici)
    
    assert err is None
    assert onayli_talep.durum == 'onaylandi'
    assert onayli_talep.onaylayan_id == test_kullanici.id

def test_talep_reddet(app_context, session, test_kullanici):
    """Talep reddetme testi"""
    talep = talep_olustur(test_kullanici, kalem_adi='Test Kalem')
    
    red_talep, err = talep_reddet(talep.id, test_kullanici, 'Bütçe yetersiz')
    
    assert err is None
    assert red_talep.durum == 'reddedildi'
    assert red_talep.red_nedeni == 'Bütçe yetersiz'

def test_teklif_ekle_ve_sec(app_context, session, test_kullanici):
    """Teklif ekleme ve seçme testi"""
    talep = talep_olustur(test_kullanici, kalem_adi='Test')
    talep_onayla(talep.id, test_kullanici)
    
    # 2 Teklif ekle
    teklif1, _ = teklif_ekle(talep.id, birim_fiyat=Decimal('100.00'), toplam_fiyat=Decimal('100.00'))
    teklif2, _ = teklif_ekle(talep.id, birim_fiyat=Decimal('120.00'), toplam_fiyat=Decimal('120.00'))
    
    assert talep.teklif_sayisi == 2
    
    # 2. teklifi seç
    secilen, _ = teklif_sec(teklif2.id)
    assert secilen.secildi_mi is True
    
    # 1. teklif seçili olmamalı
    session.refresh(teklif1)
    assert teklif1.secildi_mi is False

def test_siparis_olustur(app_context, session, test_kullanici):
    """Sipariş oluşturma testi"""
    talep = talep_olustur(test_kullanici, kalem_adi='Test')
    talep_onayla(talep.id, test_kullanici)
    
    siparis, err = siparis_olustur(
        talep.id, test_kullanici,
        birim_fiyat=Decimal('50.00'),
        miktar=Decimal('2'),
        kdv_orani=Decimal('20.00')
    )
    
    assert err is None
    assert siparis.durum == 'siparis_verildi'
    assert siparis.toplam_tutar == Decimal('100.00')
    assert siparis.genel_toplam == Decimal('120.00')
    
    # Talep durumu güncellenmiş olmalı
    session.refresh(talep)
    assert talep.durum == 'siparis_verildi'

def test_siparis_teslim_al(app_context, session, test_kullanici):
    """Sipariş teslim alma testi"""
    talep = talep_olustur(test_kullanici, kalem_adi='Test')
    talep_onayla(talep.id, test_kullanici)
    siparis, _ = siparis_olustur(talep.id, test_kullanici, birim_fiyat=Decimal('50.00'))
    
    teslim, err = siparis_teslim_al(
        siparis.id, test_kullanici,
        gercek_teslim=datetime.now(timezone.utc).date()
    )
    
    assert err is None
    assert teslim.durum == 'teslim_alindi'
    assert teslim.teslim_alan_id == test_kullanici.id
    
    # Talep durumu güncellenmiş olmalı
    session.refresh(talep)
    assert talep.durum == 'teslim_alindi'
