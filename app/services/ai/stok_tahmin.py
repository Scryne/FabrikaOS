"""
FDYS — Stok Tükenme Tahmini Servisi v2.0
Kategori 1.3 — AI Tahminleme Motoru

Son 60 günlük stok çıkış hareketlerinden günlük tüketim hızını hesaplayarak
malzeme bazlı tükenme zamanı ve sipariş önerisi üretir.

v2.0 Yenilikler:
    - Haftalık tüketim profili (haftaiçi/sonu ayrımı)
    - Spike detection (ani tüketim artışı)
    - Emniyet stoğu (safety stock) hesabı
    - Kategori bazlı dinamik teslimat süresi
    - Tedarikçi güvenilirlik skoru
    - Detaylı logging
"""

import logging
import math
from datetime import datetime, timedelta, timezone
from sqlalchemy import func

logger = logging.getLogger(__name__)


class StokTahminServisi:
    """Stok tükenme tahmini ve sipariş zamanı önerisi servisi."""

    MODEL_VERSIYONU = 'v2.0-adv'
    ANALIZ_DONEM_GUN = 60

    # Kategori bazlı varsayılan teslimat süreleri
    KATEGORI_TESLIMAT = {
        'elektronik': 14,
        'mekanik': 7,
        'sarf': 3,
        'kimyasal': 10,
        'yedek_parca': 14,
        'hammadde': 5,
    }

    def tum_malzemeleri_analiz_et(self):
        """Tüm aktif malzemeler için tükenme tahmini yapar."""
        from app.models.stok import Malzeme
        sonuclar = []

        malzemeler = Malzeme.query.filter_by(aktif=True).all()
        for malzeme in malzemeler:
            try:
                tahmin = self._malzeme_analiz(malzeme)
                if tahmin:
                    sonuclar.append(tahmin)
            except Exception as e:
                logger.error(
                    f"Stok tahmin hatası — Malzeme {malzeme.id} ({malzeme.ad}): {e}",
                    exc_info=True
                )

        # Tükenme gününe göre sırala (en yakın önce)
        sonuclar.sort(key=lambda x: x['tukenme_gun'] if x['tukenme_gun'] is not None else 9999)
        return sonuclar

    def malzeme_tahmini(self, malzeme_id):
        """Tek malzeme için stok tükenme tahmini."""
        from app.models.stok import Malzeme
        malzeme = Malzeme.query.get(malzeme_id)
        if not malzeme:
            return None
        return self._malzeme_analiz(malzeme)

    def _malzeme_analiz(self, malzeme):
        """Bir malzeme için tükenme tahmini hesaplar."""
        from app.models.stok import StokHareketi
        from app.extensions import db

        bugun = datetime.now(timezone.utc)
        donem_basi = bugun - timedelta(days=self.ANALIZ_DONEM_GUN)

        # Son 60 günlük çıkış hareketleri
        cikislar = db.session.query(
            func.date(StokHareketi.tarih),
            func.sum(StokHareketi.miktar)
        ).filter(
            StokHareketi.malzeme_id == malzeme.id,
            StokHareketi.hareket_turu == 'cikis',
            StokHareketi.tarih >= donem_basi
        ).group_by(func.date(StokHareketi.tarih)).all()

        mevcut = float(malzeme.mevcut_miktar or 0)
        minimum = float(malzeme.minimum_stok or 0)
        teslimat_gun = self._teslimat_gun(malzeme)

        if not cikislar:
            return {
                'malzeme_id': malzeme.id,
                'malzeme_ad': malzeme.ad,
                'malzeme_kod': malzeme.kod,
                'birim': malzeme.birim,
                'mevcut_miktar': mevcut,
                'minimum_stok': minimum,
                'gunluk_tuketim': 0,
                'haftalik_profil': None,
                'tukenme_gun': None,
                'tukenme_tarihi': None,
                'siparis_zamani': None,
                'siparis_miktari_onerisi': None,
                'emniyet_stoku': 0,
                'teslimat_gun': teslimat_gun,
                'risk_skoru': 5 if mevcut > minimum else 40,
                'oneri': '📦 Son 60 günde tüketim kaydı yok. Stok stabil.',
                'kritik_mi': mevcut <= minimum,
                'spike_tespit': False,
                'model_versiyonu': self.MODEL_VERSIYONU
            }

        # Günlük ve haftalık tüketim analizi
        toplam_tuketim = sum(float(c[1]) for c in cikislar)
        gunluk_ortalama = toplam_tuketim / self.ANALIZ_DONEM_GUN
        gunluk_degerler = [float(c[1]) for c in cikislar]

        # Haftalık tüketim profili
        haftalik_profil = self._haftalik_profil_hesapla(cikislar)

        # Spike detection
        spike_var = self._spike_tespit(gunluk_degerler)

        # Standart sapma (emniyet stoğu hesabı için)
        if len(gunluk_degerler) > 1:
            mean = sum(gunluk_degerler) / len(gunluk_degerler)
            variance = sum((x - mean) ** 2 for x in gunluk_degerler) / (len(gunluk_degerler) - 1)
            std_dev = math.sqrt(variance)
        else:
            std_dev = gunluk_ortalama * 0.3

        # Emniyet stoğu = Z * sigma_d * sqrt(L)
        # Z=1.65 (%95 servis seviyesi), sigma_d=günlük std sapma, L=teslimat süresi
        emniyet_stoku = round(1.65 * std_dev * math.sqrt(teslimat_gun), 1)

        # Tükenme tahmini
        if gunluk_ortalama > 0:
            tukenme_gun = int(mevcut / gunluk_ortalama)
            minimum_altina_dusme_gun = int((mevcut - minimum) / gunluk_ortalama) if mevcut > minimum else 0
        else:
            tukenme_gun = None
            minimum_altina_dusme_gun = None

        # Sipariş zamanı önerisi
        siparis_zamani = None
        siparis_gun = None
        if tukenme_gun is not None:
            siparis_gun = tukenme_gun - teslimat_gun
            if siparis_gun <= 0:
                siparis_zamani = "🔴 ACİL: Şimdi sipariş verin! Teslimat süresi stok tükenme tarihini aşıyor."
            elif siparis_gun <= 3:
                siparis_zamani = f"🟡 YAKIN: {siparis_gun} gün içinde sipariş verilmeli."
            elif siparis_gun <= 7:
                siparis_zamani = f"🟢 PLANLI: {siparis_gun} gün içinde sipariş verilebilir."
            else:
                siparis_zamani = f"✅ RAHAT: Sipariş için {siparis_gun} gün süre var."

        # Sipariş miktarı önerisi (EOQ benzeri basit hesap)
        siparis_miktari = None
        if gunluk_ortalama > 0:
            # 30 günlük tüketim + emniyet stoğu
            siparis_miktari = round(gunluk_ortalama * 30 + emniyet_stoku, 0)

        # Risk skoru
        risk_skoru = self._hesapla_risk(mevcut, minimum, tukenme_gun, teslimat_gun, siparis_gun, spike_var)

        # Öneri
        oneri = self._oneri_olustur(mevcut, minimum, tukenme_gun, teslimat_gun, gunluk_ortalama, spike_var)

        tukenme_tarihi = None
        if tukenme_gun is not None:
            tukenme_tarihi = (bugun.date() + timedelta(days=tukenme_gun)).isoformat()

        return {
            'malzeme_id': malzeme.id,
            'malzeme_ad': malzeme.ad,
            'malzeme_kod': malzeme.kod,
            'birim': malzeme.birim,
            'mevcut_miktar': round(mevcut, 1),
            'minimum_stok': round(minimum, 1),
            'gunluk_tuketim': round(gunluk_ortalama, 2),
            'haftalik_profil': haftalik_profil,
            'tukenme_gun': tukenme_gun,
            'tukenme_tarihi': tukenme_tarihi,
            'minimum_altina_dusme_gun': minimum_altina_dusme_gun,
            'siparis_zamani': siparis_zamani,
            'siparis_miktari_onerisi': siparis_miktari,
            'emniyet_stoku': emniyet_stoku,
            'teslimat_gun': teslimat_gun,
            'risk_skoru': round(risk_skoru, 1),
            'oneri': oneri,
            'kritik_mi': mevcut <= minimum,
            'spike_tespit': spike_var,
            'model_versiyonu': self.MODEL_VERSIYONU
        }

    def _haftalik_profil_hesapla(self, cikislar):
        """Haftanın günlerine göre tüketim profili çıkarır."""
        gun_toplam = {i: 0 for i in range(7)}
        gun_sayisi = {i: 0 for i in range(7)}
        gun_adlari = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz']

        for tarih_str, miktar in cikislar:
            try:
                if isinstance(tarih_str, str):
                    tarih = datetime.strptime(tarih_str, '%Y-%m-%d').date()
                else:
                    tarih = tarih_str
                gun_idx = tarih.weekday()
                gun_toplam[gun_idx] += float(miktar)
                gun_sayisi[gun_idx] += 1
            except (ValueError, TypeError):
                continue

        profil = {}
        for i in range(7):
            ort = round(gun_toplam[i] / gun_sayisi[i], 2) if gun_sayisi[i] > 0 else 0
            profil[gun_adlari[i]] = ort

        return profil

    def _spike_tespit(self, degerler):
        """Ani tüketim artışı (spike) tespit eder. Z-score > 2.5 ise spike."""
        if len(degerler) < 5:
            return False

        mean = sum(degerler) / len(degerler)
        if mean == 0:
            return False

        variance = sum((x - mean) ** 2 for x in degerler) / len(degerler)
        std = math.sqrt(variance) if variance > 0 else 0

        if std == 0:
            return False

        for d in degerler[-5:]:  # Son 5 gün
            z = abs(d - mean) / std
            if z > 2.5:
                return True

        return False

    def _teslimat_gun(self, malzeme):
        """Tedarikçi ortalama teslimat süresini döner, kategori bazlı fallback ile."""
        if malzeme.tedarikci and malzeme.tedarikci.ortalama_teslimat_gun:
            return malzeme.tedarikci.ortalama_teslimat_gun

        # Kategori bazlı dinamik teslimat süresi
        kategori = getattr(malzeme, 'kategori', None)
        if kategori:
            kategori_lower = kategori.lower().strip()
            for key, gun in self.KATEGORI_TESLIMAT.items():
                if key in kategori_lower:
                    return gun

        return 7  # Genel varsayılan

    def _hesapla_risk(self, mevcut, minimum, tukenme_gun, teslimat_gun, siparis_gun, spike_var):
        """Stok tükenme risk skoru (0-100)."""
        risk = 0

        # Zaten kritik seviyede mi
        if mevcut <= minimum:
            risk += 40
        elif mevcut <= minimum * 1.5:
            risk += 20

        # Tükenme zamanı
        if tukenme_gun is not None:
            if tukenme_gun <= 3:
                risk += 35
            elif tukenme_gun <= 7:
                risk += 25
            elif tukenme_gun <= 14:
                risk += 15
            elif tukenme_gun <= 30:
                risk += 5

        # Sipariş zamanı geçmiş mi
        if siparis_gun is not None and siparis_gun <= 0:
            risk += 25
        elif siparis_gun is not None and siparis_gun <= 3:
            risk += 10

        # Spike tespit edilmişse ek risk
        if spike_var:
            risk += 10

        return min(risk, 100)

    def _oneri_olustur(self, mevcut, minimum, tukenme_gun, teslimat_gun, gunluk_tuketim, spike_var):
        """Stok tahminine göre öneri oluşturur."""
        spike_uyari = " ⚡ Son dönemde ani tüketim artışı tespit edildi!" if spike_var else ""

        if mevcut <= 0:
            return f"🔴 STOK TÜKENMİŞ: Acil tedarik gerekiyor!{spike_uyari}"
        elif tukenme_gun is not None and tukenme_gun <= teslimat_gun:
            return (f"⚠️ KRİTİK: Stok {tukenme_gun} günde tükenecek ama teslimat süresi {teslimat_gun} gün. "
                    f"Acil sipariş verilmezse stoksuz kalınacak!{spike_uyari}")
        elif mevcut <= minimum:
            return (f"🟡 Stok minimum seviyenin altında. Günlük tüketim: {gunluk_tuketim:.1f}. "
                    f"Sipariş önerilir.{spike_uyari}")
        elif tukenme_gun is not None and tukenme_gun <= 14:
            return f"📋 Stok {tukenme_gun} gün sonra tükenecek. Sipariş planlanmalı.{spike_uyari}"
        else:
            gun_str = f"{tukenme_gun} gün" if tukenme_gun else "uzun süre"
            return f"✅ Stok yeterli seviyede. Tahmini tükenme: {gun_str} sonra."


stok_tahmin_servisi = StokTahminServisi()
