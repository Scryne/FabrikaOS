import pytest
from app.models.crm import Ortak, Firma

def test_site_harita_index_access(client, yonetici_user):
    """Sanayi haritası sayfasına erişim testi."""
    client.post('/auth/login', data={
        'kullanici_adi': 'yonetici_test',
        'sifre': 'admin123'
    })
    
    response = client.get('/sanayi-harita/')
    assert response.status_code == 200
    assert b'Sanayi Sitesi Haritas' in response.data

def test_site_harita_api_veriler(client, yonetici_user, test_db):
    """Harita API'sinden veri çekme testi."""
    client.post('/auth/login', data={
        'kullanici_adi': 'yonetici_test',
        'sifre': 'admin123'
    })
    
    # Test için dummy ortak ekleyelim
    ortak = Ortak(ortak_no='TEST-01', ad_soyad='Harita Ortak', harita_enlem=41.0, harita_boylam=29.0)
    test_db.add(ortak)
    test_db.commit()
    
    response = client.get('/sanayi-harita/api/veriler')
    assert response.status_code == 200
    data = response.get_json()
    assert 'ortaklar' in data
    assert 'firmalar' in data
    assert 'talepler' in data
    
    assert len(data['ortaklar']) >= 1
    assert data['ortaklar'][-1]['lat'] == 41.0
    assert data['ortaklar'][-1]['lng'] == 29.0
    
def test_koordinat_guncelleme_yetki(client, operator_user, test_db):
    """Operatör kullanıcısının koordinat güncelleyememesi."""
    client.post('/auth/login', data={
        'kullanici_adi': 'op_test',
        'sifre': 'op123'
    })
    
    ortak = Ortak(ortak_no='TEST-02', ad_soyad='Test 2')
    test_db.add(ortak)
    test_db.commit()
    
    response = client.post('/sanayi-harita/api/koordinat-guncelle', json={
        'tip': 'ortak',
        'id': ortak.id,
        'lat': 41.1,
        'lng': 29.1
    })
    
    # Operatör olduğu için yetkisiz
    assert response.status_code == 403
    
def test_koordinat_guncelleme(client, yonetici_user, test_db):
    """Yöneticinin koordinat güncelleyebilmesi."""
    client.post('/auth/login', data={
        'kullanici_adi': 'yonetici_test',
        'sifre': 'admin123'
    })
    
    ortak = Ortak(ortak_no='TEST-03', ad_soyad='Test 3')
    test_db.add(ortak)
    test_db.commit()
    
    response = client.post('/sanayi-harita/api/koordinat-guncelle', json={
        'tip': 'ortak',
        'id': ortak.id,
        'lat': 41.2,
        'lng': 29.2
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    
    # Veritabanında kontrol
    o = test_db.get(Ortak, ortak.id)
    assert o.harita_enlem == 41.2
    assert o.harita_boylam == 29.2
