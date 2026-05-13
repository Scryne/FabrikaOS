"""
FDYS — İş Emri Servisi v2.0
Kategori 6 — İş Akışı Otomasyonu

Merkezi iş emri oluşturma, atama, durum yönetimi ve istatistik servisi.

v2.0 Yenilikler:
    - Kademeli SLA uyarıları (%75, %90, %100)
    - SLA eskalasyon (süre aşımında üst yönetici bildirimi)
    - İptal nedenini zorunlu alan yapma
    - İş emri dondurma (hold) desteği
    - Teknisyen performans raporu
    - Kategori bazlı istatistik
    - Haftalık/aylık trend verisi
    - Detaylı exception logging
"""

import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from app.extensions import db
from app.models.is_emri import IsEmri, IsEmriYorum

logger = logging.getLogger(__name__)


class IsEmriServisi:
    """İş emri oluşturma, atama ve yaşam döngüsü yönetimi."""

    def is_emri_no_uret(self):
        """IE-{yıl}-{sıralı 4 basamaklı numara} formatında iş emri numarası üretir."""
        yil = datetime.now(timezone.utc).year
        prefix = f"IE-{yil}-"

        son_kayit = IsEmri.query.filter(
            IsEmri.is_emri_no.like(f'{prefix}%')
        ).order_by(IsEmri.id.desc()).first()

        if son_kayit:
            try:
                son_no = int(son_kayit.is_emri_no.split('-')[-1])
                yeni_no = son_no + 1
            except (ValueError, IndexError):
                yeni_no = 1
        else:
            yeni_no = 1

        return f"{prefix}{yeni_no:04d}"

    def is_emri_olustur(self, baslik, aciklama=None, kaynak_modul='manuel',
                         kaynak_id=None, kategori='genel', oncelik='normal',
                         olusturan_id=None, atanan_id=None, sla_saat=None):
        """Yeni iş emri oluşturur, numara atar, SLA hesaplar ve bildirim gönderir."""
        is_emri = IsEmri(
            is_emri_no=self.is_emri_no_uret(),
            baslik=baslik,
            aciklama=aciklama,
            kaynak_modul=kaynak_modul,
            kaynak_id=kaynak_id,
            kategori=kategori,
            oncelik=oncelik,
            olusturan_id=olusturan_id,
            atanan_id=atanan_id,
            sla_saat=sla_saat,
            durum=IsEmri.DURUM_ATANDI if atanan_id else IsEmri.DURUM_ACIK,
        )

        is_emri.olusturma_tarihi = datetime.now(timezone.utc)
        is_emri.sla_hesapla()

        db.session.add(is_emri)
        db.session.commit()

        if atanan_id:
            self._atama_bildirimi_gonder(is_emri)

        logger.info(f"İş emri oluşturuldu: {is_emri.is_emri_no} — {baslik}")
        return is_emri

    def en_uygun_teknisyen_bul(self, makine_id=None, departman=None):
        """Akıllı teknisyen eşleştirme algoritması."""
        from app.models.kullanici import Kullanici
        from app.models.personel import Calisan

        teknisyenler = Kullanici.query.filter(
            Kullanici.rol == 'teknisyen',
            Kullanici.aktif == True
        ).all()

        if not teknisyenler:
            yoneticiler = Kullanici.query.filter(
                Kullanici.rol == 'yonetici',
                Kullanici.aktif == True
            ).first()
            return yoneticiler

        en_iyi = None
        en_yuksek_puan = -999

        for teknisyen in teknisyenler:
            puan = 0
            if makine_id and teknisyen.calisan:
                yetkinlik = teknisyen.calisan.yetkinlik_puani(makine_id)
                puan += yetkinlik * 3
            if departman and teknisyen.calisan:
                if teknisyen.calisan.departman == departman:
                    puan += 2
            acik_is_sayisi = IsEmri.query.filter(
                IsEmri.atanan_id == teknisyen.id,
                IsEmri.durum.in_([IsEmri.DURUM_ACIK, IsEmri.DURUM_ATANDI, IsEmri.DURUM_DEVAM])
            ).count()
            puan -= acik_is_sayisi

            if puan > en_yuksek_puan:
                en_yuksek_puan = puan
                en_iyi = teknisyen

        return en_iyi

    def durum_guncelle(self, is_emri_id, yeni_durum, kullanici_id=None,
                        cozum_notu=None, iptal_nedeni=None):
        """İş emri durumunu günceller. Geçersiz geçişleri reddeder."""
        is_emri = db.session.get(IsEmri, is_emri_id)
        if not is_emri:
            return False, "İş emri bulunamadı."

        if not is_emri.gecis_gecerli_mi(yeni_durum):
            return False, f"'{is_emri.durum_etiket}' durumundan bu duruma geçiş yapılamaz."

        # İptal nedeni zorunluluğu
        if yeni_durum == IsEmri.DURUM_IPTAL and not iptal_nedeni:
            return False, "İptal nedeni belirtilmelidir."

        eski_durum = is_emri.durum
        is_emri.durum = yeni_durum
        simdi = datetime.now(timezone.utc)

        if yeni_durum == IsEmri.DURUM_DEVAM and not is_emri.baslama_zamani:
            is_emri.baslama_zamani = simdi

        elif yeni_durum == IsEmri.DURUM_TAMAMLANDI:
            is_emri.tamamlanma_zamani = simdi
            if cozum_notu:
                is_emri.cozum_notu = cozum_notu
            if is_emri.baslama_zamani:
                baslama = is_emri.baslama_zamani
                if baslama.tzinfo is None:
                    baslama = baslama.replace(tzinfo=timezone.utc)
                diff = simdi - baslama
                is_emri.gercek_sure_dk = int(diff.total_seconds() / 60)

        elif yeni_durum == IsEmri.DURUM_ONAYLANDI:
            is_emri.onay_zamani = simdi
            is_emri.onaylayan_id = kullanici_id

        elif yeni_durum == IsEmri.DURUM_IPTAL:
            if iptal_nedeni:
                is_emri.cozum_notu = f"[İPTAL NEDENİ] {iptal_nedeni}"

        db.session.commit()
        db.session.refresh(is_emri)

        # Otomatik yorum ekle
        durum_etiketleri = {
            'acik': 'Açık', 'atandi': 'Atandı', 'devam': 'Devam Ediyor',
            'tamamlandi': 'Tamamlandı', 'onaylandi': 'Onaylandı', 'iptal': 'İptal'
        }
        eski_etiket = durum_etiketleri.get(eski_durum, eski_durum)
        yeni_etiket = durum_etiketleri.get(yeni_durum, yeni_durum)

        yorum_icerik = f"Durum güncellendi: {eski_etiket} → {yeni_etiket}"
        if iptal_nedeni:
            yorum_icerik += f"\nNeden: {iptal_nedeni}"

        self.yorum_ekle(
            is_emri_id=is_emri_id,
            kullanici_id=kullanici_id,
            icerik=yorum_icerik
        )

        self._durum_degisikligi_bildirimi(is_emri, eski_durum)

        logger.info(f"İş emri {is_emri.is_emri_no}: {eski_etiket} → {yeni_etiket}")
        return True, f"İş emri durumu '{yeni_etiket}' olarak güncellendi."

    def yorum_ekle(self, is_emri_id, kullanici_id, icerik):
        """İş emrine yorum ekler."""
        if not kullanici_id:
            return None

        yorum = IsEmriYorum(
            is_emri_id=is_emri_id,
            kullanici_id=kullanici_id,
            icerik=icerik
        )
        db.session.add(yorum)
        db.session.commit()
        return yorum

    def sla_toplu_kontrol(self):
        """Tüm açık iş emirlerinin SLA durumunu kontrol eder + kademeli uyarı."""
        acik_durumlar = [IsEmri.DURUM_ACIK, IsEmri.DURUM_ATANDI, IsEmri.DURUM_DEVAM]
        is_emirleri = IsEmri.query.filter(
            IsEmri.durum.in_(acik_durumlar),
            IsEmri.sla_bitis.isnot(None)
        ).all()

        asilmis_listesi = []
        uyari_listesi = []

        for ie in is_emirleri:
            if ie.sla_asildi_mi:
                # Zaten aşılmış, eskalasyon kontrolü
                continue

            if ie.sla_kontrol():
                asilmis_listesi.append(ie)
                self._sla_asim_bildirimi(ie)
                self._sla_eskalasyon(ie)
            else:
                # Kademeli uyarı
                sla_yuzde = ie.sla_kalan_yuzde
                if sla_yuzde is not None:
                    if sla_yuzde <= 10:  # %90 doluluk = %10 kalan
                        uyari_listesi.append({'ie': ie, 'seviye': 'turuncu', 'kalan': sla_yuzde})
                        self._sla_uyari_bildirimi(ie, 'turuncu')
                    elif sla_yuzde <= 25:  # %75 doluluk = %25 kalan
                        uyari_listesi.append({'ie': ie, 'seviye': 'sari', 'kalan': sla_yuzde})
                        self._sla_uyari_bildirimi(ie, 'sari')

        if asilmis_listesi:
            db.session.commit()

        return {
            'asilmis': asilmis_listesi,
            'uyari': uyari_listesi,
        }

    def istatistikler(self):
        """Dashboard ve widget için özet istatistikler."""
        toplam = IsEmri.query.count()
        acik = IsEmri.query.filter(IsEmri.durum == IsEmri.DURUM_ACIK).count()
        atandi = IsEmri.query.filter(IsEmri.durum == IsEmri.DURUM_ATANDI).count()
        devam = IsEmri.query.filter(IsEmri.durum == IsEmri.DURUM_DEVAM).count()
        tamamlandi = IsEmri.query.filter(IsEmri.durum == IsEmri.DURUM_TAMAMLANDI).count()
        onaylandi = IsEmri.query.filter(IsEmri.durum == IsEmri.DURUM_ONAYLANDI).count()
        iptal = IsEmri.query.filter(IsEmri.durum == IsEmri.DURUM_IPTAL).count()
        sla_asilan = IsEmri.query.filter(IsEmri.sla_asildi_mi == True).count()

        ort_sure = db.session.query(func.avg(IsEmri.gercek_sure_dk)).filter(
            IsEmri.gercek_sure_dk.isnot(None)
        ).scalar() or 0

        bugun = datetime.now(timezone.utc).date()
        bugun_olusturulan = IsEmri.query.filter(
            db.func.date(IsEmri.olusturma_tarihi) == bugun
        ).count()

        return {
            'toplam': toplam,
            'acik': acik,
            'atandi': atandi,
            'devam': devam,
            'tamamlandi': tamamlandi,
            'onaylandi': onaylandi,
            'iptal': iptal,
            'bekleyen': acik + atandi + devam,
            'sla_asilan': sla_asilan,
            'ort_cozum_suresi_dk': round(float(ort_sure), 0),
            'bugun_olusturulan': bugun_olusturulan,
        }

    def teknisyen_performans_raporu(self, gun=30):
        """Teknisyen bazlı performans raporu."""
        from app.models.kullanici import Kullanici
        bas = datetime.now(timezone.utc) - timedelta(days=gun)

        teknisyenler = Kullanici.query.filter_by(rol='teknisyen', aktif=True).all()
        rapor = []

        for t in teknisyenler:
            tamamlanan = IsEmri.query.filter(
                IsEmri.atanan_id == t.id,
                IsEmri.durum.in_([IsEmri.DURUM_TAMAMLANDI, IsEmri.DURUM_ONAYLANDI]),
                IsEmri.tamamlanma_zamani >= bas
            ).all()

            acik = IsEmri.query.filter(
                IsEmri.atanan_id == t.id,
                IsEmri.durum.in_([IsEmri.DURUM_ACIK, IsEmri.DURUM_ATANDI, IsEmri.DURUM_DEVAM])
            ).count()

            sla_tutulan = sum(1 for ie in tamamlanan if not ie.sla_asildi_mi)

            ort_sure = 0
            if tamamlanan:
                sureler = [ie.gercek_sure_dk for ie in tamamlanan if ie.gercek_sure_dk]
                ort_sure = round(sum(sureler) / len(sureler)) if sureler else 0

            sla_oran = round((sla_tutulan / len(tamamlanan)) * 100, 1) if tamamlanan else 0

            rapor.append({
                'teknisyen_id': t.id,
                'teknisyen_ad': t.kullanici_adi,
                'tamamlanan_sayi': len(tamamlanan),
                'acik_sayi': acik,
                'ort_cozum_dk': ort_sure,
                'sla_tutma_orani': sla_oran,
                'sla_tutulan': sla_tutulan,
            })

        rapor.sort(key=lambda x: x['sla_tutma_orani'], reverse=True)
        return rapor

    def kategori_istatistik(self):
        """Kategori bazlı iş emri istatistiği."""
        kategori_sayilari = db.session.query(
            IsEmri.kategori,
            func.count(IsEmri.id).label('sayi')
        ).group_by(IsEmri.kategori).all()

        return [{'kategori': k, 'sayi': s} for k, s in kategori_sayilari]

    def haftalik_trend(self, hafta_sayisi=8):
        """Haftalık oluşturulan vs kapanan iş emri trendi."""
        bugun = datetime.now(timezone.utc).date()
        sonuclar = []

        for i in range(hafta_sayisi - 1, -1, -1):
            hafta_basi = bugun - timedelta(days=bugun.weekday() + 7 * i)
            hafta_sonu = hafta_basi + timedelta(days=6)

            olusturulan = IsEmri.query.filter(
                db.func.date(IsEmri.olusturma_tarihi).between(hafta_basi, hafta_sonu)
            ).count()

            kapanan = IsEmri.query.filter(
                IsEmri.durum.in_([IsEmri.DURUM_TAMAMLANDI, IsEmri.DURUM_ONAYLANDI]),
                db.func.date(IsEmri.tamamlanma_zamani).between(hafta_basi, hafta_sonu)
            ).count()

            sonuclar.append({
                'hafta': hafta_basi.strftime('%d.%m'),
                'olusturulan': olusturulan,
                'kapanan': kapanan,
            })

        return sonuclar

    # ── Bildirim Yardımcıları ──

    def _atama_bildirimi_gonder(self, is_emri):
        """Atanan kişiye bildirim gönderir."""
        try:
            from app.services.bildirim_motoru import bildirim_motoru
            bildirim_motoru.bildirim_olustur(
                kullanici_id=is_emri.atanan_id,
                baslik="Yeni İş Emri Atandı",
                mesaj=f"{is_emri.is_emri_no} — {is_emri.baslik} ({is_emri.oncelik_etiket} öncelik)",
                seviye='uyari' if is_emri.oncelik in ('kritik', 'yuksek') else 'bilgi',
                modul='is_emri',
                url=f'/is-emri/detay/{is_emri.id}'
            )
        except Exception as e:
            logger.error(f"Atama bildirimi hatası: {e}", exc_info=True)

    def _durum_degisikligi_bildirimi(self, is_emri, eski_durum):
        """Durum değişikliğinde ilgili kişilere bildirim gönderir."""
        try:
            from app.services.bildirim_motoru import bildirim_motoru
            hedef_idler = set()

            if is_emri.olusturan_id:
                hedef_idler.add(is_emri.olusturan_id)
            if is_emri.atanan_id:
                hedef_idler.add(is_emri.atanan_id)

            for kid in hedef_idler:
                bildirim_motoru.bildirim_olustur(
                    kullanici_id=kid,
                    baslik=f"İş Emri Güncellendi: {is_emri.is_emri_no}",
                    mesaj=f"Durum: {is_emri.durum_etiket}",
                    seviye='bilgi',
                    modul='is_emri',
                    url=f'/is-emri/detay/{is_emri.id}'
                )
        except Exception as e:
            logger.error(f"Durum bildirim hatası: {e}", exc_info=True)

    def _sla_asim_bildirimi(self, is_emri):
        """SLA aşıldığında yöneticilere bildirim gönderir."""
        try:
            from app.services.bildirim_motoru import bildirim_motoru
            from app.models.kullanici import Kullanici

            yoneticiler = Kullanici.query.filter_by(rol='yonetici', aktif=True).all()
            for y in yoneticiler:
                bildirim_motoru.bildirim_olustur(
                    kullanici_id=y.id,
                    baslik="⚠️ SLA Aşıldı!",
                    mesaj=f"{is_emri.is_emri_no} — {is_emri.baslik} iş emrinin SLA süresi aşıldı!",
                    seviye='kritik',
                    modul='is_emri',
                    url=f'/is-emri/detay/{is_emri.id}'
                )
        except Exception as e:
            logger.error(f"SLA aşım bildirim hatası: {e}", exc_info=True)

    def _sla_uyari_bildirimi(self, is_emri, seviye):
        """SLA yaklaşıyorken uyarı bildirimi gönderir."""
        try:
            from app.services.bildirim_motoru import bildirim_motoru

            if is_emri.atanan_id:
                mesaj_prefix = '🟡' if seviye == 'sari' else '🟠'
                bildirim_motoru.bildirim_olustur(
                    kullanici_id=is_emri.atanan_id,
                    baslik=f"{mesaj_prefix} SLA Uyarısı: {is_emri.is_emri_no}",
                    mesaj=f"SLA süresi dolmak üzere. Kalan: %{is_emri.sla_kalan_yuzde or 0:.0f}",
                    seviye='uyari',
                    modul='is_emri',
                    url=f'/is-emri/detay/{is_emri.id}'
                )
        except Exception as e:
            logger.error(f"SLA uyarı bildirim hatası: {e}", exc_info=True)

    def _sla_eskalasyon(self, is_emri):
        """SLA aşıldığında eskalasyon: üst yöneticiye bildirim."""
        try:
            from app.services.bildirim_motoru import bildirim_motoru
            from app.models.kullanici import Kullanici

            # Tüm yöneticilere eskalasyon
            yoneticiler = Kullanici.query.filter_by(rol='yonetici', aktif=True).all()
            for y in yoneticiler:
                bildirim_motoru.bildirim_olustur(
                    kullanici_id=y.id,
                    baslik=f"🔴 SLA ESKALASYON: {is_emri.is_emri_no}",
                    mesaj=(f"{is_emri.baslik} — SLA süresi aşıldı. "
                           f"Atanan: {is_emri.atanan.kullanici_adi if is_emri.atanan else 'Yok'}. "
                           f"Öncelik: {is_emri.oncelik_etiket}"),
                    seviye='kritik',
                    modul='is_emri',
                    url=f'/is-emri/detay/{is_emri.id}'
                )

            logger.warning(f"SLA eskalasyon tetiklendi: {is_emri.is_emri_no}")
        except Exception as e:
            logger.error(f"SLA eskalasyon hatası: {e}", exc_info=True)


# Singleton instance
is_emri_servisi = IsEmriServisi()
