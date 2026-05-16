"""
FDYS — AI Tahminleme Motoru (Merkezi Orchestrator) v2.0
Kategori 1 — Yapay Zeka Destekli Tahminleme

4 alt servisi koordine eder ve sonuçları TahminKaydi tablosuna kaydeder.
Dashboard ve bildirim entegrasyonu sağlar.

v2.0 Yenilikler:
    - Modül bazlı performans izleme (çalışma süresi loglama)
    - Bildirim spam önleme (24 saat tekrar engelleme)
    - Bakım tahmini → otomasyon motoruna iş emri tetikleme
    - Dashboard özeti cache desteği
"""

import logging
import json
import time
from datetime import datetime, timedelta, timezone

from app.extensions import db

logger = logging.getLogger(__name__)


class TahminMotoru:
    """Merkezi AI tahminleme orkestratörü."""

    # Bildirim spam önleme: her kaynak için son bildirim zamanı
    _son_bildirimler = {}

    def tum_tahminleri_calistir(self):
        """Tüm AI modüllerini çalıştırır ve sonuçları kaydeder."""
        sonuclar = {
            'bakim': [],
            'oee': [],
            'stok': [],
            'anomali': [],
            'ozet': {},
            'performans': {}
        }

        # Her modül için çalışma süresini ölç
        for modul, method in [
            ('bakim', self._bakim_tahminleri),
            ('oee', self._oee_tahminleri),
            ('stok', self._stok_tahminleri),
            ('anomali', self._anomali_tahminleri),
        ]:
            baslangic = time.time()
            try:
                sonuclar[modul] = method()
                sure = round(time.time() - baslangic, 3)
                sonuclar['performans'][modul] = {
                    'sure_sn': sure,
                    'kayit_sayisi': len(sonuclar[modul]),
                    'durum': 'basarili'
                }
                logger.info(f"AI Modül [{modul}]: {len(sonuclar[modul])} kayıt, {sure}s")
            except Exception as e:
                sure = round(time.time() - baslangic, 3)
                sonuclar['performans'][modul] = {
                    'sure_sn': sure,
                    'kayit_sayisi': 0,
                    'durum': 'hata',
                    'hata': str(e)
                }
                logger.error(f"AI Modül [{modul}] hatası ({sure}s): {e}", exc_info=True)

        # Özet istatistikler
        sonuclar['ozet'] = self._ozet_hesapla(sonuclar)

        # Kritik tahminler için bildirim gönder (spam korumalı)
        self._bildirimleri_gonder(sonuclar)

        # Kritik bakım tahminleri için otomatik iş emri tetikle
        self._bakim_is_emri_tetikle(sonuclar.get('bakim', []))

        return sonuclar

    def _bakim_tahminleri(self):
        """Kestirimci bakım analizi çalıştırır."""
        from app.services.ai.kestirimci_bakim import kestirimci_bakim_servisi
        from app.models.tahmin import TahminKaydi

        sonuclar = kestirimci_bakim_servisi.tum_makineleri_analiz_et()

        # Mevcut bakım tahminlerini pasifleştir
        TahminKaydi.query.filter_by(tahmin_turu='bakim', aktif=True).update({'aktif': False})

        for s in sonuclar:
            kayit = TahminKaydi(
                tahmin_turu='bakim',
                kaynak_turu='makine',
                kaynak_id=s['makine_id'],
                kaynak_adi=s['makine_ad'],
                baslik=f"{s['makine_ad']} — Bakım Tahmini",
                aciklama=s['oneri'],
                risk_skoru=s['risk_skoru'],
                tahmin_tarihi=datetime.fromisoformat(s['tahmin_tarihi']).date() if s.get('tahmin_tarihi') else None,
                tahmini_gun=s.get('tahmini_gun'),
                oneri=s['oneri'],
                model_versiyonu=s.get('model_versiyonu', 'v2.0'),
                meta_veri=json.dumps({
                    **s.get('detaylar', {}),
                    'confidence_score': s.get('confidence_score'),
                    'ml_kullanildi': s.get('ml_kullanildi'),
                }, ensure_ascii=False)
            )
            db.session.add(kayit)

        db.session.commit()
        return sonuclar

    def _oee_tahminleri(self):
        """OEE trend tahmini çalıştırır."""
        from app.services.ai.oee_tahmin import oee_tahmin_servisi
        from app.models.tahmin import TahminKaydi

        sonuclar = oee_tahmin_servisi.tum_makineleri_analiz_et()

        TahminKaydi.query.filter_by(tahmin_turu='oee', aktif=True).update({'aktif': False})

        for s in sonuclar:
            kayit = TahminKaydi(
                tahmin_turu='oee',
                kaynak_turu='makine',
                kaynak_id=s['makine_id'],
                kaynak_adi=s['makine_ad'],
                baslik=f"{s['makine_ad']} — OEE Tahmini",
                aciklama=s.get('uyari', f"OEE Tahmini: %{s.get('tahmin_ort', 0)}"),
                risk_skoru=s.get('risk_skoru', 0),
                oneri=s.get('uyari'),
                model_versiyonu=s.get('model_versiyonu', 'v2.0'),
                meta_veri=json.dumps({
                    'makine_kod': s.get('makine_kod'),
                    'mevcut_oee': s.get('mevcut_oee'),
                    'tahmin_ort': s.get('tahmin_ort'),
                    'trend': s.get('trend'),
                    'hedef_oee': s.get('hedef_oee'),
                    'guvenilirlik': s.get('guvenilirlik'),
                    'gecmis': s.get('gecmis'),
                    'tahmin': s.get('tahmin'),
                }, ensure_ascii=False)
            )
            db.session.add(kayit)

        db.session.commit()
        return sonuclar

    def _stok_tahminleri(self):
        """Stok tükenme tahmini çalıştırır."""
        from app.services.ai.stok_tahmin import stok_tahmin_servisi
        from app.models.tahmin import TahminKaydi

        sonuclar = stok_tahmin_servisi.tum_malzemeleri_analiz_et()

        TahminKaydi.query.filter_by(tahmin_turu='stok', aktif=True).update({'aktif': False})

        for s in sonuclar:
            kayit = TahminKaydi(
                tahmin_turu='stok',
                kaynak_turu='malzeme',
                kaynak_id=s['malzeme_id'],
                kaynak_adi=s['malzeme_ad'],
                baslik=f"{s['malzeme_ad']} — Stok Tahmini",
                aciklama=s.get('oneri', ''),
                risk_skoru=s.get('risk_skoru', 0),
                tahmini_gun=s.get('tukenme_gun'),
                oneri=s.get('siparis_zamani') or s.get('oneri'),
                model_versiyonu=s.get('model_versiyonu', 'v2.0'),
                meta_veri=json.dumps({
                    'mevcut_miktar': s.get('mevcut_miktar'),
                    'gunluk_tuketim': s.get('gunluk_tuketim'),
                    'teslimat_gun': s.get('teslimat_gun'),
                    'minimum_stok': s.get('minimum_stok'),
                    'emniyet_stoku': s.get('emniyet_stoku'),
                    'siparis_miktari': s.get('siparis_miktari_onerisi'),
                    'spike_tespit': s.get('spike_tespit'),
                }, ensure_ascii=False)
            )
            db.session.add(kayit)

        db.session.commit()
        return sonuclar

    def _anomali_tahminleri(self):
        """Anomali tespiti çalıştırır."""
        from app.services.ai.anomali_tespit import anomali_tespit_servisi
        from app.models.tahmin import TahminKaydi

        sonuclar = anomali_tespit_servisi.tum_anomalileri_tespit_et()

        TahminKaydi.query.filter_by(tahmin_turu='anomali', aktif=True).update({'aktif': False})

        for s in sonuclar:
            kayit = TahminKaydi(
                tahmin_turu='anomali',
                kaynak_turu=s.get('kaynak_turu', 'sistem'),
                kaynak_id=s.get('kaynak_id', 0),
                kaynak_adi=s.get('kaynak_adi', ''),
                baslik=s.get('baslik', 'Anomali Tespit Edildi'),
                aciklama=s.get('aciklama', ''),
                risk_skoru=s.get('risk_skoru', 0),
                model_versiyonu=s.get('model_versiyonu', 'v2.0'),
                meta_veri=json.dumps({
                    'tip': s.get('tip'),
                    'deger': s.get('deger'),
                    'ortalama': s.get('ortalama'),
                    'sapma_yuzde': s.get('sapma_yuzde'),
                    'z_score': s.get('z_score'),
                    'gecmis_benzer': s.get('gecmis_benzer'),
                }, ensure_ascii=False)
            )
            db.session.add(kayit)

        db.session.commit()
        return sonuclar

    def _ozet_hesapla(self, sonuclar):
        """Tahmin sonuçlarının özetini oluşturur."""
        bakim_kritik = sum(1 for s in sonuclar['bakim'] if s.get('risk_skoru', 0) >= 75)
        bakim_yuksek = sum(1 for s in sonuclar['bakim'] if 50 <= s.get('risk_skoru', 0) < 75)
        stok_kritik = sum(1 for s in sonuclar['stok'] if s.get('kritik_mi', False))
        anomali_sayisi = len(sonuclar['anomali'])

        return {
            'toplam_tahmin': (len(sonuclar['bakim']) + len(sonuclar['oee']) +
                              len(sonuclar['stok']) + len(sonuclar['anomali'])),
            'bakim_kritik': bakim_kritik,
            'bakim_yuksek': bakim_yuksek,
            'stok_kritik': stok_kritik,
            'anomali_sayisi': anomali_sayisi,
            'kritik_toplam': bakim_kritik + stok_kritik,
            'guncelleme_zamani': datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M'),
            'performans': sonuclar.get('performans', {})
        }

    def _bildirim_gonderilmis_mi(self, anahtar):
        """Son 24 saat içinde aynı anahtar için bildirim gönderilmiş mi kontrol eder."""
        son = self._son_bildirimler.get(anahtar)
        if son is None:
            return False
        return (datetime.now(timezone.utc) - son).total_seconds() < 86400  # 24 saat

    def _bildirimleri_gonder(self, sonuclar):
        """Kritik tahminler için bildirim oluşturur (spam korumalı)."""
        try:
            from app.services.bildirim_motoru import bildirim_motoru
            from app.models.kullanici import Kullanici

            yoneticiler = Kullanici.query.filter_by(rol='yonetici', aktif=True).all()
            if not yoneticiler:
                return

            # Kritik bakım tahminleri
            for s in sonuclar['bakim']:
                if s.get('risk_skoru', 0) >= 75:
                    anahtar = f"bakim_{s['makine_id']}"
                    if self._bildirim_gonderilmis_mi(anahtar):
                        continue
                    for y in yoneticiler:
                        bildirim_motoru.bildirim_olustur(
                            kullanici_id=y.id,
                            baslik=f"🧠 AI: Kritik Bakım Uyarısı — {s['makine_ad']}",
                            mesaj=f"Risk: %{s['risk_skoru']} (Güven: %{s.get('confidence_score', 0) * 100:.0f}) — {s['oneri'][:100]}",
                            seviye='kritik',
                            modul='tahmin',
                            url='/tahmin/kestirimci-bakim'
                        )
                    self._son_bildirimler[anahtar] = datetime.now(timezone.utc)

            # Kritik stok tahminleri
            for s in sonuclar['stok']:
                if s.get('risk_skoru', 0) >= 75:
                    anahtar = f"stok_{s['malzeme_id']}"
                    if self._bildirim_gonderilmis_mi(anahtar):
                        continue
                    for y in yoneticiler:
                        bildirim_motoru.bildirim_olustur(
                            kullanici_id=y.id,
                            baslik=f"🧠 AI: Stok Tükenme Uyarısı — {s['malzeme_ad']}",
                            mesaj=f"Tahmini tükenme: {s.get('tukenme_gun', '?')} gün — {s.get('siparis_zamani', '')}",
                            seviye='uyari',
                            modul='tahmin',
                            url='/tahmin/stok-tahmin'
                        )
                    self._son_bildirimler[anahtar] = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"AI bildirim hatası: {e}", exc_info=True)

    def _bakim_is_emri_tetikle(self, bakim_sonuclari):
        """Kritik bakım tahminleri için otomasyon motoruna iş emri tetikler."""
        try:
            from app.models.makine import Makine

            for s in bakim_sonuclari:
                if s.get('risk_skoru', 0) >= 75:
                    makine = Makine.query.get(s['makine_id'])
                    if makine:
                        from app.services.otomasyon_motoru import otomasyon_motoru
                        otomasyon_motoru.bakim_is_emri_olustur(makine)
        except Exception as e:
            logger.error(f"AI → İş emri tetikleme hatası: {e}", exc_info=True)

    def dashboard_ozeti(self):
        """Dashboard için hızlı AI özet verisi döner (DB'den)."""
        from app.models.tahmin import TahminKaydi

        aktif_tahminler = TahminKaydi.query.filter_by(aktif=True).all()

        bakim_tahminleri = [t for t in aktif_tahminler if t.tahmin_turu == 'bakim']
        stok_tahminleri = [t for t in aktif_tahminler if t.tahmin_turu == 'stok']
        anomaliler = [t for t in aktif_tahminler if t.tahmin_turu == 'anomali']

        en_riskli = sorted(aktif_tahminler, key=lambda t: float(t.risk_skoru or 0), reverse=True)[:5]

        return {
            'kritik_bakim': sum(1 for t in bakim_tahminleri if float(t.risk_skoru or 0) >= 75),
            'yuksek_bakim': sum(1 for t in bakim_tahminleri if 50 <= float(t.risk_skoru or 0) < 75),
            'kritik_stok': sum(1 for t in stok_tahminleri if float(t.risk_skoru or 0) >= 50),
            'anomali_sayisi': len(anomaliler),
            'en_riskli': en_riskli,
            'toplam_tahmin': len(aktif_tahminler),
            'son_guncelleme': max((t.olusturma_tarihi for t in aktif_tahminler), default=None)
        }


tahmin_motoru = TahminMotoru()
