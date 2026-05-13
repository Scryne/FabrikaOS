import pytest
from app import create_app
from app.extensions import db
from app.models.kullanici import Kullanici

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_ana_sayfa_yonlendirme(client):
    """Giriş yapmamış kullanıcı login sayfasına yönlendirilmeli."""
    response = client.get('/')
    assert response.status_code == 302
    assert '/auth/login' in response.location

def test_login_sayfasi_erisim(client):
    """Login sayfası başarıyla açılmalı."""
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'FDYS' in response.data
