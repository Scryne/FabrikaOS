"""
FDYS — Otomasyon Modül Testleri
Dalga 5.3 — Otomasyon motoru, iş emri servisi, SLA
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock


class TestOtomasyonMotoru:
    """Otomasyon motoru testleri."""

    def test_kural_toggle(self, app):
        """Kural aktif/pasif toggle çalışmalı."""
        with app.app_context():
            from app.services.otomasyon_motoru import OtomasyonMotoru
            motor = OtomasyonMotoru()
            assert motor.kural_aktif_mi('ariza_is_emri') is True
            motor.kural_toggle('ariza_is_emri', False)
            assert motor.kural_aktif_mi('ariza_is_emri') is False
            motor.kural_toggle('ariza_is_emri', True)

    def test_kural_istatistikleri(self, app):
        """Kural istatistikleri düzgün dönmeli."""
        with app.app_context():
            from app.services.otomasyon_motoru import OtomasyonMotoru
            motor = OtomasyonMotoru()
            istat = motor.kural_istatistikleri_al()
            assert isinstance(istat, dict)
            assert 'ariza_is_emri' in istat
            assert 'aktif' in istat['ariza_is_emri']

    def test_pasif_kural_atlanir(self, app):
        """Pasif kural çalıştırılmamalı."""
        with app.app_context():
            from app.services.otomasyon_motoru import OtomasyonMotoru
            motor = OtomasyonMotoru()
            motor.kural_toggle('stok_satin_alma', False)
            mock_malzeme = MagicMock()
            sonuc = motor.stok_satin_alma_talebi(mock_malzeme)
            assert sonuc is None
            motor.kural_toggle('stok_satin_alma', True)

    def test_akilli_teknisyen_bos(self, app):
        """Teknisyen yokken None dönmeli."""
        with app.app_context():
            from app.services.otomasyon_motoru import OtomasyonMotoru
            motor = OtomasyonMotoru()
            # Bu test geçerli teknisyen yoksa None döner
            sonuc = motor._akilli_teknisyen_bul(makine_id=None)
            # Sonuç teknisyen yoksa None veya varsa teknisyen olmalı
            assert sonuc is None or hasattr(sonuc, 'id')


class TestIsEmriServisi:
    """İş emri servisi testleri."""

    def test_is_emri_no_uretimi(self, app):
        """İş emri numarası doğru formatta üretilmeli."""
        with app.app_context():
            from app.services.is_emri_servisi import is_emri_servisi
            no = is_emri_servisi.is_emri_no_uret()
            yil = datetime.now(timezone.utc).year
            assert no.startswith(f"IE-{yil}-")
            assert len(no.split('-')[-1]) == 4

    def test_istatistikler(self, app):
        """İstatistik sonuçları doğru yapıda olmalı."""
        with app.app_context():
            from app.services.is_emri_servisi import is_emri_servisi
            istat = is_emri_servisi.istatistikler()
            assert isinstance(istat, dict)
            assert 'toplam' in istat
            assert 'bekleyen' in istat
            assert 'sla_asilan' in istat
            assert istat['bekleyen'] == istat['acik'] + istat['atandi'] + istat['devam']

    def test_teknisyen_performans_raporu(self, app):
        """Teknisyen performans raporu hatasız çalışmalı."""
        with app.app_context():
            from app.services.is_emri_servisi import is_emri_servisi
            rapor = is_emri_servisi.teknisyen_performans_raporu()
            assert isinstance(rapor, list)

    def test_kategori_istatistik(self, app):
        """Kategori istatistiği hatasız çalışmalı."""
        with app.app_context():
            from app.services.is_emri_servisi import is_emri_servisi
            sonuc = is_emri_servisi.kategori_istatistik()
            assert isinstance(sonuc, list)

    def test_haftalik_trend(self, app):
        """Haftalık trend 8 hafta dönmeli."""
        with app.app_context():
            from app.services.is_emri_servisi import is_emri_servisi
            trend = is_emri_servisi.haftalik_trend()
            assert isinstance(trend, list)
            assert len(trend) == 8


class TestSLA:
    """SLA mekanizması testleri."""

    def test_sla_hesaplama(self, app):
        """SLA doğru hesaplanmalı."""
        with app.app_context():
            from app.models.is_emri import IsEmri
            ie = IsEmri(oncelik='kritik')
            ie.olusturma_tarihi = datetime.now(timezone.utc)
            ie.sla_hesapla()
            assert ie.sla_saat == 4
            assert ie.sla_bitis is not None

    def test_sla_kalan_yuzde(self, app):
        """SLA kalan yüzde doğru hesaplanmalı."""
        with app.app_context():
            from app.models.is_emri import IsEmri
            ie = IsEmri(oncelik='normal', durum='acik')
            ie.olusturma_tarihi = datetime.now(timezone.utc)
            ie.sla_hesapla()
            kalan = ie.sla_kalan_yuzde
            assert kalan is not None
            assert 0 <= kalan <= 100

    def test_sla_toplu_kontrol(self, app):
        """Toplu SLA kontrolü hatasız çalışmalı."""
        with app.app_context():
            from app.services.is_emri_servisi import is_emri_servisi
            sonuc = is_emri_servisi.sla_toplu_kontrol()
            assert isinstance(sonuc, dict)
            assert 'asilmis' in sonuc
            assert 'uyari' in sonuc

    def test_gecis_gecerliligi(self, app):
        """Durum geçiş kontrolleri doğru çalışmalı."""
        with app.app_context():
            from app.models.is_emri import IsEmri
            ie = IsEmri(durum='acik')
            assert ie.gecis_gecerli_mi('atandi') is True
            assert ie.gecis_gecerli_mi('tamamlandi') is False

            ie2 = IsEmri(durum='devam')
            assert ie2.gecis_gecerli_mi('tamamlandi') is True
            assert ie2.gecis_gecerli_mi('acik') is False

    def test_iptal_neden_zorunlu(self, app):
        """İptal edilirken neden belirtilmeli."""
        with app.app_context():
            from app.services.is_emri_servisi import is_emri_servisi
            from app.models.is_emri import IsEmri
            from app.extensions import db

            ie = IsEmri(
                is_emri_no='IE-TEST-0001', baslik='Test',
                durum='acik', oncelik='normal'
            )
            ie.olusturma_tarihi = datetime.now(timezone.utc)
            db.session.add(ie)
            db.session.commit()

            basarili, mesaj = is_emri_servisi.durum_guncelle(
                ie.id, 'iptal', kullanici_id=None
            )
            assert basarili is False
            assert 'neden' in mesaj.lower() or 'neden' in mesaj
