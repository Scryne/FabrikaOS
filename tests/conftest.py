import pytest
from datetime import datetime, timezone
from app import create_app
from app.extensions import db, bcrypt
from app.models.kullanici import Kullanici
from app.models.personel import Calisan
from app.models.makine import Makine

@pytest.fixture(scope='session')
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.drop_all()

@pytest.fixture(scope='function', autouse=True)
def app_context(app):
    with app.app_context():
        yield

@pytest.fixture(scope='function')
def session(app):
    db.session.begin_nested()
    yield db.session
    db.session.rollback()

@pytest.fixture
def client(app, session):
    return app.test_client()

@pytest.fixture
def auth_client_yonetici(client, session):
    user = Kullanici.query.filter_by(kullanici_adi='yonetici_test').first()
    if not user:
        hashed = bcrypt.generate_password_hash('admin123').decode('utf-8')
        user = Kullanici(ad_soyad='Yönetici Test', kullanici_adi='yonetici_test', sifre_hash=hashed, rol='yonetici')
        session.add(user)
        session.commit()
    client.post('/auth/login', data={'kullanici_adi': 'yonetici_test', 'sifre': 'admin123'})
    return client

@pytest.fixture
def auth_client_operator(client, session):
    client.delete_cookie('session')
    user = Kullanici.query.filter_by(kullanici_adi='op_test').first()
    if not user:
        hashed = bcrypt.generate_password_hash('op123').decode('utf-8')
        user = Kullanici(ad_soyad='Operator Test', kullanici_adi='op_test', sifre_hash=hashed, rol='operator', modul_erisim={'makine': True, 'personel': True})
        session.add(user)
        session.commit()
    client.post('/auth/login', data={'kullanici_adi': 'op_test', 'sifre': 'op123'})
    return client

@pytest.fixture
def auth_client_teknisyen(client, session):
    client.delete_cookie('session')
    user = Kullanici.query.filter_by(kullanici_adi='tech_test').first()
    if not user:
        hashed = bcrypt.generate_password_hash('tech123').decode('utf-8')
        user = Kullanici(ad_soyad='Teknisyen Test', kullanici_adi='tech_test', sifre_hash=hashed, rol='teknisyen', modul_erisim={'makine': True})
        session.add(user)
        session.commit()
    client.post('/auth/login', data={'kullanici_adi': 'tech_test', 'sifre': 'tech123'})
    return client

@pytest.fixture
def temel_veriler(session):
    u1 = Kullanici.query.filter_by(kullanici_adi='sistem').first()
    if not u1:
        u1 = Kullanici(ad_soyad='Sistem', kullanici_adi='sistem', sifre_hash='dummy', rol='yonetici')
        session.add(u1)
        session.commit()

    c1 = Calisan.query.filter_by(sicil_no='1001').first()
    m1 = Makine.query.filter_by(kod='M-01').first()
    
    if not c1:
        c1 = Calisan(sicil_no='1001', ad_soyad='Ali Yılmaz', departman='Üretim', pozisyon='Operatör', ise_baslama=datetime.now(timezone.utc).date(), kullanici_id=u1.id)
        session.add(c1)
    if not m1:
        m1 = Makine(kod='M-01', ad='CNC Torna', durum='aktif', teorik_kapasite=200, hedef_oee=85.0, satin_alma_tarihi=datetime.now(timezone.utc).date())
        session.add(m1)
        
    session.commit()
    return {'calisan_id': c1.id, 'makine_id': m1.id, 'kullanici_id': u1.id}

@pytest.fixture
def sample_data(session):
    """AI ve analitik testleri için örnek veri seti."""
    u1 = Kullanici.query.filter_by(kullanici_adi='sistem').first()
    if not u1:
        u1 = Kullanici(ad_soyad='Sistem', kullanici_adi='sistem', sifre_hash='dummy', rol='yonetici')
        session.add(u1)
        session.commit()

    m1 = Makine.query.filter_by(kod='M-TEST-01').first()
    if not m1:
        m1 = Makine(
            kod='M-TEST-01', ad='Test CNC', durum='aktif',
            teorik_kapasite=200, hedef_oee=85.0,
            satin_alma_tarihi=datetime(2024, 1, 1, tzinfo=timezone.utc).date(),
            satin_alma_fiyati=100000, periyodik_bakim_gun=90,
        )
        session.add(m1)
        session.commit()

    return {'makine': m1, 'kullanici': u1}

@pytest.fixture
def test_user(session):
    user = Kullanici.query.filter_by(kullanici_adi='test_user').first()
    if not user:
        hashed = bcrypt.generate_password_hash('test1234').decode('utf-8')
        user = Kullanici(ad_soyad='Test User', kullanici_adi='test_user', sifre_hash=hashed, rol='teknisyen')
        session.add(user)
        session.commit()
    return user

@pytest.fixture
def yonetici_user(session):
    user = Kullanici.query.filter_by(kullanici_adi='yonetici_test').first()
    if not user:
        hashed = bcrypt.generate_password_hash('admin123').decode('utf-8')
        user = Kullanici(ad_soyad='Yönetici Test', kullanici_adi='yonetici_test', sifre_hash=hashed, rol='yonetici')
        session.add(user)
        session.commit()
    return user

@pytest.fixture
def operator_user(session):
    user = Kullanici.query.filter_by(kullanici_adi='op_test').first()
    if not user:
        hashed = bcrypt.generate_password_hash('op123').decode('utf-8')
        user = Kullanici(ad_soyad='Operator Test', kullanici_adi='op_test', sifre_hash=hashed, rol='operator')
        session.add(user)
        session.commit()
    return user

@pytest.fixture
def test_db(session):
    return session

class AuthActions:
    def __init__(self, client):
        self._client = client

    def login(self, username='yonetici_test', password='admin123'):
        return self._client.post(
            '/auth/login',
            data={'kullanici_adi': username, 'sifre': password}
        )

    def logout(self):
        return self._client.get('/auth/logout')

@pytest.fixture
def auth(client, yonetici_user):
    return AuthActions(client)
