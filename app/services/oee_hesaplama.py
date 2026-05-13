"""
FDYS — OEE Hesaplama Motoru

OEE = Kullanılabilirlik × Performans × Kalite

Kullanılabilirlik = Gerçek çalışma süresi / Planlanan çalışma süresi
Performans = Gerçek üretim / (Teorik kapasite × Gerçek çalışma saat)
Kalite = (Toplam üretim - Hatalı üretim) / Toplam üretim
"""


class OEEHesaplama:
    """OEE formül motoru."""

    @staticmethod
    def hesapla(planlanan_dk, gercek_dk, gercek_uretim, hatali_uretim, teorik_kapasite):
        """
        Tek vardiya OEE hesabı yapar.

        Returns:
            dict: kullanilabilirlik, performans, kalite, oee yüzdeleri
        """
        if planlanan_dk == 0 or teorik_kapasite == 0 or gercek_dk == 0:
            return {'kullanilabilirlik': 0, 'performans': 0, 'kalite': 0, 'oee': 0}

        kullanilabilirlik = gercek_dk / planlanan_dk
        performans = gercek_uretim / (teorik_kapasite * (gercek_dk / 60))
        kalite = (gercek_uretim - hatali_uretim) / gercek_uretim if gercek_uretim > 0 else 0

        oee = kullanilabilirlik * performans * kalite

        return {
            'kullanilabilirlik': round(kullanilabilirlik * 100, 2),
            'performans': round(performans * 100, 2),
            'kalite': round(kalite * 100, 2),
            'oee': round(min(oee * 100, 100), 2)
        }

    @staticmethod
    def degerlendir(oee_yuzde, hedef=85.0):
        """OEE değerini yorumlar ve renk kodu döner."""
        if oee_yuzde >= hedef:
            return {'durum': 'İyi', 'renk': 'yesil'}
        elif oee_yuzde >= hedef * 0.9:
            return {'durum': 'Uyarı', 'renk': 'sari'}
        else:
            return {'durum': 'Kritik', 'renk': 'kirmizi'}


oee_hesaplama = OEEHesaplama()
