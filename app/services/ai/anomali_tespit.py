"""
FDYS — Anomali Tespiti Servisi v2.0
Kategori 1.4 — AI Tahminleme Motoru

Enerji tüketimi ve kalite verilerinde anormal sapmaları tespit eder.
Z-Score ve IQR tabanlı istatistiksel anomali algılama kullanır.

v2.0 Yenilikler:
    - Yapılandırılabilir Z-score eşiği
    - Sliding window (7 gün) anomali tespiti
    - False positive filtreleme (aynı kaynak/gün tekrarı yok)
    - Anomali geçmişi karşılaştırması
    - Doğru quartile hesaplama (interpolasyonlu)
    - Sıfır üretim günü filtreleme
    - Detaylı logging
"""

import logging
import math
from datetime import datetime, timedelta, timezone
from sqlalchemy import func

logger = logging.getLogger(__name__)


class AnomaliTespitServisi:
    """Enerji ve kalite anomalisi tespiti servisi."""

    MODEL_VERSIYONU = 'v2.0-zscore'
    DEFAULT_Z_ESIK = 2.0
    SLIDING_WINDOW_GUN = 7

    def __init__(self, z_esik=None):
        self.z_esik = z_esik or self.DEFAULT_Z_ESIK

    def tum_anomalileri_tespit_et(self, z_esik=None):
        """Tüm modüllerde anomali taraması yapar."""
        esik = z_esik or self.z_esik

        enerji_anomalileri = self._enerji_anomali_tara(esik)
        kalite_anomalileri = self._kalite_anomali_tara()

        tum = enerji_anomalileri + kalite_anomalileri

        # False positive filtreleme: aynı kaynaktan aynı gün tekrar anomali raporlama
        tum = self._false_positive_filtrele(tum)

        tum.sort(key=lambda x: x['risk_skoru'], reverse=True)
        return tum

    def enerji_anomalileri(self, z_esik=None):
        """Sadece enerji anomalilerini döner."""
        esik = z_esik or self.z_esik
        return self._enerji_anomali_tara(esik)

    def kalite_anomalileri(self):
        """Sadece kalite anomalilerini döner."""
        return self._kalite_anomali_tara()

    def _false_positive_filtrele(self, anomaliler):
        """Aynı kaynaktan aynı gün birden fazla anomali raporlanmasını engeller."""
        gorulmus = set()
        filtrelenmis = []

        for a in anomaliler:
            anahtar = f"{a['tip']}_{a['kaynak_id']}_{a['tarih']}"
            if anahtar not in gorulmus:
                gorulmus.add(anahtar)
                filtrelenmis.append(a)
            else:
                logger.debug(f"False positive filtrelendi: {anahtar}")

        return filtrelenmis

    def _enerji_anomali_tara(self, z_esik):
        """Makine bazlı enerji tüketiminde anomali tarar (sliding window)."""
        from app.models.enerji import EnerjiTuketimi
        from app.models.makine import Makine

        bugun = datetime.now(timezone.utc).date()
        donem_basi = bugun - timedelta(days=90)
        anomaliler = []

        makineler = Makine.query.filter_by(aktif=True).all()

        for makine in makineler:
            try:
                enerji_verileri = EnerjiTuketimi.query.filter(
                    EnerjiTuketimi.makine_id == makine.id,
                    EnerjiTuketimi.donem_baslangic >= donem_basi
                ).order_by(EnerjiTuketimi.donem_baslangic).all()

                if len(enerji_verileri) < 5:
                    continue

                degerler = [float(e.miktar) for e in enerji_verileri]
                tarihler = [e.donem_baslangic for e in enerji_verileri]

                # Global istatistikler
                ortalama = sum(degerler) / len(degerler)
                varyans = sum((x - ortalama) ** 2 for x in degerler) / len(degerler)
                std_sapma = math.sqrt(varyans) if varyans > 0 else 0

                if std_sapma == 0:
                    continue

                # Sliding window ile son 7 kayıt için anomali kontrolü
                window_start = max(0, len(degerler) - self.SLIDING_WINDOW_GUN)

                for i in range(window_start, len(degerler)):
                    deger = degerler[i]
                    tarih = tarihler[i]
                    z_score = abs(deger - ortalama) / std_sapma

                    if z_score >= z_esik:
                        sapma_yuzde = round(((deger - ortalama) / ortalama) * 100, 1) if ortalama != 0 else 0
                        yuksek_mi = deger > ortalama

                        # Geçmiş anomali kontrolü
                        gecmis_benzer = self._gecmis_anomali_kontrol(
                            'enerji', makine.id, deger, ortalama
                        )

                        anomaliler.append({
                            'tip': 'enerji',
                            'kaynak_turu': 'makine',
                            'kaynak_id': makine.id,
                            'kaynak_adi': makine.ad,
                            'baslik': f"{'Yüksek' if yuksek_mi else 'Düşük'} Enerji Tüketimi — {makine.ad}",
                            'aciklama': (
                                f"{makine.ad} normalde ortalama {ortalama:.1f} {enerji_verileri[i].birim} "
                                f"tüketirken, {tarih.strftime('%d.%m.%Y')} tarihinde {deger:.1f} {enerji_verileri[i].birim} "
                                f"tüketim kaydedildi (sapma: %{sapma_yuzde})."
                            ),
                            'tarih': tarih.isoformat(),
                            'deger': round(deger, 1),
                            'ortalama': round(ortalama, 1),
                            'sapma_yuzde': sapma_yuzde,
                            'z_score': round(z_score, 2),
                            'risk_skoru': min(100, round(z_score * 25, 1)),
                            'birim': enerji_verileri[i].birim,
                            'gecmis_benzer': gecmis_benzer,
                            'model_versiyonu': self.MODEL_VERSIYONU
                        })
            except Exception as e:
                logger.error(
                    f"Enerji anomali tarama hatası — Makine {makine.id}: {e}",
                    exc_info=True
                )

        return anomaliler

    def _kalite_anomali_tara(self):
        """Vardiya bazlı hata oranlarında anomali tarar."""
        from app.models.makine import UretimVerisi
        from app.extensions import db

        bugun = datetime.now(timezone.utc).date()
        donem_basi = bugun - timedelta(days=60)
        anomaliler = []

        try:
            vardiya_hatalari = db.session.query(
                UretimVerisi.vardiya,
                func.date(UretimVerisi.tarih).label('tarih'),
                func.sum(UretimVerisi.hatali_uretim).label('hatali'),
                func.sum(UretimVerisi.gercek_uretim).label('toplam')
            ).filter(
                UretimVerisi.tarih >= donem_basi,
                UretimVerisi.gercek_uretim > 0
            ).group_by(UretimVerisi.vardiya, func.date(UretimVerisi.tarih)).all()

            if len(vardiya_hatalari) < 5:
                return anomaliler

            # Hata oranlarını hesapla (sıfır üretim günlerini filtrele)
            hata_oranlari = []
            for vh in vardiya_hatalari:
                hatali = float(vh.hatali or 0)
                toplam = float(vh.toplam or 0)
                if toplam <= 0:
                    continue  # Sıfır üretim günü atla
                oran = (hatali / toplam) * 100
                hata_oranlari.append({
                    'vardiya': vh.vardiya,
                    'tarih': vh.tarih,
                    'oran': oran,
                    'hatali': hatali,
                    'toplam': toplam
                })

            if len(hata_oranlari) < 5:
                return anomaliler

            # Doğru quartile hesaplama (interpolasyonlu)
            oranlar = sorted([h['oran'] for h in hata_oranlari])
            q1 = self._percentile(oranlar, 25)
            q3 = self._percentile(oranlar, 75)
            iqr = q3 - q1
            ust_sinir = q3 + 1.5 * iqr
            ortalama = sum(oranlar) / len(oranlar)

            for h in hata_oranlari:
                if h['oran'] > ust_sinir and h['oran'] > 0:
                    sapma_yuzde = round(
                        ((h['oran'] - ortalama) / ortalama) * 100, 1
                    ) if ortalama > 0 else 0

                    vardiya_label = h['vardiya'].replace('_', ' ').title() if h['vardiya'] else 'Bilinmeyen'

                    gecmis_benzer = self._gecmis_anomali_kontrol(
                        'kalite', 0, h['oran'], ortalama
                    )

                    anomaliler.append({
                        'tip': 'kalite',
                        'kaynak_turu': 'uretim',
                        'kaynak_id': 0,
                        'kaynak_adi': vardiya_label,
                        'baslik': f"Yüksek Hata Oranı — {vardiya_label} Vardiyası",
                        'aciklama': (
                            f"{h['tarih']} tarihinde {vardiya_label} vardiyasında hata oranı "
                            f"%{h['oran']:.1f} olarak kaydedildi. Normal üst sınır: %{ust_sinir:.1f}. "
                            f"({int(h['hatali'])} hatalı / {int(h['toplam'])} toplam üretim)"
                        ),
                        'tarih': str(h['tarih']),
                        'deger': round(h['oran'], 1),
                        'ortalama': round(ortalama, 1),
                        'sapma_yuzde': sapma_yuzde,
                        'z_score': 0,
                        'risk_skoru': min(100, round(h['oran'] * 5, 1)),
                        'birim': '%',
                        'gecmis_benzer': gecmis_benzer,
                        'model_versiyonu': self.MODEL_VERSIYONU
                    })
        except Exception as e:
            logger.error(f"Kalite anomali tarama hatası: {e}", exc_info=True)

        return anomaliler

    def _percentile(self, sorted_data, percentile):
        """Doğru percentile hesaplama (linear interpolasyon ile)."""
        if not sorted_data:
            return 0
        n = len(sorted_data)
        k = (n - 1) * (percentile / 100.0)
        f = int(k)
        c = f + 1 if f + 1 < n else f
        d = k - f
        return sorted_data[f] + d * (sorted_data[c] - sorted_data[f])

    def _gecmis_anomali_kontrol(self, tip, kaynak_id, deger, ortalama):
        """Bu anomalinin daha önce de yaşanıp yaşanmadığını kontrol eder."""
        try:
            from app.models.tahmin import TahminKaydi
            import json

            gecmis = TahminKaydi.query.filter_by(
                tahmin_turu='anomali',
                kaynak_id=kaynak_id,
                aktif=False
            ).order_by(TahminKaydi.olusturma_tarihi.desc()).limit(50).all()

            benzer_sayisi = 0
            for t in gecmis:
                meta = t.meta
                if meta and meta.get('tip') == tip:
                    gecmis_sapma = meta.get('sapma_yuzde', 0)
                    mevcut_sapma = ((deger - ortalama) / ortalama * 100) if ortalama > 0 else 0
                    # Aynı yönde sapma varsa benzer kabul et
                    if (gecmis_sapma > 0 and mevcut_sapma > 0) or (gecmis_sapma < 0 and mevcut_sapma < 0):
                        benzer_sayisi += 1

            if benzer_sayisi > 0:
                return {
                    'tekrar': True,
                    'sayisi': benzer_sayisi,
                    'mesaj': f"Bu anomali daha önce {benzer_sayisi} kez yaşanmış."
                }
            return {'tekrar': False, 'sayisi': 0, 'mesaj': 'İlk kez tespit edildi.'}

        except Exception as e:
            logger.warning(f"Geçmiş anomali kontrolü başarısız: {e}")
            return {'tekrar': False, 'sayisi': 0, 'mesaj': 'Geçmiş kontrol edilemedi.'}


anomali_tespit_servisi = AnomaliTespitServisi()
