"""
FDYS — İSG Genişletme (Faz 5) Testleri
SaglikMuayenesi ve IsgDokumani modelleri ile ilgili
route ve servis işlevselliğini test eder.
"""

import pytest
from datetime import date, timedelta
from app.extensions import db
from app.models.isg import SaglikMuayenesi, IsgDokumani
from app.models.personel import Calisan
from app.services.isg_hatirlatici import tum_hatirlatmalar

@pytest.fixture
def mock_calisan(app_context):
    calisan = Calisan.query.filter_by(sicil_no="TEST-002").first()
    if not calisan:
        calisan = Calisan(
            sicil_no="TEST-002",
            ad_soyad="Test Çalışan İSG",
            departman="Üretim",
            pozisyon="Operatör",
            ise_baslama=date(2020, 1, 1),
            aktif=True
        )
        db.session.add(calisan)
        db.session.commit()
    return calisan

def test_muayene_model_olusturma(app_context, mock_calisan):
    """Sağlık muayenesi modelinin temel işlevleri."""
    bugun = date.today()
    sonraki = bugun + timedelta(days=365)
    
    muayene = SaglikMuayenesi(
        calisan_id=mock_calisan.id,
        muayene_turu=SaglikMuayenesi.TUR_PERIYODIK,
        muayene_tarihi=bugun,
        sonraki_muayene_tarihi=sonraki,
        sonuc=SaglikMuayenesi.SONUC_UYGUN,
        hastane_adi="Test Hastanesi"
    )
    db.session.add(muayene)
    db.session.commit()
    
    assert muayene.id is not None
    assert muayene.calisan.ad_soyad == "Test Çalışan İSG"
    assert muayene.tur_adi == "Periyodik Muayene"
    assert muayene.sonuc_adi == "Uygun"
    assert muayene.muayene_gecikti_mi is False
    assert muayene.muayene_yaklasıyor_mu is False

def test_muayene_gecikme_durumu(app_context, mock_calisan):
    """Gecikmiş muayenelerin doğru tespit edilmesi."""
    gecmis_tarih = date.today() - timedelta(days=10)
    
    muayene = SaglikMuayenesi(
        calisan_id=mock_calisan.id,
        muayene_turu=SaglikMuayenesi.TUR_PERIYODIK,
        muayene_tarihi=gecmis_tarih - timedelta(days=365),
        sonraki_muayene_tarihi=gecmis_tarih,
        sonuc=SaglikMuayenesi.SONUC_UYGUN
    )
    db.session.add(muayene)
    db.session.commit()
    
    assert muayene.muayene_gecikti_mi is True

def test_dokuman_model_olusturma(app_context, test_user):
    """İSG Doküman modelinin temel işlevleri."""
    dokuman = IsgDokumani(
        baslik="Test Acil Durum Planı",
        kategori=IsgDokumani.KAT_PROSEDUR,
        versiyon=1,
        sorumlu_id=test_user.id
    )
    db.session.add(dokuman)
    db.session.commit()
    
    assert dokuman.id is not None
    assert dokuman.kategori_adi == "Prosedür"
    assert dokuman.onay_durumu == IsgDokumani.ONAY_TASLAK
    assert dokuman.gecerliligi_doldu_mu is False

def test_dokuman_onay_islemi(app_context, test_user):
    """Doküman onayı verildiğinde durumun güncellenmesi."""
    dokuman = IsgDokumani(
        baslik="Test Talimat",
        kategori=IsgDokumani.KAT_TALIMAT,
        onay_durumu=IsgDokumani.ONAY_BEKLIYOR
    )
    db.session.add(dokuman)
    db.session.commit()
    
    dokuman.onay_durumu = IsgDokumani.ONAY_ONAYLANDI
    dokuman.onaylayan_id = test_user.id
    db.session.commit()
    
    assert dokuman.onay_durumu == "onaylandi"
    assert dokuman.onaylayan_id == test_user.id

def test_isg_hatirlatici_servisi(app_context, mock_calisan):
    """İSG Hatırlatıcı servisinin uyarıları doğru toplaması."""
    # Gecikmiş muayene ekle
    m = SaglikMuayenesi(
        calisan_id=mock_calisan.id,
        muayene_tarihi=date.today() - timedelta(days=400),
        sonraki_muayene_tarihi=date.today() - timedelta(days=35),
    )
    db.session.add(m)
    
    # Süresi dolan doküman ekle
    d = IsgDokumani(
        baslik="Test Doküman",
        gecerlilik_tarihi=date.today() - timedelta(days=5),
        onay_durumu='onaylandi'
    )
    db.session.add(d)
    db.session.commit()
    
    hatirlatmalar = tum_hatirlatmalar()
    
    assert 'muayene' in hatirlatmalar
    assert 'dokuman' in hatirlatmalar
    assert hatirlatmalar['toplam_uyari'] > 0
    
    muayene_geciken = hatirlatmalar['muayene']['geciken']
    assert len(muayene_geciken) >= 1
    assert muayene_geciken[0]['muayene'].id == m.id
    
    dokuman_geciken = hatirlatmalar['dokuman']['geciken']
    assert len(dokuman_geciken) >= 1
    assert dokuman_geciken[0]['dokuman'].id == d.id

def test_saglik_muayeneleri_route(client, auth):
    """Sağlık muayeneleri listesi endpoint erişimi."""
    auth.login()
    response = client.get('/isg/saglik-muayeneleri')
    assert response.status_code == 200

def test_isg_dokumanlar_route(client, auth):
    """İSG Dokümanları listesi endpoint erişimi."""
    auth.login()
    response = client.get('/isg/dokumanlar')
    assert response.status_code == 200

def test_isg_hatirlatmalar_route(client, auth):
    """İSG Hatırlatmalar dashboard endpoint erişimi."""
    auth.login()
    response = client.get('/isg/hatirlatmalar')
    assert response.status_code == 200
