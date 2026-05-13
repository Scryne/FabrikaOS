"""
FDYS — Maliyet Merkezi Analiz Servisi v2.0
Kategori 4.4 — Gelişmiş Analitik

v2.0 Yenilikler:
    - Amortisman yöntemi seçimi (doğrusal/azalan bakiye)
    - Makine yaşam sonu tahmini
    - Karşılaştırmalı maliyet tablosu
    - Dolaylı maliyet tahmini (operatör maaş payı)
"""
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from app.extensions import db
from app.models.makine import Makine, UretimVerisi, BakimKaydi, DurusKaydi
from app.models.enerji import EnerjiTuketimi

logger = logging.getLogger(__name__)


class MaliyetServisi:
    """Makine TCO, birim üretim maliyeti ve ROI hesaplamaları."""

    def makine_tco(self, makine_id):
        """Makine Toplam Sahip Olma Maliyeti (TCO) hesaplar."""
        m = Makine.query.get(makine_id)
        if not m:
            return None

        satin_alma = float(m.satin_alma_fiyati or 0)
        bakim = db.session.query(func.sum(BakimKaydi.maliyet))\
            .filter(BakimKaydi.makine_id == makine_id).scalar() or 0
        enerji = db.session.query(func.sum(EnerjiTuketimi.toplam_maliyet))\
            .filter(EnerjiTuketimi.makine_id == makine_id).scalar() or 0

        # Duruş kayıp maliyeti tahmini
        durus_dk = db.session.query(func.sum(DurusKaydi.sure_dk))\
            .filter(DurusKaydi.makine_id == makine_id).scalar() or 0
        birim_fiyat = float(m.birim_satis_fiyati or 0)
        durus_kaybi = round(
            (int(durus_dk) / 60) * m.teorik_kapasite * birim_fiyat, 2
        ) if birim_fiyat > 0 and m.teorik_kapasite else 0

        bakim_f = round(float(bakim), 2)
        enerji_f = round(float(enerji), 2)
        toplam = round(satin_alma + bakim_f + enerji_f + durus_kaybi, 2)

        # Günlük ortalama
        if m.satin_alma_tarihi:
            gun_sayisi = max((datetime.now(timezone.utc).date() - m.satin_alma_tarihi).days, 1)
        else:
            gun_sayisi = 365
        gunluk_ort = round(toplam / gun_sayisi, 2)

        # Yaşam sonu tahmini
        yasam_sonu = self._yasam_sonu_tahmini(m, bakim_f, enerji_f, gun_sayisi)

        return {
            'makine_id': m.id, 'makine_ad': m.ad, 'makine_kod': m.kod,
            'satin_alma': satin_alma, 'bakim': bakim_f, 'enerji': enerji_f,
            'durus_kaybi': durus_kaybi, 'toplam_tco': toplam, 'gunluk_ort': gunluk_ort,
            'yasam_sonu': yasam_sonu,
            'dagilim': [
                {'kategori': 'Satın Alma', 'tutar': satin_alma, 'renk': '#3b82f6'},
                {'kategori': 'Bakım', 'tutar': bakim_f, 'renk': '#f59e0b'},
                {'kategori': 'Enerji', 'tutar': enerji_f, 'renk': '#10b981'},
                {'kategori': 'Duruş Kaybı', 'tutar': durus_kaybi, 'renk': '#ef4444'},
            ]
        }

    def _yasam_sonu_tahmini(self, makine, bakim_maliyeti, enerji_maliyeti, gun_sayisi):
        """Makine yaşam sonu tahmini: bakım maliyeti trendi baz alınarak."""
        satin_alma = float(makine.satin_alma_fiyati or 0)
        if satin_alma <= 0 or gun_sayisi <= 0:
            return None

        # Yıllık bakım maliyeti
        yillik_bakim = (bakim_maliyeti / gun_sayisi) * 365

        # Bakım maliyeti satın alma bedelinin %60'ını aştığında değiştirmek mantıklı
        esik = satin_alma * 0.6
        if yillik_bakim <= 0:
            return {'yil': None, 'mesaj': 'Bakım verisi yetersiz.'}

        kalan_yil = round((esik - bakim_maliyeti) / yillik_bakim, 1) if yillik_bakim > 0 else None
        if kalan_yil is not None and kalan_yil > 0:
            return {
                'kalan_yil': kalan_yil,
                'mesaj': f'Tahmini {kalan_yil} yıl sonra değiştirme değerlendirmesi önerilir.',
                'seviye': 'info' if kalan_yil > 3 else ('warning' if kalan_yil > 1 else 'danger')
            }
        elif kalan_yil is not None:
            return {
                'kalan_yil': 0,
                'mesaj': 'Bakım maliyetleri satın alma bedelinin %60\'ını aşmış. Değiştirme değerlendirilmeli.',
                'seviye': 'danger'
            }
        return None

    def tum_makineler_birim_maliyet(self, gun=30):
        """Tüm makineler için birim üretim maliyeti hesaplar (dolaylı maliyet dahil)."""
        bas = datetime.now(timezone.utc).date() - timedelta(days=gun)
        makineler = Makine.query.filter_by(aktif=True).all()
        sonuclar = []

        for m in makineler:
            uretim = db.session.query(func.sum(UretimVerisi.gercek_uretim))\
                .filter(UretimVerisi.makine_id == m.id, UretimVerisi.tarih >= bas).scalar() or 0
            bakim = db.session.query(func.sum(BakimKaydi.maliyet))\
                .filter(BakimKaydi.makine_id == m.id, BakimKaydi.tarih >= bas).scalar() or 0
            enerji = db.session.query(func.sum(EnerjiTuketimi.toplam_maliyet))\
                .filter(EnerjiTuketimi.makine_id == m.id, EnerjiTuketimi.donem_baslangic >= bas).scalar() or 0

            dogrudan_maliyet = float(bakim or 0) + float(enerji or 0)

            # Dolaylı maliyet tahmini (operatör maaş payı: çalışma saati bazlı)
            calisma_dk = db.session.query(func.sum(UretimVerisi.gercek_calisma_dk))\
                .filter(UretimVerisi.makine_id == m.id, UretimVerisi.tarih >= bas).scalar() or 0
            # Tahmini operatör saat ücreti: 150 TL/saat
            dolayli_maliyet = round((float(calisma_dk) / 60) * 150, 2)

            toplam_mal = dogrudan_maliyet + dolayli_maliyet
            uretim_int = int(uretim)
            birim = round(toplam_mal / uretim_int, 2) if uretim_int > 0 else 0
            birim_dogrudan = round(dogrudan_maliyet / uretim_int, 2) if uretim_int > 0 else 0

            sonuclar.append({
                'makine_id': m.id, 'makine_ad': m.ad, 'makine_kod': m.kod,
                'dogrudan_maliyet': round(dogrudan_maliyet, 2),
                'dolayli_maliyet': round(dolayli_maliyet, 2),
                'toplam_maliyet': round(toplam_mal, 2),
                'toplam_uretim': uretim_int,
                'birim_maliyet': birim,
                'birim_dogrudan_maliyet': birim_dogrudan,
            })

        sonuclar.sort(key=lambda x: x['birim_maliyet'])
        return sonuclar

    def makine_roi(self, makine_id, amortisman_yontemi='dogrusal'):
        """
        Makine yatırım geri dönüş (ROI) analizi.
        amortisman_yontemi: 'dogrusal' veya 'azalan_bakiye'
        """
        m = Makine.query.get(makine_id)
        if not m or not m.satin_alma_fiyati:
            return None

        satin_alma = float(m.satin_alma_fiyati)
        birim_fiyat = float(m.birim_satis_fiyati or 0)

        # Toplam üretim geliri
        toplam_uretim = db.session.query(func.sum(UretimVerisi.gercek_uretim))\
            .filter(UretimVerisi.makine_id == makine_id).scalar() or 0
        hatali = db.session.query(func.sum(UretimVerisi.hatali_uretim))\
            .filter(UretimVerisi.makine_id == makine_id).scalar() or 0
        iyi_uretim = int(toplam_uretim) - int(hatali)
        gelir = round(iyi_uretim * birim_fiyat, 2) if birim_fiyat > 0 else 0

        # Toplam maliyet
        tco = self.makine_tco(makine_id)
        toplam_maliyet = tco['toplam_tco'] if tco else satin_alma

        # ROI
        roi = round(((gelir - toplam_maliyet) / satin_alma) * 100, 1) if satin_alma > 0 else 0

        # Makine yaşı
        if m.satin_alma_tarihi:
            gun_sayisi = max((datetime.now(timezone.utc).date() - m.satin_alma_tarihi).days, 1)
        else:
            gun_sayisi = 365

        gunluk_gelir = gelir / gun_sayisi if gun_sayisi > 0 else 0
        amortisman_gun = round(satin_alma / gunluk_gelir) if gunluk_gelir > 0 else None

        # Amortisman hesabı
        amortisman = self._amortisman_hesapla(satin_alma, gun_sayisi, amortisman_yontemi)

        return {
            'makine_id': m.id, 'makine_ad': m.ad, 'makine_kod': m.kod,
            'satin_alma': satin_alma, 'toplam_gelir': gelir,
            'toplam_maliyet': toplam_maliyet, 'roi_yuzde': roi,
            'iyi_uretim': iyi_uretim, 'birim_fiyat': birim_fiyat,
            'amortisman_gun': amortisman_gun,
            'yillik_getiri_tahmini': round(gunluk_gelir * 365, 2),
            'amortisman': amortisman,
        }

    def _amortisman_hesapla(self, satin_alma, gun_sayisi, yontem='dogrusal', faydali_omur_yil=10):
        """Amortisman hesabı (doğrusal veya azalan bakiye)."""
        yil_sayisi = gun_sayisi / 365.0

        if yontem == 'dogrusal':
            yillik_amor = satin_alma / faydali_omur_yil
            toplam_amor = min(yillik_amor * yil_sayisi, satin_alma)
            kalan_deger = max(satin_alma - toplam_amor, 0)
        elif yontem == 'azalan_bakiye':
            oran = 2.0 / faydali_omur_yil  # Çift azalan bakiye
            kalan_deger = satin_alma
            for _ in range(int(yil_sayisi)):
                kalan_deger -= kalan_deger * oran
            kalan_deger = max(kalan_deger, 0)
            toplam_amor = satin_alma - kalan_deger
            yillik_amor = toplam_amor / max(yil_sayisi, 1)
        else:
            return None

        return {
            'yontem': yontem,
            'faydali_omur_yil': faydali_omur_yil,
            'yillik_amortisman': round(yillik_amor, 2),
            'toplam_amortisman': round(toplam_amor, 2),
            'kalan_defter_degeri': round(kalan_deger, 2),
            'amortisman_yuzde': round((toplam_amor / satin_alma) * 100, 1) if satin_alma > 0 else 0,
        }

    def tum_makineler_tco_karsilastirma(self):
        """Tüm makinelerin TCO'sunu karşılaştırmalı tablo olarak döner."""
        makineler = Makine.query.filter_by(aktif=True).all()
        sonuclar = []
        for m in makineler:
            try:
                tco = self.makine_tco(m.id)
                if tco:
                    sonuclar.append(tco)
            except Exception as e:
                logger.error(f"TCO hesaplama hatası — Makine {m.id}: {e}", exc_info=True)

        sonuclar.sort(key=lambda x: x['toplam_tco'], reverse=True)
        return sonuclar


maliyet_servisi = MaliyetServisi()
