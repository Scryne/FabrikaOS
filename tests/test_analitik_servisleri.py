"""
FDYS — Analitik Modül Testleri
Dalga 5.2 — Korelasyon, karşılaştırma, KPI, maliyet
"""
import pytest
from datetime import datetime, timezone


class TestKorelasyon:
    """Korelasyon servisi testleri."""

    def test_operator_makine_bos(self, app):
        """Veri yokken boş matris dönmeli."""
        with app.app_context():
            from app.services.analitik.korelasyon import korelasyon_servisi
            sonuc = korelasyon_servisi.operator_makine_matrisi()
            assert isinstance(sonuc, dict)
            assert 'matris' in sonuc

    def test_enerji_uretim(self, app):
        """Enerji-üretim korelasyonu hatasız çalışmalı."""
        with app.app_context():
            from app.services.analitik.korelasyon import korelasyon_servisi
            sonuc = korelasyon_servisi.enerji_uretim_korelasyonu()
            assert isinstance(sonuc, dict)
            assert 'pearson_r' in sonuc
            assert 'pearson_yorum' in sonuc

    def test_pearson_hesaplama(self, app):
        """Pearson korelasyon doğru hesaplanmalı."""
        with app.app_context():
            from app.services.analitik.korelasyon import KorelasyonServisi
            servis = KorelasyonServisi()
            # Mükemmel pozitif korelasyon
            r = servis._pearson_korelasyon([1, 2, 3, 4, 5], [2, 4, 6, 8, 10])
            assert r is not None
            assert abs(r - 1.0) < 0.001

            # Yetersiz veri
            r_yok = servis._pearson_korelasyon([1, 2], [3, 4])
            assert r_yok is None

    def test_hata_zaman_paterni(self, app):
        """Hata-zaman analizi hatasız çalışmalı."""
        with app.app_context():
            from app.services.analitik.korelasyon import korelasyon_servisi
            sonuc = korelasyon_servisi.hata_zaman_paterni()
            assert isinstance(sonuc, dict)
            assert 'matris' in sonuc
            assert len(sonuc['matris']) == 7

    def test_chi_square(self, app):
        """Chi-square testi doğru çalışmalı."""
        with app.app_context():
            from app.services.analitik.korelasyon import KorelasyonServisi
            servis = KorelasyonServisi()
            # Eşit dağılım -> anlamlı fark olmamalı
            matris = [[10, 10, 10]] * 7
            toplam = 210
            sonuc = servis._chi_square_test(matris, toplam)
            assert sonuc is not None
            assert sonuc['anlamli'] is False
            assert sonuc['chi2'] == 0

    def test_akilli_insightlar(self, app):
        """Akıllı insight'lar hatasız çalışmalı."""
        with app.app_context():
            from app.services.analitik.korelasyon import korelasyon_servisi
            insightlar = korelasyon_servisi.akilli_insightlar()
            assert isinstance(insightlar, list)


class TestKarsilastirma:
    """Karşılaştırma servisi testleri."""

    def test_gecersiz_makine(self, app):
        """Geçersiz makine ID'leri için None dönmeli."""
        with app.app_context():
            from app.services.analitik.karsilastirma import karsilastirma_servisi
            sonuc = karsilastirma_servisi.makine_karsilastir(99999, 99998)
            assert sonuc is None

    def test_vardiya_karsilastir(self, app):
        """Vardiya karşılaştırması hatasız çalışmalı."""
        with app.app_context():
            from app.services.analitik.karsilastirma import karsilastirma_servisi
            sonuclar = karsilastirma_servisi.vardiya_karsilastir()
            assert isinstance(sonuclar, list)
            assert len(sonuclar) == 3  # sabah, ogleden_sonra, gece


class TestKpiServisi:
    """KPI servisi testleri."""

    def test_kpi_dashboard(self, app):
        """KPI dashboard özeti hatasız çalışmalı."""
        with app.app_context():
            from app.services.analitik.kpi_servisi import kpi_servisi
            sonuc = kpi_servisi.kpi_dashboard_ozeti()
            assert isinstance(sonuc, list)

    def test_fabrika_saglik_skoru(self, app):
        """Fabrika sağlık skoru hatasız çalışmalı."""
        with app.app_context():
            from app.services.analitik.kpi_servisi import kpi_servisi
            sonuc = kpi_servisi.fabrika_saglik_skoru()
            assert isinstance(sonuc, dict)
            assert 'skor' in sonuc
            # KPI tanımlanmamışsa skor None olabilir
            if sonuc['skor'] is not None:
                assert 'seviye' in sonuc
                assert 0 <= sonuc['skor'] <= 100

    def test_yillik_seri(self, app):
        """Yıllık KPI serisi 12 ay dönmeli."""
        with app.app_context():
            from app.services.analitik.kpi_servisi import kpi_servisi
            sonuc = kpi_servisi.yillik_kpi_serisi('makine', 'ort_oee', 2026)
            assert isinstance(sonuc, list)
            assert len(sonuc) == 12

    def test_gerceklesen_hesapla(self, app):
        """Gerçekleşen hesabı hatasız çalışmalı."""
        with app.app_context():
            from app.services.analitik.kpi_servisi import kpi_servisi
            sonuc = kpi_servisi.gerceklesen_hesapla('makine', 'ort_oee', 2026, 1)
            assert sonuc is not None or sonuc == 0


class TestMaliyetServisi:
    """Maliyet servisi testleri."""

    def test_gecersiz_makine_tco(self, app):
        """Geçersiz makine için None dönmeli."""
        with app.app_context():
            from app.services.analitik.maliyet_servisi import maliyet_servisi
            sonuc = maliyet_servisi.makine_tco(99999)
            assert sonuc is None

    def test_birim_maliyet(self, app):
        """Birim maliyet listesi hatasız çalışmalı."""
        with app.app_context():
            from app.services.analitik.maliyet_servisi import maliyet_servisi
            sonuc = maliyet_servisi.tum_makineler_birim_maliyet()
            assert isinstance(sonuc, list)

    def test_amortisman_dogrusal(self, app):
        """Doğrusal amortisman hesabı doğru olmalı."""
        with app.app_context():
            from app.services.analitik.maliyet_servisi import MaliyetServisi
            servis = MaliyetServisi()
            sonuc = servis._amortisman_hesapla(100000, 365 * 5, 'dogrusal', 10)
            assert sonuc is not None
            assert sonuc['yillik_amortisman'] == 10000
            assert sonuc['amortisman_yuzde'] == 50.0  # 5 yıl / 10 yıl

    def test_amortisman_azalan(self, app):
        """Azalan bakiye amortismanı hesaplanabilmeli."""
        with app.app_context():
            from app.services.analitik.maliyet_servisi import MaliyetServisi
            servis = MaliyetServisi()
            sonuc = servis._amortisman_hesapla(100000, 365 * 5, 'azalan_bakiye', 10)
            assert sonuc is not None
            assert sonuc['kalan_defter_degeri'] > 0
            assert sonuc['kalan_defter_degeri'] < 100000

    def test_tco_karsilastirma(self, app):
        """TCO karşılaştırma tablosu hatasız çalışmalı."""
        with app.app_context():
            from app.services.analitik.maliyet_servisi import maliyet_servisi
            sonuc = maliyet_servisi.tum_makineler_tco_karsilastirma()
            assert isinstance(sonuc, list)
