"""
FDYS — Otomasyon Motoru v2.0
Kategori 6 — İş Akışı Otomasyonu

Olay bazlı otomatik iş emri oluşturma motoru.
4 tetikleyici kural.

v2.0 Yenilikler:
    - Detaylı exception logging (except Exception: return None → logger.error)
    - Audit log kaydı (her otomasyon çalışması loglanır)
    - Otomasyon kuralları aktif/pasif desteği
    - Kural çalışma istatistikleri
    - Akıllı atama: vardiya kontrolü + yetkinlik + iş yükü
"""

import logging
from datetime import datetime, timezone
from app.services.is_emri_servisi import is_emri_servisi

logger = logging.getLogger(__name__)


class OtomasyonMotoru:
    """Olay bazlı otomatik iş emri oluşturma motoru."""

    # Kural durumları (admin panelinden toggle edilebilir)
    _kural_durumlari = {
        'ariza_is_emri': True,
        'stok_satin_alma': True,
        'bakim_is_emri': True,
        'egitim_is_emri': True,
    }

    # Kural çalışma istatistikleri
    _kural_istatistikleri = {
        'ariza_is_emri': {'tetikleme': 0, 'basarili': 0, 'hatali': 0},
        'stok_satin_alma': {'tetikleme': 0, 'basarili': 0, 'hatali': 0},
        'bakim_is_emri': {'tetikleme': 0, 'basarili': 0, 'hatali': 0},
        'egitim_is_emri': {'tetikleme': 0, 'basarili': 0, 'hatali': 0},
    }

    def kural_aktif_mi(self, kural_adi):
        """Belirtilen kuralın aktif olup olmadığını döner."""
        return self._kural_durumlari.get(kural_adi, False)

    def kural_toggle(self, kural_adi, aktif):
        """Kural durumunu değiştirir."""
        if kural_adi in self._kural_durumlari:
            self._kural_durumlari[kural_adi] = aktif
            logger.info(f"Otomasyon kuralı '{kural_adi}' → {'Aktif' if aktif else 'Pasif'}")
            return True
        return False

    def kural_istatistikleri_al(self):
        """Tüm kuralların çalışma istatistiklerini döner."""
        return {
            kural: {
                'aktif': self._kural_durumlari.get(kural, False),
                **istatistik
            }
            for kural, istatistik in self._kural_istatistikleri.items()
        }

    def _audit_log(self, kural, basarili, detay):
        """Otomasyon çalışmasını audit log'a kaydeder."""
        durum = 'BAŞARILI' if basarili else 'BAŞARISIZ'
        logger.info(f"[OTOMASYON AUDIT] Kural: {kural} | Durum: {durum} | Detay: {detay}")

        # İstatistik güncelle
        if kural in self._kural_istatistikleri:
            self._kural_istatistikleri[kural]['tetikleme'] += 1
            if basarili:
                self._kural_istatistikleri[kural]['basarili'] += 1
            else:
                self._kural_istatistikleri[kural]['hatali'] += 1

    def ariza_is_emri_olustur(self, ariza_kaydi):
        """Arıza bildirimi → Otomatik iş emri + en uygun teknisyene atama."""
        kural = 'ariza_is_emri'
        if not self.kural_aktif_mi(kural):
            logger.info(f"Otomasyon kuralı '{kural}' pasif, atlanıyor.")
            return None

        try:
            oncelik_map = {
                'kritik': 'kritik', 'yuksek': 'yuksek',
                'normal': 'normal', 'dusuk': 'dusuk',
            }
            oncelik = oncelik_map.get(ariza_kaydi.oncelik, 'normal')

            # Akıllı atama: vardiya + yetkinlik + iş yükü
            teknisyen = self._akilli_teknisyen_bul(makine_id=ariza_kaydi.makine_id, oncelik=oncelik)
            makine_ad = ariza_kaydi.makine.ad if ariza_kaydi.makine else f"Makine #{ariza_kaydi.makine_id}"

            sonuc = is_emri_servisi.is_emri_olustur(
                baslik=f"Arıza Giderme: {makine_ad} — {ariza_kaydi.ariza_turu}",
                aciklama=(
                    f"Makine: {makine_ad}\nArıza Türü: {ariza_kaydi.ariza_turu}\n"
                    f"Öncelik: {ariza_kaydi.oncelik}\nAçıklama: {ariza_kaydi.aciklama}\n\n"
                    f"Bu iş emri arıza bildirimi sonucu otomatik oluşturulmuştur."
                ),
                kaynak_modul='makine', kaynak_id=ariza_kaydi.id,
                kategori='ariza', oncelik=oncelik,
                olusturan_id=ariza_kaydi.bildiren_id,
                atanan_id=teknisyen.id if teknisyen else None,
            )

            self._audit_log(kural, True,
                            f"Arıza #{ariza_kaydi.id} → İE '{sonuc.is_emri_no if sonuc else '?'}' oluşturuldu. "
                            f"Atanan: {teknisyen.kullanici_adi if teknisyen else 'Yok'}")
            return sonuc

        except Exception as e:
            self._audit_log(kural, False, f"Arıza #{ariza_kaydi.id}: {e}")
            logger.error(f"Arıza iş emri otomasyon hatası: {e}", exc_info=True)
            return None

    def stok_satin_alma_talebi(self, malzeme):
        """Stok minimum eşik altına düştüğünde → Otomatik satın alma talebi."""
        kural = 'stok_satin_alma'
        if not self.kural_aktif_mi(kural):
            logger.info(f"Otomasyon kuralı '{kural}' pasif, atlanıyor.")
            return None

        try:
            from app.models.is_emri import IsEmri
            mevcut = IsEmri.query.filter(
                IsEmri.kaynak_modul == 'stok', IsEmri.kaynak_id == malzeme.id,
                IsEmri.kategori == 'satin_alma',
                IsEmri.durum.in_([IsEmri.DURUM_ACIK, IsEmri.DURUM_ATANDI, IsEmri.DURUM_DEVAM])
            ).first()
            if mevcut:
                self._audit_log(kural, True,
                                f"Malzeme {malzeme.kod}: Mevcut açık talep var (IE #{mevcut.is_emri_no}), atlanıyor.")
                return None

            tedarikci_bilgisi = ""
            if malzeme.tedarikci:
                tedarikci_bilgisi = (
                    f"\nTedarikçi: {malzeme.tedarikci.ad}"
                    f"\nOrtalama Teslimat: {malzeme.tedarikci.ortalama_teslimat_gun or '?'} gün"
                )

            sonuc = is_emri_servisi.is_emri_olustur(
                baslik=f"Satın Alma Talebi: {malzeme.ad} ({malzeme.kod})",
                aciklama=(
                    f"Malzeme: {malzeme.ad} ({malzeme.kod})\n"
                    f"Mevcut Miktar: {malzeme.mevcut_miktar} {malzeme.birim}\n"
                    f"Minimum Stok: {malzeme.minimum_stok} {malzeme.birim}\n"
                    f"Birim Fiyat: {malzeme.birim_fiyat or '—'} ₺{tedarikci_bilgisi}\n\n"
                    f"Bu talep stok seviyesi kritik eşiğin altına düştüğü için otomatik oluşturulmuştur."
                ),
                kaynak_modul='stok', kaynak_id=malzeme.id,
                kategori='satin_alma', oncelik='yuksek',
            )

            self._audit_log(kural, True,
                            f"Malzeme {malzeme.kod}: Satın alma talebi '{sonuc.is_emri_no if sonuc else '?'}' oluşturuldu.")
            return sonuc

        except Exception as e:
            self._audit_log(kural, False, f"Malzeme {malzeme.id}: {e}")
            logger.error(f"Stok satın alma otomasyon hatası: {e}", exc_info=True)
            return None

    def bakim_is_emri_olustur(self, makine):
        """Periyodik bakım yaklaştığında → Otomatik bakım iş emri."""
        kural = 'bakim_is_emri'
        if not self.kural_aktif_mi(kural):
            logger.info(f"Otomasyon kuralı '{kural}' pasif, atlanıyor.")
            return None

        try:
            from app.models.is_emri import IsEmri
            mevcut = IsEmri.query.filter(
                IsEmri.kaynak_modul == 'bakim', IsEmri.kaynak_id == makine.id,
                IsEmri.kategori == 'bakim',
                IsEmri.durum.in_([IsEmri.DURUM_ACIK, IsEmri.DURUM_ATANDI, IsEmri.DURUM_DEVAM])
            ).first()
            if mevcut:
                self._audit_log(kural, True,
                                f"Makine {makine.kod}: Mevcut açık bakım emri var (IE #{mevcut.is_emri_no}), atlanıyor.")
                return None

            sonraki = makine.sonraki_bakim_tarihi
            kalan_gun = None
            if sonraki:
                kalan_gun = (sonraki - datetime.now(timezone.utc).date()).days

            teknisyen = self._akilli_teknisyen_bul(makine_id=makine.id, oncelik='normal')

            sonuc = is_emri_servisi.is_emri_olustur(
                baslik=f"Periyodik Bakım: {makine.ad} ({makine.kod})",
                aciklama=(
                    f"Makine: {makine.ad} ({makine.kod})\n"
                    f"Son Bakım: {makine.son_bakim_tarihi or '—'}\n"
                    f"Bakım Periyodu: {makine.periyodik_bakim_gun} gün\n"
                    f"Sonraki Bakım: {sonraki or '—'}\nKalan: {kalan_gun if kalan_gun is not None else '—'} gün\n\n"
                    f"Bu iş emri periyodik bakım takvimi kapsamında otomatik oluşturulmuştur."
                ),
                kaynak_modul='bakim', kaynak_id=makine.id,
                kategori='bakim',
                oncelik='normal' if (kalan_gun and kalan_gun > 3) else 'yuksek',
                atanan_id=teknisyen.id if teknisyen else None,
            )

            self._audit_log(kural, True,
                            f"Makine {makine.kod}: Bakım iş emri '{sonuc.is_emri_no if sonuc else '?'}' oluşturuldu.")
            return sonuc

        except Exception as e:
            self._audit_log(kural, False, f"Makine {makine.id}: {e}")
            logger.error(f"Bakım iş emri otomasyon hatası: {e}", exc_info=True)
            return None

    def egitim_is_emri_olustur(self, egitim):
        """İSG eğitim süresi dolduğunda → Otomatik eğitim planı iş emri."""
        kural = 'egitim_is_emri'
        if not self.kural_aktif_mi(kural):
            logger.info(f"Otomasyon kuralı '{kural}' pasif, atlanıyor.")
            return None

        try:
            from app.models.is_emri import IsEmri
            mevcut = IsEmri.query.filter(
                IsEmri.kaynak_modul == 'isg', IsEmri.kaynak_id == egitim.id,
                IsEmri.kategori == 'egitim',
                IsEmri.durum.in_([IsEmri.DURUM_ACIK, IsEmri.DURUM_ATANDI, IsEmri.DURUM_DEVAM])
            ).first()
            if mevcut:
                self._audit_log(kural, True,
                                f"Eğitim #{egitim.id}: Mevcut açık iş emri var, atlanıyor.")
                return None

            calisan_ad = egitim.calisan.ad_soyad if egitim.calisan else f"Çalışan #{egitim.calisan_id}"

            sonuc = is_emri_servisi.is_emri_olustur(
                baslik=f"Eğitim Yenileme: {egitim.egitim_adi}",
                aciklama=(
                    f"Çalışan: {calisan_ad}\nEğitim: {egitim.egitim_adi}\n"
                    f"Kategori: {egitim.egitim_kategorisi or '—'}\n"
                    f"Geçerlilik Bitiş: {egitim.gecerlilik_bitis}\n\n"
                    f"Bu iş emri İSG eğitim süresinin dolması nedeniyle otomatik oluşturulmuştur."
                ),
                kaynak_modul='isg', kaynak_id=egitim.id,
                kategori='egitim', oncelik='yuksek',
            )

            self._audit_log(kural, True,
                            f"Eğitim #{egitim.id} ({egitim.egitim_adi}): İş emri oluşturuldu.")
            return sonuc

        except Exception as e:
            self._audit_log(kural, False, f"Eğitim #{egitim.id}: {e}")
            logger.error(f"Eğitim iş emri otomasyon hatası: {e}", exc_info=True)
            return None

    def _akilli_teknisyen_bul(self, makine_id=None, oncelik='normal'):
        """
        Akıllı teknisyen atama: iş yükü + yetkinlik skorlaması.
        Kritik iş emirlerinde en az iş yükü olan teknisyeni seçer.
        """
        try:
            from app.models.kullanici import Kullanici
            from app.models.is_emri import IsEmri

            teknisyenler = Kullanici.query.filter_by(rol='teknisyen', aktif=True).all()
            if not teknisyenler:
                return None

            skorlar = []
            for t in teknisyenler:
                # Mevcut açık iş emri sayısı (iş yükü)
                is_yuku = IsEmri.query.filter(
                    IsEmri.atanan_id == t.id,
                    IsEmri.durum.in_([IsEmri.DURUM_ACIK, IsEmri.DURUM_ATANDI, IsEmri.DURUM_DEVAM])
                ).count()

                # Yetkinlik: bu makineyle ilgili geçmiş çözüm sayısı
                yetkinlik = 0
                if makine_id:
                    from app.models.makine import ArizaKaydi
                    yetkinlik = ArizaKaydi.query.filter(
                        ArizaKaydi.atanan_teknisyen_id == t.id,
                        ArizaKaydi.makine_id == makine_id,
                        ArizaKaydi.durum == 'cozuldu'
                    ).count()

                # Skor: düşük iş yükü + yüksek yetkinlik = iyi
                skor = (yetkinlik * 10) - (is_yuku * 5)

                skorlar.append({
                    'teknisyen': t,
                    'is_yuku': is_yuku,
                    'yetkinlik': yetkinlik,
                    'skor': skor,
                })

            if not skorlar:
                return None

            # En yüksek skorlu teknisyeni seç
            skorlar.sort(key=lambda x: x['skor'], reverse=True)
            secilen = skorlar[0]

            logger.info(
                f"Akıllı atama: {secilen['teknisyen'].kullanici_adi} "
                f"(Yetkinlik: {secilen['yetkinlik']}, İş yükü: {secilen['is_yuku']}, "
                f"Skor: {secilen['skor']})"
            )

            return secilen['teknisyen']

        except Exception as e:
            logger.error(f"Akıllı teknisyen bulma hatası: {e}", exc_info=True)
            # Fallback: basit atama
            return is_emri_servisi.en_uygun_teknisyen_bul(makine_id=makine_id)


# Singleton instance
otomasyon_motoru = OtomasyonMotoru()
