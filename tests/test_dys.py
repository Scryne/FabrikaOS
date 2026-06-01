"""
FDYS — DYS (Doküman Yönetim Sistemi) Testleri
Faz 6
"""

import pytest
from app.models.dys import Dokuman
from app.models.kullanici import Kullanici


def test_dokuman_olusturma(app, session, temel_veriler):
    """Yeni doküman oluşturulabilmeli."""
    kullanici = Kullanici.query.first()
    dokuman = Dokuman(
        baslik="Test Prosedürü",
        kategori="prosedur",
        dosya_adi="dys/test.pdf",
        orijinal_adi="test.pdf",
        sahip_id=kullanici.id,
        versiyon=1
    )
    session.add(dokuman)
    session.commit()

    assert dokuman.id is not None
    assert dokuman.baslik == "Test Prosedürü"
    assert dokuman.dosya_tipi == "pdf"


def test_versiyon_gecmisi(app, session, temel_veriler):
    """Versiyon geçmişi doğru çalışmalı."""
    kullanici = Kullanici.query.first()

    # V1
    v1 = Dokuman(
        baslik="Sözleşme", kategori="sozlesme", dosya_adi="dys/v1.pdf",
        orijinal_adi="sozlesme.pdf", sahip_id=kullanici.id, versiyon=1
    )
    session.add(v1)
    session.commit()

    # V2
    v2 = Dokuman(
        baslik="Sözleşme", kategori="sozlesme", dosya_adi="dys/v2.pdf",
        orijinal_adi="sozlesme_v2.pdf", sahip_id=kullanici.id, versiyon=2,
        onceki_versiyon_id=v1.id
    )
    session.add(v2)
    session.commit()

    # V3
    v3 = Dokuman(
        baslik="Sözleşme", kategori="sozlesme", dosya_adi="dys/v3.pdf",
        orijinal_adi="sozlesme_v3.pdf", sahip_id=kullanici.id, versiyon=3,
        onceki_versiyon_id=v2.id
    )
    session.add(v3)
    session.commit()

    gecmis = v3.versiyon_gecmisi()
    assert len(gecmis) == 3
    assert gecmis[0].versiyon == 3
    assert gecmis[1].versiyon == 2
    assert gecmis[2].versiyon == 1


def test_erisim_kontrol(app, session, temel_veriler):
    """Doküman erişim kontrolleri çalışmalı."""
    yonetici = Kullanici.query.filter_by(rol='yonetici').first()
    kullanici1 = Kullanici(kullanici_adi='user1', sifre_hash='dummy', ad_soyad='User 1', departman='uretim')
    kullanici2 = Kullanici(kullanici_adi='user2', sifre_hash='dummy', ad_soyad='User 2', departman='kalite')
    session.add_all([kullanici1, kullanici2])
    session.commit()

    # Herkese açık
    d1 = Dokuman(baslik="Public", dosya_adi="p.pdf", orijinal_adi="p.pdf", erisim_seviyesi="herkese_acik")
    assert d1.erisim_kontrol(kullanici1) is True

    # Özel (Sadece sahip)
    d2 = Dokuman(baslik="Private", dosya_adi="p2.pdf", orijinal_adi="p2.pdf", erisim_seviyesi="ozel", sahip_id=kullanici1.id)
    assert d2.erisim_kontrol(kullanici1) is True
    assert d2.erisim_kontrol(kullanici2) is False

    # Departman içi
    d3 = Dokuman(baslik="Dept", dosya_adi="p3.pdf", orijinal_adi="p3.pdf", erisim_seviyesi="departman", departman="uretim")
    assert d3.erisim_kontrol(kullanici1) is True   # Üretim
    assert d3.erisim_kontrol(kullanici2) is False  # Kalite

    # Yönetici her şeye erişir
    assert d2.erisim_kontrol(yonetici) is True
    assert d3.erisim_kontrol(yonetici) is True
