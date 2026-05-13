"""
FDYS — Karşılaştırmalı Analiz Servisi v2.0
Kategori 4.2 — Gelişmiş Analitik

v2.0 Yenilikler:
    - Radar chart veri yapısı (7 eksenli)
    - Değişim yüzdesine renk kodu
    - Vardiya kapasite kullanım oranı
    - "En İyi/En Kötü" vurgulama
"""
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from app.extensions import db
from app.models.makine import Makine, UretimVerisi, ArizaKaydi, BakimKaydi, DurusKaydi
from app.models.enerji import EnerjiTuketimi
from app.models.kalite import HataKaydi
from app.models.isg import IsKazasi

logger = logging.getLogger(__name__)


class KarsilastirmaServisi:
    """Makine vs Makine, Dönem vs Dönem, Vardiya vs Vardiya karşılaştırmaları."""

    # Radar chart metrikleri (0-100 normalize)
    RADAR_METRIKLERI = ['ort_oee', 'verimlilik', 'kalite', 'guvenilirlik', 'enerji_verimlilik', 'bakim_verimlilik', 'kapasite_kullanim']

    def _makine_metrikleri(self, makine_id, bas, bit):
        """Tek makine için dönem metriklerini hesaplar."""
        m = Makine.query.get(makine_id)
        if not m:
            return None
        ort_oee = db.session.query(func.avg(UretimVerisi.oee_yuzde))\
            .filter(UretimVerisi.makine_id == makine_id, UretimVerisi.tarih.between(bas, bit)).scalar() or 0
        toplam_uretim = db.session.query(func.sum(UretimVerisi.gercek_uretim))\
            .filter(UretimVerisi.makine_id == makine_id, UretimVerisi.tarih.between(bas, bit)).scalar() or 0
        toplam_hata = db.session.query(func.sum(UretimVerisi.hatali_uretim))\
            .filter(UretimVerisi.makine_id == makine_id, UretimVerisi.tarih.between(bas, bit)).scalar() or 0
        ariza = ArizaKaydi.query.filter(
            ArizaKaydi.makine_id == makine_id,
            ArizaKaydi.baslangic_zamani.between(datetime.combine(bas, datetime.min.time()),
                                                 datetime.combine(bit, datetime.max.time()))
        ).count()
        durus_dk = db.session.query(func.sum(DurusKaydi.sure_dk))\
            .filter(DurusKaydi.makine_id == makine_id, DurusKaydi.baslangic.between(
                datetime.combine(bas, datetime.min.time()), datetime.combine(bit, datetime.max.time()))).scalar() or 0
        bakim_mal = db.session.query(func.sum(BakimKaydi.maliyet))\
            .filter(BakimKaydi.makine_id == makine_id, BakimKaydi.tarih.between(bas, bit)).scalar() or 0
        enerji = db.session.query(func.sum(EnerjiTuketimi.toplam_maliyet))\
            .filter(EnerjiTuketimi.makine_id == makine_id, EnerjiTuketimi.donem_baslangic >= bas,
                    EnerjiTuketimi.donem_bitis <= bit).scalar() or 0
        # Kapasite kullanım oranı
        toplam_plan = db.session.query(func.sum(UretimVerisi.planlanan_sure_dk))\
            .filter(UretimVerisi.makine_id == makine_id, UretimVerisi.tarih.between(bas, bit)).scalar() or 0
        toplam_ger = db.session.query(func.sum(UretimVerisi.gercek_calisma_dk))\
            .filter(UretimVerisi.makine_id == makine_id, UretimVerisi.tarih.between(bas, bit)).scalar() or 0

        uretim_int = int(toplam_uretim)
        hata_int = int(toplam_hata)
        hata_oran = round((hata_int / uretim_int) * 100, 2) if uretim_int > 0 else 0
        kapasite_kullanim = round((int(toplam_ger) / int(toplam_plan)) * 100, 1) if int(toplam_plan) > 0 else 0

        return {
            'makine_id': m.id, 'makine_ad': m.ad, 'makine_kod': m.kod,
            'ort_oee': round(float(ort_oee), 1), 'toplam_uretim': uretim_int,
            'hata_orani': hata_oran, 'ariza_sayisi': ariza,
            'durus_dk': int(durus_dk), 'bakim_maliyeti': round(float(bakim_mal), 2),
            'enerji_maliyeti': round(float(enerji), 2),
            'kapasite_kullanim': kapasite_kullanim,
        }

    def makine_karsilastir(self, m1_id, m2_id, bas=None, bit=None):
        """İki makineyi yan yana karşılaştırır + radar chart verisi."""
        bugun = datetime.now(timezone.utc).date()
        bas = bas or (bugun - timedelta(days=30))
        bit = bit or bugun
        met1 = self._makine_metrikleri(m1_id, bas, bit)
        met2 = self._makine_metrikleri(m2_id, bas, bit)
        if not met1 or not met2:
            return None

        # Günlük OEE trend
        trend = db.session.query(UretimVerisi.tarih, UretimVerisi.makine_id,
                                  func.avg(UretimVerisi.oee_yuzde).label('oee'))\
            .filter(UretimVerisi.makine_id.in_([m1_id, m2_id]), UretimVerisi.tarih.between(bas, bit))\
            .group_by(UretimVerisi.tarih, UretimVerisi.makine_id)\
            .order_by(UretimVerisi.tarih).all()

        tarihler = sorted(set(t.tarih for t in trend))
        m1_trend = {t.tarih: round(float(t.oee), 1) for t in trend if t.makine_id == m1_id}
        m2_trend = {t.tarih: round(float(t.oee), 1) for t in trend if t.makine_id == m2_id}

        # Kazanan hesabı + metrik bazlı vurgulama
        karsilastirma_sonuclari = []
        skor1 = skor2 = 0
        for k in ['ort_oee', 'toplam_uretim', 'kapasite_kullanim']:
            if met1[k] > met2[k]:
                skor1 += 1
                kazanan = 1
            elif met2[k] > met1[k]:
                skor2 += 1
                kazanan = 2
            else:
                kazanan = 0
            karsilastirma_sonuclari.append({'metrik': k, 'kazanan': kazanan})

        for k in ['hata_orani', 'ariza_sayisi', 'durus_dk', 'bakim_maliyeti', 'enerji_maliyeti']:
            if met1[k] < met2[k]:
                skor1 += 1
                kazanan = 1
            elif met2[k] < met1[k]:
                skor2 += 1
                kazanan = 2
            else:
                kazanan = 0
            karsilastirma_sonuclari.append({'metrik': k, 'kazanan': kazanan})

        # Radar chart verisi (0-100 normalize)
        radar = self._radar_chart_verisi(met1, met2)

        return {
            'makine1': met1, 'makine2': met2,
            'trend_labels': [t.strftime('%d.%m') for t in tarihler],
            'trend_m1': [m1_trend.get(t, None) for t in tarihler],
            'trend_m2': [m2_trend.get(t, None) for t in tarihler],
            'kazanan': 1 if skor1 > skor2 else (2 if skor2 > skor1 else 0),
            'skor': [skor1, skor2],
            'karsilastirma_detay': karsilastirma_sonuclari,
            'radar': radar,
            'donem': f"{bas.strftime('%d.%m.%Y')} — {bit.strftime('%d.%m.%Y')}"
        }

    def _radar_chart_verisi(self, met1, met2):
        """Radar chart için 7 eksenli normalize veri üretir (0-100)."""
        labels = ['OEE', 'Verimlilik', 'Kalite', 'Güvenilirlik', 'Enerji Verim.', 'Bakım Verim.', 'Kap. Kullanım']

        def normalize(val, max_val, ters=False):
            if max_val == 0:
                return 50
            n = min(val / max_val * 100, 100) if not ters else max(0, 100 - (val / max_val * 100))
            return round(n, 1)

        max_uretim = max(met1['toplam_uretim'], met2['toplam_uretim'], 1)
        max_ariza = max(met1['ariza_sayisi'], met2['ariza_sayisi'], 1)
        max_bakim = max(met1['bakim_maliyeti'], met2['bakim_maliyeti'], 1)
        max_enerji = max(met1['enerji_maliyeti'], met2['enerji_maliyeti'], 1)

        m1_values = [
            met1['ort_oee'],
            normalize(met1['toplam_uretim'], max_uretim),
            max(0, 100 - met1['hata_orani'] * 10),
            normalize(met1['ariza_sayisi'], max_ariza, ters=True),
            normalize(met1['enerji_maliyeti'], max_enerji, ters=True),
            normalize(met1['bakim_maliyeti'], max_bakim, ters=True),
            met1['kapasite_kullanim'],
        ]
        m2_values = [
            met2['ort_oee'],
            normalize(met2['toplam_uretim'], max_uretim),
            max(0, 100 - met2['hata_orani'] * 10),
            normalize(met2['ariza_sayisi'], max_ariza, ters=True),
            normalize(met2['enerji_maliyeti'], max_enerji, ters=True),
            normalize(met2['bakim_maliyeti'], max_bakim, ters=True),
            met2['kapasite_kullanim'],
        ]

        return {
            'labels': labels,
            'makine1': [round(v, 1) for v in m1_values],
            'makine2': [round(v, 1) for v in m2_values],
        }

    def _donem_metrikleri(self, bas, bit):
        """Bir dönem için fabrika geneli metrikleri hesaplar."""
        bas_dt = datetime.combine(bas, datetime.min.time())
        bit_dt = datetime.combine(bit, datetime.max.time())
        ort_oee = db.session.query(func.avg(UretimVerisi.oee_yuzde))\
            .filter(UretimVerisi.tarih.between(bas, bit)).scalar() or 0
        toplam_ur = db.session.query(func.sum(UretimVerisi.gercek_uretim))\
            .filter(UretimVerisi.tarih.between(bas, bit)).scalar() or 0
        toplam_ht = db.session.query(func.sum(UretimVerisi.hatali_uretim))\
            .filter(UretimVerisi.tarih.between(bas, bit)).scalar() or 0
        ariza = ArizaKaydi.query.filter(ArizaKaydi.baslangic_zamani.between(bas_dt, bit_dt)).count()
        enerji = db.session.query(func.sum(EnerjiTuketimi.toplam_maliyet))\
            .filter(EnerjiTuketimi.donem_baslangic >= bas, EnerjiTuketimi.donem_bitis <= bit).scalar() or 0
        kaza = IsKazasi.query.filter(IsKazasi.tarih.between(bas_dt, bit_dt), IsKazasi.ramak_kala == False).count()
        uretim_int = int(toplam_ur)
        hata_int = int(toplam_ht)
        return {
            'ort_oee': round(float(ort_oee), 1),
            'toplam_uretim': uretim_int,
            'hata_orani': round((hata_int / uretim_int) * 100, 2) if uretim_int > 0 else 0,
            'ariza_sayisi': ariza, 'enerji_maliyeti': round(float(enerji), 2),
            'kaza_sayisi': kaza, 'etiket': f"{bas.strftime('%d.%m')} — {bit.strftime('%d.%m.%Y')}"
        }

    def donem_karsilastir(self, d1_bas, d1_bit, d2_bas, d2_bit):
        """İki dönemi karşılaştırır + değişim renk kodu."""
        m1 = self._donem_metrikleri(d1_bas, d1_bit)
        m2 = self._donem_metrikleri(d2_bas, d2_bit)
        degisimler = {}

        # Yükselmesi iyi olan metrikler
        yukari_iyi = {'ort_oee', 'toplam_uretim'}

        for k in ['ort_oee', 'toplam_uretim', 'hata_orani', 'ariza_sayisi', 'enerji_maliyeti', 'kaza_sayisi']:
            eski = m1[k] or 0
            yeni = m2[k] or 0
            if eski > 0:
                yuzde = round(((yeni - eski) / eski) * 100, 1)
            else:
                yuzde = 100.0 if yeni > 0 else 0.0

            # Renk kodu belirleme
            if k in yukari_iyi:
                renk = 'success' if yuzde > 0 else ('danger' if yuzde < 0 else 'secondary')
            else:
                renk = 'success' if yuzde < 0 else ('danger' if yuzde > 0 else 'secondary')

            degisimler[k] = {
                'yuzde': yuzde,
                'renk': renk,
                'yon': 'yukari' if yuzde > 0 else ('asagi' if yuzde < 0 else 'stabil')
            }

        return {'donem1': m1, 'donem2': m2, 'degisimler': degisimler}

    def vardiya_karsilastir(self, gun=30):
        """Sabah/Öğleden sonra/Gece vardiya performans karşılaştırması + kapasite kullanım."""
        bas = datetime.now(timezone.utc).date() - timedelta(days=gun)
        vardiyalar_db = ['sabah', 'ogleden_sonra', 'gece']
        vardiya_adlari = {'sabah': 'Sabah', 'ogleden_sonra': 'Öğleden Sonra', 'gece': 'Gece'}
        sonuclar = []

        for v in vardiyalar_db:
            ort_oee = db.session.query(func.avg(UretimVerisi.oee_yuzde))\
                .filter(UretimVerisi.vardiya == v, UretimVerisi.tarih >= bas).scalar() or 0
            toplam_ur = db.session.query(func.sum(UretimVerisi.gercek_uretim))\
                .filter(UretimVerisi.vardiya == v, UretimVerisi.tarih >= bas).scalar() or 0
            toplam_ht = db.session.query(func.sum(UretimVerisi.hatali_uretim))\
                .filter(UretimVerisi.vardiya == v, UretimVerisi.tarih >= bas).scalar() or 0
            toplam_plan = db.session.query(func.sum(UretimVerisi.planlanan_sure_dk))\
                .filter(UretimVerisi.vardiya == v, UretimVerisi.tarih >= bas).scalar() or 1
            toplam_ger = db.session.query(func.sum(UretimVerisi.gercek_calisma_dk))\
                .filter(UretimVerisi.vardiya == v, UretimVerisi.tarih >= bas).scalar() or 0

            uretim_int = int(toplam_ur)
            hata_int = int(toplam_ht)
            plan_int = int(toplam_plan)
            ger_int = int(toplam_ger)

            durus_yuzde = round(((plan_int - ger_int) / plan_int) * 100, 1) if plan_int > 0 else 0
            kapasite_kullanim = round((ger_int / plan_int) * 100, 1) if plan_int > 0 else 0

            sonuclar.append({
                'vardiya': v, 'ad': vardiya_adlari[v],
                'ort_oee': round(float(ort_oee), 1), 'toplam_uretim': uretim_int,
                'hata_orani': round((hata_int / uretim_int) * 100, 2) if uretim_int > 0 else 0,
                'durus_yuzde': durus_yuzde,
                'kapasite_kullanim': kapasite_kullanim,
            })

        # En iyi/en kötü vurgulama
        if sonuclar:
            en_iyi_oee = max(sonuclar, key=lambda x: x['ort_oee'])['vardiya']
            en_kotu_oee = min(sonuclar, key=lambda x: x['ort_oee'])['vardiya']
            for s in sonuclar:
                s['en_iyi'] = s['vardiya'] == en_iyi_oee
                s['en_kotu'] = s['vardiya'] == en_kotu_oee

        return sonuclar


karsilastirma_servisi = KarsilastirmaServisi()
