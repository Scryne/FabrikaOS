"""
FDYS — Kestirimci Bakım Servisi (Predictive Maintenance)
Kategori 1.1 — AI Tahminleme Motoru v2.0

Makine başına arıza geçmişi + bakım geçmişi + üretim yoğunluğu
verilerini analiz ederek arıza olasılığı ve optimum bakım zamanı tahmin eder.

Algoritma:
    - Yeterli veri varsa: scikit-learn RandomForestRegressor
    - Yetersiz veri: Gelişmiş kural tabanlı heuristik (fallback)

v2.0 Yenilikler:
    - Gerçek ML modeli (RandomForest)
    - Güven skoru (confidence_score)
    - Doğruluk raporu
    - Detaylı exception logging
    - Timezone tutarlılığı
"""

import logging
import traceback
from datetime import datetime, timedelta, timezone
from sqlalchemy import func

logger = logging.getLogger(__name__)


def _ensure_utc(dt):
    """Datetime nesnesinin UTC timezone'a sahip olmasını garantiler."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class KestirimciBakimServisi:
    """Makine arıza olasılığı ve bakım zamanlaması tahmini."""

    MODEL_VERSIYONU = 'v2.0-rf'
    MIN_EGITIM_VERISI = 30  # ML modeli için minimum kayıt

    def __init__(self):
        self._model = None
        self._model_accuracy = None

    def tum_makineleri_analiz_et(self):
        """Tüm aktif makineler için bakım tahmini yapar."""
        from app.models.makine import Makine
        sonuclar = []

        makineler = Makine.query.filter_by(aktif=True).all()
        for makine in makineler:
            try:
                tahmin = self._makine_analiz(makine)
                if tahmin:
                    sonuclar.append(tahmin)
            except Exception as e:
                logger.error(
                    f"Kestirimci bakım hatası — Makine {makine.id} ({makine.ad}): {e}",
                    exc_info=True
                )

        # Risk skoruna göre sırala (en riskli önce)
        sonuclar.sort(key=lambda x: x['risk_skoru'], reverse=True)
        return sonuclar

    def makine_tahmini(self, makine_id):
        """Tek makine için detaylı bakım tahmini."""
        from app.models.makine import Makine
        makine = Makine.query.get(makine_id)
        if not makine:
            return None
        return self._makine_analiz(makine)

    def dogruluk_raporu(self):
        """Geçmiş tahminleri gerçekleşenlerle karşılaştırarak doğruluk raporu üretir."""
        from app.models.tahmin import TahminKaydi
        from app.models.makine import ArizaKaydi

        tahminler = TahminKaydi.query.filter_by(
            tahmin_turu='bakim', aktif=False
        ).order_by(TahminKaydi.olusturma_tarihi.desc()).limit(200).all()

        if not tahminler:
            return {'toplam': 0, 'dogruluk': None, 'mesaj': 'Henüz yeterli geçmiş tahmin yok.'}

        dogru = 0
        toplam_degerli = 0

        for t in tahminler:
            if t.tahmin_tarihi is None:
                continue

            # Tahmin tarihinden ±7 gün içinde arıza olmuş mu?
            aralik_bas = t.tahmin_tarihi - timedelta(days=7)
            aralik_bit = t.tahmin_tarihi + timedelta(days=7)

            ariza_var = ArizaKaydi.query.filter(
                ArizaKaydi.makine_id == t.kaynak_id,
                func.date(ArizaKaydi.baslangic_zamani).between(aralik_bas, aralik_bit)
            ).first()

            toplam_degerli += 1
            risk = float(t.risk_skoru or 0)

            if risk >= 50 and ariza_var:
                dogru += 1  # Yüksek risk tahmin edilmiş, arıza olmuş
            elif risk < 50 and not ariza_var:
                dogru += 1  # Düşük risk tahmin edilmiş, arıza olmamış

        dogruluk = round((dogru / toplam_degerli) * 100, 1) if toplam_degerli > 0 else None

        return {
            'toplam': len(tahminler),
            'degerli': toplam_degerli,
            'dogru': dogru,
            'dogruluk': dogruluk,
            'model_versiyonu': self.MODEL_VERSIYONU
        }

    def _makine_analiz(self, makine):
        """Bir makine için bakım tahmini hesaplar."""
        from app.models.makine import UretimVerisi, ArizaKaydi, BakimKaydi, DurusKaydi
        from app.extensions import db

        bugun = datetime.now(timezone.utc).date()
        donem_baslangic = bugun - timedelta(days=180)

        # ── Veri Toplama ──
        son_bakim_gunu = self._son_bakim_gunu_hesapla(makine, bugun)
        bakim_oran = son_bakim_gunu / makine.periyodik_bakim_gun if makine.periyodik_bakim_gun else 1.0

        # Toplam arıza sayısı (son 180 gün)
        ariza_sayisi = ArizaKaydi.query.filter(
            ArizaKaydi.makine_id == makine.id,
            ArizaKaydi.baslangic_zamani >= datetime.combine(
                donem_baslangic, datetime.min.time()
            ).replace(tzinfo=timezone.utc)
        ).count()

        # Toplam çalışma saati (son 90 gün)
        toplam_calisma = db.session.query(
            func.sum(UretimVerisi.gercek_calisma_dk)
        ).filter(
            UretimVerisi.makine_id == makine.id,
            UretimVerisi.tarih >= bugun - timedelta(days=90)
        ).scalar() or 0
        toplam_calisma_saat = float(toplam_calisma) / 60

        # Toplam duruş süresi (son 90 gün)
        toplam_durus = db.session.query(
            func.sum(DurusKaydi.sure_dk)
        ).filter(
            DurusKaydi.makine_id == makine.id,
            DurusKaydi.baslangic >= datetime.combine(
                bugun - timedelta(days=90), datetime.min.time()
            ).replace(tzinfo=timezone.utc)
        ).scalar() or 0
        toplam_durus_saat = float(toplam_durus) / 60

        # Son arıza ne zaman oldu
        son_ariza_gunu = self._son_ariza_gunu_hesapla(makine)

        # MTBF hesaplama
        mtbf_gun = self._mtbf_hesapla(makine)

        # Ortalama OEE (son 30 gün)
        ort_oee = db.session.query(
            func.avg(UretimVerisi.oee_yuzde)
        ).filter(
            UretimVerisi.makine_id == makine.id,
            UretimVerisi.tarih >= bugun - timedelta(days=30)
        ).scalar()
        ort_oee = float(ort_oee) if ort_oee else 0

        # Makine yaşı (gün)
        makine_yasi = (bugun - makine.satin_alma_tarihi).days if makine.satin_alma_tarihi else 365

        # ── Feature vektörü ──
        features = {
            'son_bakim_gunu': son_bakim_gunu,
            'bakim_oran': round(bakim_oran, 4),
            'ariza_sayisi_180g': ariza_sayisi,
            'toplam_calisma_saat': round(toplam_calisma_saat, 2),
            'toplam_durus_saat': round(toplam_durus_saat, 2),
            'mtbf_gun': round(mtbf_gun, 1) if mtbf_gun < 999 else None,
            'ort_oee': round(ort_oee, 1),
            'son_ariza_gunu': son_ariza_gunu if son_ariza_gunu < 999 else None,
            'makine_yasi_gun': makine_yasi,
        }

        # ── Risk Skoru Hesaplama ──
        ml_kullanildi = False
        confidence = 0.0

        # ML modeli ile tahmin dene
        try:
            ml_sonuc = self._ml_risk_hesapla(features)
            if ml_sonuc is not None:
                risk_skoru = ml_sonuc['risk_skoru']
                confidence = ml_sonuc['confidence']
                ml_kullanildi = True
            else:
                risk_skoru = self._heuristik_risk_hesapla(
                    bakim_oran, ariza_sayisi, toplam_calisma_saat,
                    toplam_durus_saat, son_ariza_gunu, mtbf_gun,
                    ort_oee, makine.durum
                )
                confidence = 0.6  # Heuristik güven skoru
        except Exception as e:
            logger.warning(f"ML tahmin başarısız, heuristik kullanılıyor: {e}")
            risk_skoru = self._heuristik_risk_hesapla(
                bakim_oran, ariza_sayisi, toplam_calisma_saat,
                toplam_durus_saat, son_ariza_gunu, mtbf_gun,
                ort_oee, makine.durum
            )
            confidence = 0.6

        # Zaten arızalı ise doğrudan yüksek risk
        if makine.durum == 'arizali':
            risk_skoru = max(risk_skoru, 90)
            confidence = 1.0

        # ── Tahmini arıza zamanı ──
        if mtbf_gun < 999 and son_ariza_gunu < 999:
            tahmini_gun = max(1, int(mtbf_gun - son_ariza_gunu))
        else:
            kalan_bakim = makine.periyodik_bakim_gun - son_bakim_gunu if makine.periyodik_bakim_gun else 30
            tahmini_gun = max(1, kalan_bakim)

        # ── Öneri Oluşturma ──
        oneri = self._oneri_olustur(risk_skoru, tahmini_gun, bakim_oran, ariza_sayisi)

        model_ver = f"{self.MODEL_VERSIYONU}-ml" if ml_kullanildi else f"{self.MODEL_VERSIYONU}-heur"

        return {
            'makine_id': makine.id,
            'makine_ad': makine.ad,
            'makine_kod': makine.kod,
            'makine_durum': makine.durum,
            'risk_skoru': round(risk_skoru, 1),
            'confidence_score': round(confidence, 2),
            'tahmini_gun': tahmini_gun,
            'tahmin_tarihi': (bugun + timedelta(days=tahmini_gun)).isoformat(),
            'oneri': oneri,
            'detaylar': features,
            'model_versiyonu': model_ver,
            'ml_kullanildi': ml_kullanildi,
        }

    # ── Yardımcı Hesaplayıcılar ──

    def _son_bakim_gunu_hesapla(self, makine, bugun):
        """Son bakımdan bu yana geçen gün sayısını hesaplar."""
        if makine.son_bakim_tarihi:
            return (bugun - makine.son_bakim_tarihi).days
        if makine.satin_alma_tarihi:
            return (bugun - makine.satin_alma_tarihi).days
        return 180

    def _son_ariza_gunu_hesapla(self, makine):
        """Son arızadan bu yana geçen gün sayısını hesaplar."""
        from app.models.makine import ArizaKaydi
        son_ariza = ArizaKaydi.query.filter_by(makine_id=makine.id).order_by(
            ArizaKaydi.baslangic_zamani.desc()
        ).first()

        if not son_ariza or not son_ariza.baslangic_zamani:
            return 999

        b_zamani = _ensure_utc(son_ariza.baslangic_zamani)
        return (datetime.now(timezone.utc) - b_zamani).days

    def _mtbf_hesapla(self, makine):
        """Ortalama arızalar arası süre (MTBF) hesaplar."""
        from app.models.makine import ArizaKaydi
        arizalar = ArizaKaydi.query.filter(
            ArizaKaydi.makine_id == makine.id
        ).order_by(ArizaKaydi.baslangic_zamani.asc()).all()

        if len(arizalar) < 2:
            return 999

        aralarki_sureler = []
        for i in range(1, len(arizalar)):
            z1 = _ensure_utc(arizalar[i - 1].baslangic_zamani)
            z2 = _ensure_utc(arizalar[i].baslangic_zamani)
            if z1 and z2:
                fark = (z2 - z1).days
                if fark > 0:
                    aralarki_sureler.append(fark)

        if aralarki_sureler:
            return sum(aralarki_sureler) / len(aralarki_sureler)
        return 999

    # ── ML Modeli ──

    def _ml_risk_hesapla(self, features):
        """scikit-learn RandomForestRegressor ile risk skoru hesaplar."""
        try:
            import numpy as np
            from sklearn.ensemble import RandomForestRegressor

            # Eğitim verisi topla
            egitim_verisi = self._egitim_verisi_topla()
            if len(egitim_verisi) < self.MIN_EGITIM_VERISI:
                return None  # Yetersiz veri, heuristik'e düş

            X = np.array([v['features'] for v in egitim_verisi])
            y = np.array([v['label'] for v in egitim_verisi])

            # Model eğit
            model = RandomForestRegressor(
                n_estimators=50,
                max_depth=8,
                min_samples_split=5,
                random_state=42,
                n_jobs=1
            )
            model.fit(X, y)

            # Tahmin yap
            feature_vector = np.array([[
                features['son_bakim_gunu'],
                features['bakim_oran'],
                features['ariza_sayisi_180g'],
                features['toplam_calisma_saat'],
                features['toplam_durus_saat'],
                features['mtbf_gun'] if features['mtbf_gun'] is not None else 999,
                features['ort_oee'],
                features['son_ariza_gunu'] if features['son_ariza_gunu'] is not None else 999,
                features['makine_yasi_gun'],
            ]])

            prediction = model.predict(feature_vector)[0]
            risk_skoru = float(max(0, min(100, prediction)))

            # Confidence: ağaçların tahmin varyansından
            tree_predictions = np.array([
                tree.predict(feature_vector)[0] for tree in model.estimators_
            ])
            std_dev = np.std(tree_predictions)
            max_range = 100.0
            confidence = max(0.3, min(1.0, 1.0 - (std_dev / max_range * 2)))

            return {
                'risk_skoru': risk_skoru,
                'confidence': confidence,
            }

        except ImportError:
            logger.warning("scikit-learn yüklü değil, heuristik kullanılacak.")
            return None
        except Exception as e:
            logger.warning(f"ML modeli çalıştırılamadı: {e}")
            return None

    def _egitim_verisi_topla(self):
        """Geçmiş makine verilerinden ML eğitim seti oluşturur."""
        from app.models.makine import Makine, UretimVerisi, ArizaKaydi, DurusKaydi
        from app.extensions import db

        bugun = datetime.now(timezone.utc).date()
        egitim = []

        makineler = Makine.query.filter_by(aktif=True).all()

        for makine in makineler:
            # Son 12 ay boyunca her ay için bir kayıt oluştur
            for ay_offset in range(1, 13):
                nokta_tarihi = bugun - timedelta(days=30 * ay_offset)
                donem_bas = nokta_tarihi - timedelta(days=180)
                donem_90 = nokta_tarihi - timedelta(days=90)

                # O noktadaki arıza sayısı
                ariza_s = ArizaKaydi.query.filter(
                    ArizaKaydi.makine_id == makine.id,
                    ArizaKaydi.baslangic_zamani >= datetime.combine(
                        donem_bas, datetime.min.time()
                    ).replace(tzinfo=timezone.utc),
                    ArizaKaydi.baslangic_zamani <= datetime.combine(
                        nokta_tarihi, datetime.max.time()
                    ).replace(tzinfo=timezone.utc)
                ).count()

                # O noktadaki OEE
                ort_oee = db.session.query(
                    func.avg(UretimVerisi.oee_yuzde)
                ).filter(
                    UretimVerisi.makine_id == makine.id,
                    UretimVerisi.tarih.between(nokta_tarihi - timedelta(days=30), nokta_tarihi)
                ).scalar()
                ort_oee = float(ort_oee) if ort_oee else 50.0

                # Çalışma saati
                calisma = db.session.query(
                    func.sum(UretimVerisi.gercek_calisma_dk)
                ).filter(
                    UretimVerisi.makine_id == makine.id,
                    UretimVerisi.tarih.between(donem_90, nokta_tarihi)
                ).scalar() or 0
                calisma_saat = float(calisma) / 60

                # Duruş saati
                durus = db.session.query(
                    func.sum(DurusKaydi.sure_dk)
                ).filter(
                    DurusKaydi.makine_id == makine.id,
                    DurusKaydi.baslangic >= datetime.combine(
                        donem_90, datetime.min.time()
                    ).replace(tzinfo=timezone.utc),
                    DurusKaydi.baslangic <= datetime.combine(
                        nokta_tarihi, datetime.max.time()
                    ).replace(tzinfo=timezone.utc)
                ).scalar() or 0
                durus_saat = float(durus) / 60

                # Label: sonraki 30 gün içinde arıza oldu mu?
                gelecek_ariza = ArizaKaydi.query.filter(
                    ArizaKaydi.makine_id == makine.id,
                    ArizaKaydi.baslangic_zamani >= datetime.combine(
                        nokta_tarihi, datetime.min.time()
                    ).replace(tzinfo=timezone.utc),
                    ArizaKaydi.baslangic_zamani <= datetime.combine(
                        nokta_tarihi + timedelta(days=30), datetime.max.time()
                    ).replace(tzinfo=timezone.utc)
                ).count()

                # Risk label: 0-100 arasında
                if gelecek_ariza >= 3:
                    label = 90.0
                elif gelecek_ariza == 2:
                    label = 70.0
                elif gelecek_ariza == 1:
                    label = 50.0
                else:
                    label = 10.0 + (ariza_s * 5)  # Geçmişe göre hafif risk

                label = min(label, 100.0)

                son_bakim_g = 90  # Tahmini
                bakim_oran = son_bakim_g / (makine.periyodik_bakim_gun or 90)
                makine_yasi = (nokta_tarihi - makine.satin_alma_tarihi).days if makine.satin_alma_tarihi else 365

                egitim.append({
                    'features': [
                        son_bakim_g, bakim_oran, ariza_s,
                        calisma_saat, durus_saat,
                        999, ort_oee, 999, makine_yasi
                    ],
                    'label': label
                })

        return egitim

    # ── Heuristik Fallback ──

    def _heuristik_risk_hesapla(self, bakim_oran, ariza_sayisi, toplam_calisma_saat,
                                 toplam_durus_saat, son_ariza_gunu, mtbf_gun,
                                 ort_oee, makine_durumu):
        """
        Gelişmiş çoklu faktör bazlı risk skoru hesaplama (0-100).

        Ağırlıklar:
            - Bakım gecikme oranı: %30
            - Arıza sıklığı: %25
            - OEE düşüklüğü: %15
            - Duruş oranı: %15
            - MTBF yakınlık: %15
        """
        risk = 0

        # 1) Bakım gecikme oranı (%30)
        if bakim_oran >= 1.5:
            risk += 30
        elif bakim_oran >= 1.0:
            risk += 25
        elif bakim_oran >= 0.8:
            risk += 15
        elif bakim_oran >= 0.6:
            risk += 8

        # 2) Arıza sıklığı (%25)
        if ariza_sayisi >= 5:
            risk += 25
        elif ariza_sayisi >= 3:
            risk += 18
        elif ariza_sayisi >= 2:
            risk += 12
        elif ariza_sayisi >= 1:
            risk += 6

        # 3) OEE düşüklüğü (%15)
        if ort_oee > 0:
            if ort_oee < 50:
                risk += 15
            elif ort_oee < 65:
                risk += 10
            elif ort_oee < 75:
                risk += 5

        # 4) Duruş oranı (%15)
        if toplam_calisma_saat > 0:
            durus_orani = toplam_durus_saat / toplam_calisma_saat
            if durus_orani > 0.3:
                risk += 15
            elif durus_orani > 0.2:
                risk += 10
            elif durus_orani > 0.1:
                risk += 5

        # 5) MTBF yakınlık (%15)
        if mtbf_gun < 999 and son_ariza_gunu < 999:
            mtbf_oran = son_ariza_gunu / mtbf_gun if mtbf_gun > 0 else 1.0
            if mtbf_oran >= 1.0:
                risk += 15
            elif mtbf_oran >= 0.8:
                risk += 10
            elif mtbf_oran >= 0.6:
                risk += 5

        return min(risk, 100)

    def _oneri_olustur(self, risk_skoru, tahmini_gun, bakim_oran, ariza_sayisi):
        """Risk skoruna göre bakım önerisi oluşturur."""
        if risk_skoru >= 75:
            return (f"⚠️ KRİTİK: Bu makine {tahmini_gun} gün içinde arıza riski taşıyor. "
                    f"Acil bakım planlanmalıdır. Son dönemde {ariza_sayisi} arıza kaydı bulunuyor.")
        elif risk_skoru >= 50:
            return (f"⚡ YÜKSEK RİSK: Bakım periyodu {int(bakim_oran * 100)}% dolulukta. "
                    f"Önümüzdeki {tahmini_gun} gün içinde bakım planlanması önerilir.")
        elif risk_skoru >= 25:
            return (f"📋 ORTA RİSK: Makine genel olarak stabil ancak bakım yaklaşıyor. "
                    f"Tahmini {tahmini_gun} gün sonrası için bakım planlanabilir.")
        else:
            return (f"✅ DÜŞÜK RİSK: Makine sağlıklı durumda. "
                    f"Bir sonraki bakım tahminen {tahmini_gun} gün sonra gerekecek.")


kestirimci_bakim_servisi = KestirimciBakimServisi()
