"""
FDYS — Enerji Maliyet Analizi Servisi (Faz 3)
"""

from datetime import datetime, timedelta
from sqlalchemy import func


class MaliyetAnalizi:
    """Enerji maliyet hesaplama ve projeksiyon motoru."""

    def aylik_maliyet(self, enerji_turu, miktar, birim_fiyat):
        """Aylık enerji maliyetini hesaplar."""
        return round(float(miktar) * float(birim_fiyat), 2)

    def tur_bazli_ozet(self):
        """Enerji türü bazlı tüketim ve maliyet özetini döner."""
        from app.extensions import db
        from app.models.enerji import EnerjiTuketimi

        sonuclar = db.session.query(
            EnerjiTuketimi.enerji_turu,
            func.sum(EnerjiTuketimi.miktar),
            func.sum(EnerjiTuketimi.toplam_maliyet),
            func.count(EnerjiTuketimi.id)
        ).group_by(EnerjiTuketimi.enerji_turu).all()

        ozet = {}
        for tur, miktar, maliyet, kayit_sayisi in sonuclar:
            ozet[tur] = {
                'miktar': float(miktar) if miktar else 0,
                'maliyet': float(maliyet) if maliyet else 0,
                'kayit_sayisi': kayit_sayisi
            }
        return ozet

    def yillik_projeksiyon(self, aylik_veriler):
        """Mevcut trende göre yıllık maliyet tahmini yapar."""
        if not aylik_veriler:
            return 0
        ortalama_aylik = sum(aylik_veriler) / len(aylik_veriler)
        return round(ortalama_aylik * 12, 2)


maliyet_analizi = MaliyetAnalizi()
