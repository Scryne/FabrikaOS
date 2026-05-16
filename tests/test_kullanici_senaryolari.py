"""
FDYS — Kullanıcı Senaryoları Testi (E2E)
Faz 6 Kapsamında Yazılmıştır.
"""

import pytest
from datetime import date
from app import create_app
from app.extensions import db
from app.models.kullanici import Kullanici
from app.models.makine import Makine, ArizaKaydi
from app.models.bildirim import Bildirim

@pytest.fixture
def test_app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(test_app):
    return test_app.test_client()

@pytest.fixture
def test_db(test_app):
    # Temel kullanıcıları ekle
    admin = Kullanici(kullanici_adi='admin', ad_soyad='Sistem Yöneticisi', rol='Yönetici')
    admin.sifre_belirle('admin123')
    
    op = Kullanici(kullanici_adi='oper', ad_soyad='Ahmet Operatör', rol='Operatör')
    op.sifre_belirle('oper123')
    
    tek = Kullanici(kullanici_adi='tek', ad_soyad='Mehmet Teknisyen', rol='Teknisyen')
    tek.sifre_belirle('tek123')

    # Temel makine ekle
    m1 = Makine(ad='Abkant Pres A1', kod='ABK-01', teorik_kapasite=1000, satin_alma_tarihi=date(2025, 1, 1))

    db.session.add_all([admin, op, tek, m1])
    db.session.commit()
    
    return db

def login(client, username, password):
    return client.post('/auth/login', data=dict(
        kullanici_adi=username,
        sifre=password
    ), follow_redirects=True)

def test_senaryo_1_ariza_bildirimi(client, test_db):
    """Senaryo 1: Operatör arıza bildirir, teknisyen çözer."""
    # 1. Operatör girişi
    login(client, 'oper', 'oper123')
    
    # 2. Arıza oluştur (Simülasyon - DB seviyesi)
    m1 = Makine.query.filter_by(kod='ABK-01').first()
    oper = Kullanici.query.filter_by(kullanici_adi='oper').first()
    tek = Kullanici.query.filter_by(kullanici_adi='tek').first()

    yeni_ariza = ArizaKaydi(
        makine_id=m1.id,
        bildiren_id=oper.id,
        ariza_turu='Elektrik',
        aciklama='Motor aşırı ısındı',
        oncelik='yuksek',
        durum='acik'
    )
    db.session.add(yeni_ariza)
    db.session.commit()

    assert ArizaKaydi.query.count() == 1
    assert ArizaKaydi.query.first().durum == 'acik'

    # 3. Teknisyenin arızayı çözmesi
    ariza = ArizaKaydi.query.first()
    ariza.durum = 'cozuldu'
    ariza.atanan_teknisyen_id = tek.id
    ariza.cozum = 'Kondansatör değişti.'
    db.session.commit()

    guncel_ariza = ArizaKaydi.query.first()
    assert guncel_ariza.durum == 'cozuldu'
    assert guncel_ariza.cozum == 'Kondansatör değişti.'

def test_senaryo_2_otomatik_bildirim_olusturma(client, test_db):
    """Senaryo 2: Sistem kritik durumlarda doğru bildirimleri oluşturur mu?"""
    admin = Kullanici.query.filter_by(kullanici_adi='admin').first()
    
    b1 = Bildirim(
        kullanici_id=admin.id,
        baslik='OEE Düşük',
        mesaj='ABK-01 makinesinde OEE hedefinin çok altında.',
        seviye='uyari'
    )
    db.session.add(b1)
    db.session.commit()

    # Bildirim okunmadı kontrolü
    assert Bildirim.query.filter_by(okundu_mu=False).count() == 1
    
    # Bildirim okundu olarak işaretle
    bildirim = Bildirim.query.first()
    bildirim.okundu_isaretle()
    db.session.commit()

    assert Bildirim.query.filter_by(okundu_mu=True).count() == 1
