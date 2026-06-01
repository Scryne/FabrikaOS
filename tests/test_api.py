import pytest
from flask_jwt_extended import decode_token
from app.models.crm import Ortak

def test_api_auth_login(client, yonetici_user):
    """API login endpoint testi."""
    response = client.post('/api/v1/auth/login', json={
        'kullanici_adi': 'yonetici_test',
        'sifre': 'admin123'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'access_token' in data['data']
    assert 'refresh_token' in data['data']
    assert data['data']['kullanici']['kullanici_adi'] == 'yonetici_test'

def test_api_auth_login_fail(client, yonetici_user):
    """API hatalı şifre testi."""
    response = client.post('/api/v1/auth/login', json={
        'kullanici_adi': 'yonetici_test',
        'sifre': 'YanlisSifre'
    })
    assert response.status_code == 401

def test_api_me(client, yonetici_user):
    """/auth/me endpointi."""
    res1 = client.post('/api/v1/auth/login', json={'kullanici_adi': 'yonetici_test', 'sifre': 'admin123'})
    token = res1.get_json()['data']['access_token']
    
    response = client.get('/api/v1/auth/me', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['data']['kullanici_adi'] == 'yonetici_test'

def test_api_ortaklar_listele(client, yonetici_user, test_db):
    """Ortaklar listesini JWT ile çekme."""
    res1 = client.post('/api/v1/auth/login', json={'kullanici_adi': 'yonetici_test', 'sifre': 'admin123'})
    token = res1.get_json()['data']['access_token']
    
    # Ortak ekle
    o1 = Ortak(ortak_no='API-01', ad_soyad='API Test Ortak 1')
    test_db.add(o1)
    test_db.commit()
    
    response = client.get('/api/v1/ortaklar', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert isinstance(data['data'], list)
    assert len(data['data']) >= 1
    
def test_api_ortak_ekle(client, yonetici_user):
    """API üzerinden yeni ortak oluşturma."""
    res1 = client.post('/api/v1/auth/login', json={'kullanici_adi': 'yonetici_test', 'sifre': 'admin123'})
    token = res1.get_json()['data']['access_token']
    
    payload = {
        'ad_soyad': 'API Yeni Ortak',
        'ortak_no': 'API-99'
    }
    
    response = client.post('/api/v1/ortaklar', json=payload, headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 201
    data = response.get_json()
    assert data['data']['ad_soyad'] == 'API Yeni Ortak'
