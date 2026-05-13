"""
FDYS — KPI Hedef Yönetimi Servisi v2.0
Kategori 4.3 — Gelişmiş Analitik

v2.0 Yenilikler:
    - KPI trend hesaplama (önceki aya göre iyileşme/kötüleşme)
    - KPI hedef kaçırıldığında bildirim tetikleme
    - Yıllık 12 aylık hedef vs gerçekleşen serisi
    - Fabrika Sağlık Skoru (0-100 ağırlıklı toplam)
"""
import logging
from datetime import datetime, timedelta, timezone
from calendar import monthrange
from sqlalchemy import func
from app.extensions import db
from app.models.analitik import KpiHedef
from app.models.makine import UretimVerisi, ArizaKaydi, BakimKaydi
from app.models.kalite import HataKaydi
from app.models.enerji import EnerjiTuketimi
from app.models.isg import IsKazasi
from app.models.stok import Malzeme
from app.models.personel import IzinTalebi

logger = logging.getLogger(__name__)

# KPI ağırlıkları (Fabrika Sağlık Skoru için)
KPI_AGIRLIKLARI = {
    'makine.ort_oee': 25,
    'kalite.hata_orani': 20,
    'makine.ariza_sayisi': 15,
    'enerji.toplam_maliyet': 10,
    'isg.kaza_sayisi': 15,
    'stok.kritik_malzeme': 10,
    'personel.devamsizlik': 5,
}


class KpiServisi:
    """KPI hedef tanımlama, gerçekleşen hesaplama ve dashboard özeti."""

    def gerceklesen_hesapla(self, modul, kpi_kodu, yil, ay=None):
        """Modül ve KPI koduna göre gerçekleşen değeri veritabanından hesaplar."""
        if ay:
            bas = datetime(yil, ay, 1).date()
            _, son_gun = monthrange(yil, ay)
            bit = datetime(yil, ay, son_gun).date()
        else:
            bas = datetime(yil, 1, 1).date()
            bit = datetime(yil, 12, 31).date()

        hesapla = getattr(self, f'_hesapla_{modul}_{kpi_kodu}', None)
        if hesapla:
            return hesapla(bas, bit)
        return None

    # ── Makine KPI Hesaplayıcıları ──
    def _hesapla_makine_ort_oee(self, bas, bit):
        val = db.session.query(func.avg(UretimVerisi.oee_yuzde))\
            .filter(UretimVerisi.tarih.between(bas, bit)).scalar()
        return round(float(val), 1) if val else 0

    def _hesapla_makine_ariza_sayisi(self, bas, bit):
        return ArizaKaydi.query.filter(
            ArizaKaydi.baslangic_zamani.between(
                datetime.combine(bas, datetime.min.time()),
                datetime.combine(bit, datetime.max.time())
            )).count()

    def _hesapla_makine_bakim_maliyeti(self, bas, bit):
        val = db.session.query(func.sum(BakimKaydi.maliyet))\
            .filter(BakimKaydi.tarih.between(bas, bit)).scalar()
        return round(float(val), 2) if val else 0

    # ── Kalite KPI Hesaplayıcıları ──
    def _hesapla_kalite_hata_orani(self, bas, bit):
        toplam = db.session.query(func.sum(UretimVerisi.gercek_uretim))\
            .filter(UretimVerisi.tarih.between(bas, bit)).scalar() or 1
        hatali = db.session.query(func.sum(UretimVerisi.hatali_uretim))\
            .filter(UretimVerisi.tarih.between(bas, bit)).scalar() or 0
        return round((int(hatali) / int(toplam)) * 100, 2) if int(toplam) > 0 else 0

    def _hesapla_kalite_fire_orani(self, bas, bit):
        val = db.session.query(func.avg(HataKaydi.fire_orani))\
            .filter(HataKaydi.tarih.between(
                datetime.combine(bas, datetime.min.time()),
                datetime.combine(bit, datetime.max.time()))).scalar()
        return round(float(val), 2) if val else 0

    # ── Enerji KPI Hesaplayıcıları ──
    def _hesapla_enerji_toplam_maliyet(self, bas, bit):
        val = db.session.query(func.sum(EnerjiTuketimi.toplam_maliyet))\
            .filter(EnerjiTuketimi.donem_baslangic >= bas, EnerjiTuketimi.donem_bitis <= bit).scalar()
        return round(float(val), 2) if val else 0

    def _hesapla_enerji_birim_tuketim(self, bas, bit):
        enerji = db.session.query(func.sum(EnerjiTuketimi.miktar))\
            .filter(EnerjiTuketimi.enerji_turu == 'elektrik',
                    EnerjiTuketimi.donem_baslangic >= bas, EnerjiTuketimi.donem_bitis <= bit).scalar() or 0
        uretim = db.session.query(func.sum(UretimVerisi.gercek_uretim))\
            .filter(UretimVerisi.tarih.between(bas, bit)).scalar() or 1
        return round(float(enerji) / int(uretim), 3) if int(uretim) > 0 else 0

    # ── İSG KPI Hesaplayıcıları ──
    def _hesapla_isg_kaza_sayisi(self, bas, bit):
        return IsKazasi.query.filter(
            IsKazasi.tarih.between(datetime.combine(bas, datetime.min.time()),
                                   datetime.combine(bit, datetime.max.time())),
            IsKazasi.ramak_kala == False).count()

    def _hesapla_isg_kayip_gun(self, bas, bit):
        val = db.session.query(func.sum(IsKazasi.kayip_gun))\
            .filter(IsKazasi.tarih.between(datetime.combine(bas, datetime.min.time()),
                                            datetime.combine(bit, datetime.max.time())),
                    IsKazasi.ramak_kala == False).scalar()
        return int(val) if val else 0

    # ── Stok KPI ──
    def _hesapla_stok_kritik_malzeme(self, bas, bit):
        return Malzeme.query.filter(Malzeme.mevcut_miktar <= Malzeme.minimum_stok, Malzeme.aktif == True).count()

    # ── Personel KPI ──
    def _hesapla_personel_devamsizlik(self, bas, bit):
        izin_gun = db.session.query(func.count(IzinTalebi.id))\
            .filter(IzinTalebi.durum == 'onaylandi',
                    IzinTalebi.baslangic_tarihi >= bas, IzinTalebi.bitis_tarihi <= bit).scalar() or 0
        return int(izin_gun)

    def kpi_dashboard_ozeti(self, yil=None, ay=None):
        """Tüm aktif KPI hedeflerini gerçekleşen ile karşılaştırır + trend bilgisi."""
        if yil is None:
            yil = datetime.now(timezone.utc).year
        if ay is None:
            ay = datetime.now(timezone.utc).month

        hedefler = KpiHedef.query.filter_by(aktif=True, yil=yil).all()
        hedefler = [h for h in hedefler if h.ay is None or h.ay == ay]

        # Önceki ay verileri (trend için)
        onceki_ay = ay - 1 if ay > 1 else 12
        onceki_yil = yil if ay > 1 else yil - 1

        sonuclar = []
        for h in hedefler:
            gerceklesen = self.gerceklesen_hesapla(h.modul, h.kpi_kodu, yil, ay if h.periyot == 'aylik' else None)
            durum = h.hedef_durumu(gerceklesen)
            tutma = h.tutma_yuzde(gerceklesen)

            # Trend hesaplama (önceki aya göre)
            onceki_gerceklesen = None
            trend = None
            trend_yon = 'stabil'
            try:
                onceki_gerceklesen = self.gerceklesen_hesapla(
                    h.modul, h.kpi_kodu, onceki_yil, onceki_ay if h.periyot == 'aylik' else None
                )
                if onceki_gerceklesen is not None and gerceklesen is not None:
                    if onceki_gerceklesen > 0:
                        trend = round(((gerceklesen - onceki_gerceklesen) / onceki_gerceklesen) * 100, 1)
                    elif gerceklesen > 0:
                        trend = 100.0
                    else:
                        trend = 0.0

                    if h.yonu == 'yukari':
                        trend_yon = 'iyilesiyor' if trend and trend > 0 else ('kotulesme' if trend and trend < 0 else 'stabil')
                    else:
                        trend_yon = 'iyilesiyor' if trend and trend < 0 else ('kotulesme' if trend and trend > 0 else 'stabil')
            except Exception as e:
                logger.warning(f"KPI trend hesaplama hatası ({h.kpi_kodu}): {e}")

            sonuclar.append({
                'id': h.id, 'modul': h.modul, 'modul_adi': h.modul_adi,
                'kpi_adi': h.kpi_adi, 'kpi_kodu': h.kpi_kodu,
                'birim': h.birim, 'hedef': float(h.hedef_deger),
                'gerceklesen': gerceklesen, 'durum': durum,
                'tutma_yuzde': tutma, 'yonu': h.yonu, 'periyot_adi': h.periyot_adi,
                'trend': trend,
                'trend_yon': trend_yon,
                'onceki_gerceklesen': onceki_gerceklesen,
            })

        return sonuclar

    def yillik_kpi_serisi(self, modul, kpi_kodu, yil):
        """12 aylık hedef vs gerçekleşen serisi (grafik için)."""
        aylar = []
        for ay in range(1, 13):
            gerceklesen = self.gerceklesen_hesapla(modul, kpi_kodu, yil, ay)

            # O aya ait hedef
            hedef_kayit = KpiHedef.query.filter_by(
                modul=modul, kpi_kodu=kpi_kodu, yil=yil, aktif=True
            ).first()
            hedef_deger = float(hedef_kayit.hedef_deger) if hedef_kayit else None

            aylar.append({
                'ay': ay,
                'ay_adi': ['', 'Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz',
                           'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara'][ay],
                'hedef': hedef_deger,
                'gerceklesen': gerceklesen,
            })

        return aylar

    def fabrika_saglik_skoru(self, yil=None, ay=None):
        """
        Fabrika geneli tek bir sağlık skoru (0-100).
        Tüm KPI'ların ağırlıklı ortalaması.
        """
        if yil is None:
            yil = datetime.now(timezone.utc).year
        if ay is None:
            ay = datetime.now(timezone.utc).month

        kpi_ozet = self.kpi_dashboard_ozeti(yil, ay)
        if not kpi_ozet:
            return {'skor': None, 'mesaj': 'Yeterli KPI verisi yok.'}

        toplam_agirlik = 0
        toplam_puan = 0

        for kpi in kpi_ozet:
            anahtar = f"{kpi['modul']}.{kpi['kpi_kodu']}"
            agirlik = KPI_AGIRLIKLARI.get(anahtar, 5)

            tutma = kpi.get('tutma_yuzde', 0) or 0
            # 0-100 arasına normalize et
            puan = min(max(tutma, 0), 100)

            toplam_agirlik += agirlik
            toplam_puan += puan * agirlik

        skor = round(toplam_puan / toplam_agirlik, 1) if toplam_agirlik > 0 else 0

        # Skor yorumu
        if skor >= 85:
            seviye = 'mukemmel'
            renk = 'success'
            mesaj = 'Fabrika mükemmel performans gösteriyor.'
        elif skor >= 70:
            seviye = 'iyi'
            renk = 'primary'
            mesaj = 'Fabrika performansı iyi, küçük iyileştirmeler mümkün.'
        elif skor >= 50:
            seviye = 'orta'
            renk = 'warning'
            mesaj = 'Bazı alanlarda iyileştirme gerekiyor.'
        else:
            seviye = 'kritik'
            renk = 'danger'
            mesaj = 'Fabrika performansı kritik seviyede. Acil aksiyon gerekiyor.'

        return {
            'skor': skor,
            'seviye': seviye,
            'renk': renk,
            'mesaj': mesaj,
            'kpi_sayisi': len(kpi_ozet),
            'donem': f"{ay}/{yil}"
        }

    def kpi_bildirim_kontrol(self, yil=None, ay=None):
        """Hedef kaçırılan KPI'lar için bildirim tetikler."""
        try:
            kpi_ozet = self.kpi_dashboard_ozeti(yil, ay)
            kritik_kpiler = [k for k in kpi_ozet if k['durum'] == 'kritik']

            if not kritik_kpiler:
                return 0

            from app.services.bildirim_motoru import bildirim_motoru
            from app.models.kullanici import Kullanici

            yoneticiler = Kullanici.query.filter_by(rol='yonetici', aktif=True).all()
            bildirim_sayisi = 0

            for kpi in kritik_kpiler:
                for y in yoneticiler:
                    bildirim_motoru.bildirim_olustur(
                        kullanici_id=y.id,
                        baslik=f"📊 KPI Hedef Kaçırıldı: {kpi['kpi_adi']}",
                        mesaj=(f"{kpi['modul_adi']} — {kpi['kpi_adi']}: "
                               f"Hedef {kpi['hedef']}{kpi['birim']}, "
                               f"Gerçekleşen {kpi['gerceklesen']}{kpi['birim']}"),
                        seviye='uyari',
                        modul='analitik',
                        url='/analitik/#kpi'
                    )
                    bildirim_sayisi += 1

            return bildirim_sayisi
        except Exception as e:
            logger.error(f"KPI bildirim hatası: {e}", exc_info=True)
            return 0


kpi_servisi = KpiServisi()
