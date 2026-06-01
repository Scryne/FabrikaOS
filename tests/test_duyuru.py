"""
FDYS — Duyuru & İletişim Testleri
Faz 6
"""

import pytest
from datetime import datetime, timezone, timedelta
from app.models.duyuru import Duyuru, DuyuruOkunma
from app.models.kullanici import Kullanici


def test_duyuru_olusturma(app, session, temel_veriler):
    """Yeni duyuru oluşturulabilmeli."""
    kullanici = Kullanici.query.first()
    duyuru = Duyuru(
        baslik="Test Duyurusu",
        icerik="Bu bir testtir.",
        yayinlayan_id=kullanici.id,
        tur="bilgi",
        hedef_kitle="tumu"
    )
    session.add(duyuru)
    session.commit()

    assert duyuru.id is not None
    assert duyuru.baslik == "Test Duyurusu"
    assert duyuru.aktif_duyuru_mu is True


def test_duyuru_sure_kontrolu(app, session, temel_veriler):
    """Süresi dolan duyurular aktif sayılmamalı."""
    kullanici = Kullanici.query.first()

    # Süresiz
    d1 = Duyuru(baslik="Süresiz", icerik="T", yayinlayan_id=kullanici.id, bitis_tarihi=None)
    # Süresi geçmiş
    gecmis = datetime.now(timezone.utc) - timedelta(days=1)
    d2 = Duyuru(baslik="Geçmiş", icerik="T", yayinlayan_id=kullanici.id, bitis_tarihi=gecmis)
    # Gelecek
    gelecek = datetime.now(timezone.utc) + timedelta(days=1)
    d3 = Duyuru(baslik="Gelecek", icerik="T", yayinlayan_id=kullanici.id, bitis_tarihi=gelecek)

    session.add_all([d1, d2, d3])
    session.commit()

    assert d1.suresi_doldu_mu is False
    assert d2.suresi_doldu_mu is True
    assert d3.suresi_doldu_mu is False


def test_hedef_kitle_kontrolu(app, session, temel_veriler):
    """Hedef kitle yetkilendirmesi çalışmalı."""
    yonetici = Kullanici.query.filter_by(rol='yonetici').first()
    kullanici1 = Kullanici(kullanici_adi='u1', sifre_hash='dummy', ad_soyad='U1', departman='uretim', rol='personel')
    kullanici2 = Kullanici(kullanici_adi='u2', sifre_hash='dummy', ad_soyad='U2', departman='kalite', rol='personel')
    session.add_all([kullanici1, kullanici2])
    session.commit()

    # Tümü
    d1 = Duyuru(baslik="Tumu", icerik="T", hedef_kitle="tumu")
    # Departman
    d2 = Duyuru(baslik="Dept", icerik="T", hedef_kitle="departman", hedef_deger="uretim")
    session.add_all([d1, d2])
    session.commit()

    assert d1.kullanici_gorebilir_mi(kullanici1) is True

    assert d2.kullanici_gorebilir_mi(kullanici1) is True
    assert d2.kullanici_gorebilir_mi(kullanici2) is False

    # Yönetici her zaman görür
    assert d2.kullanici_gorebilir_mi(yonetici) is True


def test_okunma_takibi(app, session, temel_veriler):
    """Duyuru okunma takibi çalışmalı."""
    kullanici = Kullanici.query.first()
    duyuru = Duyuru(baslik="Okunma Testi", icerik="T", yayinlayan_id=kullanici.id)
    session.add(duyuru)
    session.commit()

    assert duyuru.okunma_sayisi == 0
    assert duyuru.kullanici_okudu_mu(kullanici.id) is False

    # Okudu işaretle
    duyuru.okunma_kaydet(kullanici.id)
    session.commit()

    assert duyuru.okunma_sayisi == 1
    assert duyuru.kullanici_okudu_mu(kullanici.id) is True

    # İkinci kez okursa sayı artmamalı
    duyuru.okunma_kaydet(kullanici.id)
    session.commit()
    assert duyuru.okunma_sayisi == 1
