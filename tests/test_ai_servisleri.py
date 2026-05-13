"""
FDYS — AI Modül Testleri
Dalga 5.1 — Kestirimci bakım, OEE tahmin, stok tahmin, anomali tespit
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock


class TestKestirimciBakim:
    """Kestirimci bakım servisi testleri."""

    def test_bos_makine_listesi(self, app):
        """Hiç makine yokken boş sonuç dönmeli."""
        with app.app_context():
            from app.services.ai.kestirimci_bakim import kestirimci_bakim_servisi
            sonuc = kestirimci_bakim_servisi.tum_makineleri_analiz_et()
            assert isinstance(sonuc, list)

    def test_tek_makine_analiz(self, app, sample_data):
        """Tek makine için analiz sonucu döner."""
        with app.app_context():
            from app.services.ai.kestirimci_bakim import kestirimci_bakim_servisi
            makine = sample_data.get('makine')
            if makine:
                sonuc = kestirimci_bakim_servisi.makine_tahmini(makine.id)
                assert sonuc is not None
                assert 'risk_skoru' in sonuc
                assert 0 <= sonuc['risk_skoru'] <= 100
                assert 'confidence_score' in sonuc
                assert 'oneri' in sonuc
                assert 'model_versiyonu' in sonuc

    def test_gecersiz_makine_id(self, app):
        """Geçersiz makine ID'si için None dönmeli."""
        with app.app_context():
            from app.services.ai.kestirimci_bakim import kestirimci_bakim_servisi
            sonuc = kestirimci_bakim_servisi.makine_tahmini(99999)
            assert sonuc is None

    def test_risk_skoru_araligi(self, app, sample_data):
        """Risk skoru 0-100 arasında olmalı."""
        with app.app_context():
            from app.services.ai.kestirimci_bakim import kestirimci_bakim_servisi
            sonuclar = kestirimci_bakim_servisi.tum_makineleri_analiz_et()
            for s in sonuclar:
                assert 0 <= s['risk_skoru'] <= 100

    def test_heuristik_fallback(self, app):
        """ML başarısız olursa heuristik kullanılmalı."""
        with app.app_context():
            from app.services.ai.kestirimci_bakim import KestirimciBakimServisi
            servis = KestirimciBakimServisi()
            risk = servis._heuristik_risk_hesapla(
                bakim_oran=1.5, ariza_sayisi=3, toplam_calisma_saat=500,
                toplam_durus_saat=100, son_ariza_gunu=10, mtbf_gun=30,
                ort_oee=60, makine_durumu='aktif'
            )
            assert 0 <= risk <= 100
            assert risk > 30  # Yüksek risk parametreleri ile düşük çıkmamalı

    def test_dogruluk_raporu(self, app):
        """Doğruluk raporu hatasız çalışmalı."""
        with app.app_context():
            from app.services.ai.kestirimci_bakim import kestirimci_bakim_servisi
            rapor = kestirimci_bakim_servisi.dogruluk_raporu()
            assert isinstance(rapor, dict)
            assert 'toplam' in rapor


class TestOEETahmin:
    """OEE tahmin servisi testleri."""

    def test_bos_veri(self, app):
        """Yetersiz veri olduğunda None dönmeli."""
        with app.app_context():
            from app.services.ai.oee_tahmin import oee_tahmin_servisi
            sonuc = oee_tahmin_servisi.makine_tahmini(99999)
            assert sonuc is None

    def test_tum_makineler(self, app):
        """Tüm makineler analizi hatasız çalışmalı."""
        with app.app_context():
            from app.services.ai.oee_tahmin import oee_tahmin_servisi
            sonuclar = oee_tahmin_servisi.tum_makineleri_analiz_et()
            assert isinstance(sonuclar, list)

    def test_holt_tahmin_algoritmasi(self, app):
        """Holt ES algoritması doğru çalışmalı."""
        with app.app_context():
            from app.services.ai.oee_tahmin import OEETahminServisi
            servis = OEETahminServisi()
            degerler = [80, 82, 79, 81, 83, 80, 78, 82, 84, 81, 79, 83, 85, 82]
            tahmin, alt, ust = servis._holt_tahmin(degerler)
            assert len(tahmin) == 7
            assert len(alt) == 7
            assert len(ust) == 7
            for i in range(7):
                assert alt[i] <= tahmin[i] <= ust[i]  # Güven aralığı mantıklı
                assert 0 <= tahmin[i] <= 100

    def test_interpolasyon(self, app):
        """Boşluk interpolasyonu çalışmalı."""
        with app.app_context():
            from app.services.ai.oee_tahmin import OEETahminServisi
            servis = OEETahminServisi()
            tarihler = [datetime(2026, 1, i).date() for i in range(1, 6)]
            degerler = [80, 82, 0, 84, 81]
            sonuc = servis._interpolate_gaps(tarihler, degerler)
            assert sonuc[2] != 0  # Sıfır değer düzeltilmiş olmalı


class TestStokTahmin:
    """Stok tahmin servisi testleri."""

    def test_tum_malzemeler(self, app):
        """Tüm malzemeler analizi hatasız çalışmalı."""
        with app.app_context():
            from app.services.ai.stok_tahmin import stok_tahmin_servisi
            sonuclar = stok_tahmin_servisi.tum_malzemeleri_analiz_et()
            assert isinstance(sonuclar, list)

    def test_spike_detection_normal(self, app):
        """Normal veride spike tespit edilmemeli."""
        with app.app_context():
            from app.services.ai.stok_tahmin import StokTahminServisi
            servis = StokTahminServisi()
            degerler = [10, 12, 11, 13, 10, 11, 12]
            assert servis._spike_tespit(degerler) is False

    def test_spike_detection_anomali(self, app):
        """Ani artış spike olarak tespit edilmeli."""
        with app.app_context():
            from app.services.ai.stok_tahmin import StokTahminServisi
            servis = StokTahminServisi()
            degerler = [10, 10, 10, 10, 10, 10, 10, 10, 10, 200]  # Son değer belirgin spike
            assert servis._spike_tespit(degerler) is True

    def test_haftalik_profil(self, app):
        """Haftalık profil hesaplaması çalışmalı."""
        with app.app_context():
            from app.services.ai.stok_tahmin import StokTahminServisi
            servis = StokTahminServisi()
            cikislar = [(datetime(2026, 1, 6).date(), 10), (datetime(2026, 1, 7).date(), 15)]
            profil = servis._haftalik_profil_hesapla(cikislar)
            assert isinstance(profil, dict)
            assert len(profil) == 7

    def test_sifir_tuketim(self, app):
        """Sıfır tüketimde risk düşük olmalı."""
        with app.app_context():
            from app.services.ai.stok_tahmin import StokTahminServisi
            servis = StokTahminServisi()
            risk = servis._hesapla_risk(100, 10, None, 7, None, False)
            assert risk < 50


class TestAnomaliTespit:
    """Anomali tespit servisi testleri."""

    def test_tum_anomaliler(self, app):
        """Tüm anomali taraması hatasız çalışmalı."""
        with app.app_context():
            from app.services.ai.anomali_tespit import anomali_tespit_servisi
            sonuclar = anomali_tespit_servisi.tum_anomalileri_tespit_et()
            assert isinstance(sonuclar, list)

    def test_percentile_hesaplama(self, app):
        """Percentile hesaplaması doğru olmalı."""
        with app.app_context():
            from app.services.ai.anomali_tespit import AnomaliTespitServisi
            servis = AnomaliTespitServisi()
            veri = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            q1 = servis._percentile(veri, 25)
            q3 = servis._percentile(veri, 75)
            assert 2 < q1 < 4
            assert 7 < q3 < 9

    def test_false_positive_filtreleme(self, app):
        """Aynı kaynaktan aynı gün tekrar anomali filtrelenmeli."""
        with app.app_context():
            from app.services.ai.anomali_tespit import AnomaliTespitServisi
            servis = AnomaliTespitServisi()
            anomaliler = [
                {'tip': 'enerji', 'kaynak_id': 1, 'tarih': '2026-01-01', 'risk_skoru': 50},
                {'tip': 'enerji', 'kaynak_id': 1, 'tarih': '2026-01-01', 'risk_skoru': 60},  # Tekrar
                {'tip': 'enerji', 'kaynak_id': 2, 'tarih': '2026-01-01', 'risk_skoru': 40},
            ]
            filtrelenmis = servis._false_positive_filtrele(anomaliler)
            assert len(filtrelenmis) == 2  # 3'ten 2'ye düşmeli

    def test_yapılandirilabilir_esik(self, app):
        """Z-score eşiği yapılandırılabilir olmalı."""
        with app.app_context():
            from app.services.ai.anomali_tespit import AnomaliTespitServisi
            servis = AnomaliTespitServisi(z_esik=3.0)
            assert servis.z_esik == 3.0

    def test_bos_veri(self, app):
        """Boş veri ile percentile 0 dönmeli."""
        with app.app_context():
            from app.services.ai.anomali_tespit import AnomaliTespitServisi
            servis = AnomaliTespitServisi()
            assert servis._percentile([], 25) == 0


class TestTahminMotoru:
    """Tahmin motoru orkestratör testleri."""

    def test_dashboard_ozeti(self, app):
        """Dashboard özeti hatasız çalışmalı."""
        with app.app_context():
            from app.services.tahmin_motoru import tahmin_motoru
            ozet = tahmin_motoru.dashboard_ozeti()
            assert isinstance(ozet, dict)
            assert 'toplam_tahmin' in ozet
            assert 'kritik_bakim' in ozet

    def test_bildirim_spam_onleme(self, app):
        """Aynı anahtar için 24 saat içinde tekrar bildirim engellenmeli."""
        with app.app_context():
            from app.services.tahmin_motoru import TahminMotoru
            motor = TahminMotoru()
            motor._son_bildirimler['test_key'] = datetime.now(timezone.utc)
            assert motor._bildirim_gonderilmis_mi('test_key') is True
            assert motor._bildirim_gonderilmis_mi('baska_key') is False
