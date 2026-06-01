import pytest
from datetime import datetime, timezone
from decimal import Decimal
from app.models.talep import Talep, TalepGecmisi
from app.models.dis_kullanici import DisKullanici, Borc, Tahsilat
from app.models.kullanici import Kullanici

def test_talep_olusturma_ve_gecisler(session, app):
    """Talep oluşturma ve durum geçişlerinin testi."""
    with app.test_request_context():
        # 1. Dahili talep oluşturma
        talep = Talep(
            talep_no="TLP-2026-00001",
            talep_eden_tip=Talep.TIP_DAHILI,
            talep_eden_id=1,
            talep_eden_adi="Ahmet Yılmaz",
            kategori=Talep.KAT_TEKNIK,
            baslik="Klima Arızası",
            aciklama="Ofis kliması soğutmuyor.",
            oncelik=Talep.ONCELIK_NORMAL
        )
        session.add(talep)
        session.commit()

        assert talep.id is not None
        assert talep.durum == Talep.DURUM_ACIK
        assert talep.gecis_gecerli_mi(Talep.DURUM_YONLENDIRILDI) is True
        assert talep.gecis_gecerli_mi(Talep.DURUM_TAMAMLANDI) is False

        # 2. Durum geçişi ve yönlendirme
        talep.durum = Talep.DURUM_YONLENDIRILDI
        talep.atanan_departman = Talep.DEPT_TEKNIK
        
        gecmis = TalepGecmisi(
            talep_id=talep.id,
            islem_turu=TalepGecmisi.ISLEM_YONLENDIRME,
            aciklama="Teknik departmana yönlendirildi.",
            eski_durum=Talep.DURUM_ACIK,
            yeni_durum=Talep.DURUM_YONLENDIRILDI
        )
        session.add(gecmis)
        session.commit()

        assert talep.durum == Talep.DURUM_YONLENDIRILDI
        assert talep.gecmis.count() == 1
        assert talep.gecmis.first().islem_turu == TalepGecmisi.ISLEM_YONLENDIRME

def test_dis_kullanici_borc_tahsilat(session, app):
    """Dış kullanıcı borç ve tahsilat takibi testi."""
    with app.test_request_context():
        # 1. Dış kullanıcı oluşturma
        dis_kullanici = DisKullanici(
            kullanici_adi="firma1_yetkili",
            ad_soyad="Ali Veli",
            telefon="05554443322",
            eposta="ali@firma1.com"
        )
        dis_kullanici.sifre_belirle("firma123")
        session.add(dis_kullanici)
        session.commit()

        assert dis_kullanici.id is not None
        assert dis_kullanici.sifre_dogrula("firma123") is True
        assert dis_kullanici.sifre_dogrula("yanlis") is False

        # 2. Borç oluşturma
        borc = Borc(
            ilgili_tip=Borc.TIP_FIRMA,
            ilgili_id=1,
            borc_turu=Borc.TUR_AIDAT,
            donem="2026-05",
            tutar=Decimal('5000.00')
        )
        session.add(borc)
        session.commit()

        assert borc.id is not None
        assert borc.kalan_tutar == 5000.00
        assert borc.durum == Borc.DURUM_ODENMEDI

        # 3. Kısmi Tahsilat
        tahsilat1 = Tahsilat(
            borc_id=borc.id,
            tutar=Decimal('2000.00'),
            odeme_turu=Tahsilat.TUR_HAVALE,
            aciklama="Mayıs ayı kısmi ödeme"
        )
        session.add(tahsilat1)
        borc.odenen_tutar += Decimal('2000.00')
        borc.durum_guncelle()
        session.commit()

        assert borc.kalan_tutar == 3000.00
        assert borc.durum == Borc.DURUM_KISMI
        assert borc.odeme_yuzde == 40.0

        # 4. Tam Tahsilat
        tahsilat2 = Tahsilat(
            borc_id=borc.id,
            tutar=Decimal('3000.00'),
            odeme_turu=Tahsilat.TUR_KREDI_KARTI,
            aciklama="Kalan ödeme"
        )
        session.add(tahsilat2)
        borc.odenen_tutar += Decimal('3000.00')
        borc.durum_guncelle()
        session.commit()

        assert borc.kalan_tutar == 0.00
        assert borc.durum == Borc.DURUM_ODENDI
        assert borc.odeme_yuzde == 100.0
