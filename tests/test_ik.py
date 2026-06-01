"""
FDYS — İK Modülü Testleri
Faz 1 — İnsan Kaynakları Tam Genişletme Testleri
"""

import pytest
from datetime import date, datetime, timedelta, timezone
from app.models.personel import Calisan
from app.models.ik import (
    SavunmaTutanak, FazlaMesai, SertifikaTakip,
    MaasSkalasi, ZimmetKaydi, GirisCikisEvrak
)
from app.services.ik_servisi import (
    izin_bakiye_hesapla, kidem_hesapla, fazla_mesai_ozeti,
    sertifika_hatirlatma_kontrol
)

def test_kidem_hesapla(app, session):
    """Kıdem hesaplama testi."""
    with app.app_context():
        # 3 yıl önce işe başlamış çalışan
        bugun = date.today()
        ise_baslama = bugun - timedelta(days=3 * 365 + 10)
        
        calisan = Calisan(
            ad_soyad="Test Kıdemli",
            sicil_no="TK-001",
            departman="Üretim",
            pozisyon="Operatör",
            ise_baslama=ise_baslama
        )
        session.add(calisan)
        session.commit()

        kidem = kidem_hesapla(calisan.id)
        assert kidem == 3

        # İşten ayrılmış çalışan kıdemi
        calisan.isten_ayrilma = ise_baslama + timedelta(days=365)
        session.commit()
        kidem2 = kidem_hesapla(calisan.id)
        assert kidem2 == 1


def test_izin_bakiye_hesapla(app, session):
    """Yıllık izin bakiye hesaplama mantığı testi."""
    with app.app_context():
        # 6 yıllık çalışan (Hak: 20 gün)
        bugun = date.today()
        ise_baslama = bugun - timedelta(days=6 * 365 + 5)
        
        calisan = Calisan(
            ad_soyad="Test İzin",
            sicil_no="TI-001",
            departman="İK",
            pozisyon="Uzman",
            ise_baslama=ise_baslama
        )
        session.add(calisan)
        session.commit()

        bakiye = izin_bakiye_hesapla(calisan.id, bugun.year)
        assert bakiye['yillik']['hak'] == 20
        assert bakiye['yillik']['kullanilan'] == 0
        assert bakiye['yillik']['kalan'] == 20


def test_fazla_mesai_hesaplama(app, session):
    """Fazla mesai saat hesaplama ve onay testi."""
    with app.app_context():
        calisan = Calisan(
            ad_soyad="Test Mesai",
            sicil_no="TM-001",
            departman="Bakım",
            pozisyon="Teknisyen",
            ise_baslama=date.today()
        )
        session.add(calisan)
        session.commit()

        from datetime import time
        mesai = FazlaMesai(
            calisan_id=calisan.id,
            tarih=date.today(),
            baslangic_saati=time(18, 0),
            bitis_saati=time(21, 30),
            mesai_turu='hafta_ici'
        )
        mesai.hesapla_toplam_saat()
        mesai.varsayilan_carpan_belirle()
        
        session.add(mesai)
        session.flush()

        assert mesai.toplam_saat == 3.5
        assert mesai.ucret_carpani == 1.5
        assert mesai.onay_durumu == 'bekliyor'


def test_sertifika_hatirlatma(app, session):
    """Sertifika geçerlilik tarihi kontrol testi."""
    with app.app_context():
        calisan = Calisan(
            ad_soyad="Test Sertifika",
            sicil_no="TS-001",
            departman="Kalite",
            pozisyon="Mühendis",
            ise_baslama=date.today()
        )
        session.add(calisan)
        session.commit()

        bugun = date.today()
        
        # 10 gün sonra bitecek sertifika (hatırlatma süresi 30 gün)
        sertifika1 = SertifikaTakip(
            calisan_id=calisan.id,
            sertifika_adi="ISO 9001 İç Denetçi",
            veren_kurum="TSE",
            verilis_tarihi=bugun - timedelta(days=300),
            gecerlilik_bitis=bugun + timedelta(days=10),
            hatirlatma_gun=30,
            durum='gecerli'
        )
        
        # 50 gün sonra bitecek sertifika
        sertifika2 = SertifikaTakip(
            calisan_id=calisan.id,
            sertifika_adi="İlkyardım",
            veren_kurum="Kızılay",
            verilis_tarihi=bugun - timedelta(days=300),
            gecerlilik_bitis=bugun + timedelta(days=50),
            hatirlatma_gun=30,
            durum='gecerli'
        )
        
        session.add_all([sertifika1, sertifika2])
        session.commit()

        yaklasanlar = sertifika_hatirlatma_kontrol()
        
        assert len(yaklasanlar) == 1
        assert yaklasanlar[0]['sertifika'].id == sertifika1.id
        assert yaklasanlar[0]['kalan_gun'] == 10


def test_giris_cikis_evrak_olusturma(app, session):
    """Standart işe giriş evraklarının oluşturulması testi."""
    with app.app_context():
        calisan = Calisan(
            ad_soyad="Test Evrak",
            sicil_no="TE-001",
            departman="Lojistik",
            pozisyon="Depocu",
            ise_baslama=date.today()
        )
        session.add(calisan)
        session.commit()

        # Evrakları oluştur
        evraklar = GirisCikisEvrak.standart_evrak_olustur(calisan.id, 'ise_giris')
        for e in evraklar:
            session.add(e)
        session.commit()

        kayitlar = GirisCikisEvrak.query.filter_by(calisan_id=calisan.id).all()
        assert len(kayitlar) > 5  # Standart listede 10+ evrak var
        assert kayitlar[0].durum == 'bekliyor'
