import pytest
from app.models.crm import Ortak, Firma, FirmaYetkilisi, CrmIletisimGecmisi
from app.services import crm_servisi

def test_ortak_model_creation(app, test_db):
    """Ortak modelinin doğru şekilde oluşturulup kaydedildiğini test et."""
    with app.app_context():
        ortak = Ortak(
            ortak_no="ORT-TEST",
            ad_soyad="Test Ortak",
            tc_kimlik="12345678901",
            ortak_tipi="malik"
        )
        test_db.add(ortak)
        test_db.commit()

        kayit = Ortak.query.filter_by(ortak_no="ORT-TEST").first()
        assert kayit is not None
        assert kayit.ad_soyad == "Test Ortak"
        assert kayit.ortak_tipi_adi == "Malik"
        assert kayit.baslangic_harfler == "TO"


def test_firma_model_creation(app, test_db):
    """Firma modelinin ve yetkilisinin doğru oluşturulduğunu test et."""
    with app.app_context():
        firma = Firma(
            firma_no="FRM-TEST",
            unvan="Test Bilişim A.Ş.",
            sektor="bilisim"
        )
        test_db.add(firma)
        test_db.commit()

        kayit = Firma.query.filter_by(firma_no="FRM-TEST").first()
        assert kayit is not None
        assert kayit.sektor_adi == "Bilişim"

        yetkili = FirmaYetkilisi(
            firma_id=kayit.id,
            ad_soyad="Ali Veli",
            gorev="Müdür"
        )
        test_db.add(yetkili)
        test_db.commit()

        assert kayit.yetkililer.count() == 1
        assert kayit.yetkililer.first().ad_soyad == "Ali Veli"


def test_iletisim_gecmisi(app, test_db):
    """Ortak ve firma için iletişim geçmişi eklenebildiğini test et."""
    with app.app_context():
        # Fake ortak ve firma
        ortak = Ortak(ortak_no="ORT-IL", ad_soyad="İletişim Ortak")
        firma = Firma(firma_no="FRM-IL", unvan="İletişim Firma")
        test_db.add_all([ortak, firma])
        test_db.commit()

        iletisim_ortak = CrmIletisimGecmisi(
            ilgili_tip='ortak',
            ilgili_id=ortak.id,
            iletisim_turu='telefon',
            konu='Aidat Hatırlatması'
        )
        iletisim_firma = CrmIletisimGecmisi(
            ilgili_tip='firma',
            ilgili_id=firma.id,
            iletisim_turu='eposta',
            konu='Sözleşme Yenileme'
        )
        test_db.add_all([iletisim_ortak, iletisim_firma])
        test_db.commit()

        assert ortak.iletisim_gecmisi.count() == 1
        assert firma.iletisim_gecmisi.count() == 1
        assert ortak.iletisim_gecmisi.first().iletisim_turu_adi == "Telefon"


def test_crm_arama_servisi(app, test_db):
    """Arama motorunun ortak ve firmaları doğru getirdiğini test et."""
    with app.app_context():
        ortak = Ortak(ortak_no="ORT-SRC", ad_soyad="BenzersizArama Ortak")
        firma = Firma(firma_no="FRM-SRC", unvan="BenzersizArama Firma")
        test_db.add_all([ortak, firma])
        test_db.commit()

        sonuclar = crm_servisi.crm_arama("BenzersizArama")
        assert len(sonuclar['ortaklar']) == 1
        assert len(sonuclar['firmalar']) == 1
        assert sonuclar['ortaklar'][0].ad_soyad == "BenzersizArama Ortak"


def test_crm_routes(client, auth):
    """CRM rotalarına erişimi test et."""
    auth.login()
    
    # Dashboard
    response = client.get('/crm/')
    assert response.status_code == 200
    assert b'CRM Merkezi' in response.data

    # Ortaklar listesi
    response = client.get('/crm/ortaklar')
    assert response.status_code == 200
    
    # Firmalar listesi
    response = client.get('/crm/firmalar')
    assert response.status_code == 200

    # Harita
    response = client.get('/crm/harita')
    assert response.status_code == 200
    
    # Arşiv (Placeholder)
    response = client.get('/crm/arsiv')
    assert response.status_code == 200
