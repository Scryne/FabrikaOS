"""
FDYS — E-posta Bildirim Servisi
Faz 5 — SMTP üzerinden e-posta gönderimi
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from flask import render_template, current_app, url_for

logger = logging.getLogger(__name__)


class EpostaServisi:
    """SMTP tabanlı e-posta gönderim servisi."""

    def _ayarlari_getir(self):
        from app.models.eposta import EpostaAyarlari
        return EpostaAyarlari.ayarlari_getir()

    def _smtp_baglantisi(self, ayarlar):
        """SMTP bağlantısı oluşturur."""
        if ayarlar.ssl_aktif:
            server = smtplib.SMTP_SSL(ayarlar.smtp_host, ayarlar.smtp_port, timeout=10)
        else:
            server = smtplib.SMTP(ayarlar.smtp_host, ayarlar.smtp_port, timeout=10)
            if ayarlar.tls_aktif:
                server.starttls()
        if ayarlar.smtp_kullanici and ayarlar.smtp_sifre:
            server.login(ayarlar.smtp_kullanici, ayarlar.smtp_sifre)
        return server

    def eposta_gonder(self, alici, konu, icerik_html):
        """Tekli e-posta gönderir."""
        ayarlar = self._ayarlari_getir()
        if not ayarlar.aktif or not ayarlar.yapilandirildi_mi:
            logger.debug("E-posta sistemi aktif değil veya yapılandırılmamış.")
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = konu
        msg['From'] = f"{ayarlar.gonderici_ad} <{ayarlar.gonderici_eposta}>"
        msg['To'] = alici

        html_part = MIMEText(icerik_html, 'html', 'utf-8')
        msg.attach(html_part)

        try:
            server = self._smtp_baglantisi(ayarlar)
            server.sendmail(ayarlar.gonderici_eposta, alici, msg.as_string())
            server.quit()
            ayarlar.son_gonderim_tarihi = datetime.now(timezone.utc)
            from app.extensions import db
            db.session.commit()
            logger.info(f"E-posta gönderildi: {alici}")
            return True
        except Exception as e:
            logger.error(f"E-posta gönderim hatası ({alici}): {e}")
            return False

    def kritik_uyari_gonder(self, baslik, mesaj, modul='sistem'):
        """Tüm yöneticilere kritik uyarı e-postası gönderir."""
        ayarlar = self._ayarlari_getir()
        if not ayarlar.aktif or not ayarlar.kritik_uyari_aktif:
            return

        from app.models.kullanici import Kullanici
        from app.models.personel import Calisan
        yoneticiler = Kullanici.query.filter_by(rol='yonetici', aktif=True).all()

        try:
            html = render_template('eposta_sablonlari/kritik_uyari.html', baslik=baslik, mesaj=mesaj, modul=modul, tarih=datetime.now().strftime('%d.%m.%Y %H:%M'), url=None)
        except Exception as e:
            logger.error(f"Kritik uyarı şablonu render hatası: {e}")
            html = self._kritik_uyari_html(baslik, mesaj, modul) # Fallback

        for y in yoneticiler:
            calisan = Calisan.query.filter_by(kullanici_id=y.id).first()
            eposta = calisan.eposta if calisan and calisan.eposta else None
            if eposta:
                self.eposta_gonder(eposta, f"⚠️ FDYS Kritik Uyarı: {baslik}", html)

    def test_baglantisi(self):
        """SMTP bağlantı testi yapar."""
        ayarlar = self._ayarlari_getir()
        try:
            server = self._smtp_baglantisi(ayarlar)
            server.noop()
            server.quit()
            ayarlar.test_basarili = True
            ayarlar.son_test_tarihi = datetime.now(timezone.utc)
            from app.extensions import db
            db.session.commit()
            return {'basarili': True, 'mesaj': 'SMTP bağlantısı başarılı!'}
        except Exception as e:
            ayarlar.test_basarili = False
            ayarlar.son_test_tarihi = datetime.now(timezone.utc)
            from app.extensions import db
            db.session.commit()
            return {'basarili': False, 'mesaj': f'Bağlantı hatası: {str(e)}'}

    def gunluk_ozet_gonder(self):
        """Günlük KPI özet e-postası gönderir."""
        ayarlar = self._ayarlari_getir()
        if not ayarlar.aktif or not ayarlar.gunluk_ozet_aktif:
            return
        alicilar = ayarlar.ozet_alici_epostalar or []
        if not alicilar:
            return

        ozet = self._gunluk_ozet_verisi()
        
        try:
            html = render_template('eposta_sablonlari/gunluk_ozet.html', 
                                   tarih=ozet['tarih'], 
                                   oee=ozet['oee'], 
                                   uretim=ozet['uretim'], 
                                   acik_ariza=ozet['acik_ariza'], 
                                   kritik_stok=ozet['kritik_stok'],
                                   dashboard_url='#')
        except Exception as e:
            logger.error(f"Günlük özet şablonu render hatası: {e}")
            html = self._gunluk_ozet_html(ozet) # Fallback

        bugun = datetime.now().strftime('%d.%m.%Y')

        for alici in alicilar:
            self.eposta_gonder(alici, f"📊 FDYS Günlük Özet — {bugun}", html)

    def _gunluk_ozet_verisi(self):
        """Dashboard'dan günlük KPI verileri toplar."""
        from app.models.makine import UretimVerisi, ArizaKaydi
        from app.models.stok import Malzeme
        from sqlalchemy import func
        from datetime import timedelta

        bugun = datetime.now(timezone.utc).date()
        bugun_uretim = db.session.query(func.sum(UretimVerisi.gercek_uretim)).filter(
            UretimVerisi.tarih == bugun).scalar() or 0
        ort_oee = db.session.query(func.avg(UretimVerisi.oee_yuzde)).filter(
            UretimVerisi.tarih == bugun).scalar() or 0
        acik_ariza = ArizaKaydi.query.filter_by(durum='acik').count()
        kritik_stok = Malzeme.query.filter(Malzeme.mevcut_miktar <= Malzeme.minimum_stok).count()

        from app.extensions import db
        return {
            'tarih': bugun.strftime('%d.%m.%Y'),
            'uretim': int(bugun_uretim),
            'oee': round(float(ort_oee), 1),
            'acik_ariza': acik_ariza,
            'kritik_stok': kritik_stok
        }

    # ── HTML Şablonları ──

    def _kritik_uyari_html(self, baslik, mesaj, modul):
        return f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#1a1a2e;color:#e0e0e0;border-radius:12px;overflow:hidden;">
            <div style="background:linear-gradient(135deg,#dc3545,#c82333);padding:20px 30px;">
                <h2 style="margin:0;color:#fff;">⚠️ Kritik Uyarı</h2>
                <p style="margin:5px 0 0;color:rgba(255,255,255,0.8);font-size:13px;">FDYS — Fabrika Dijital Yönetim Sistemi</p>
            </div>
            <div style="padding:30px;">
                <h3 style="color:#ff6b6b;margin-top:0;">{baslik}</h3>
                <p style="color:#ccc;line-height:1.6;">{mesaj}</p>
                <p style="color:#888;font-size:12px;margin-top:20px;">Modül: {modul} | {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
            </div>
        </div>"""

    def _gunluk_ozet_html(self, ozet):
        oee_renk = '#00b894' if ozet['oee'] >= 85 else '#fdcb6e' if ozet['oee'] >= 70 else '#d63031'
        return f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#1a1a2e;color:#e0e0e0;border-radius:12px;overflow:hidden;">
            <div style="background:linear-gradient(135deg,#667eea,#764ba2);padding:20px 30px;">
                <h2 style="margin:0;color:#fff;">📊 Günlük Özet Rapor</h2>
                <p style="margin:5px 0 0;color:rgba(255,255,255,0.8);">{ozet['tarih']}</p>
            </div>
            <div style="padding:30px;">
                <table style="width:100%;border-collapse:collapse;">
                    <tr><td style="padding:12px;border-bottom:1px solid #333;color:#aaa;">Toplam Üretim</td>
                        <td style="padding:12px;border-bottom:1px solid #333;text-align:right;font-weight:bold;color:#fff;">{ozet['uretim']:,} adet</td></tr>
                    <tr><td style="padding:12px;border-bottom:1px solid #333;color:#aaa;">Ortalama OEE</td>
                        <td style="padding:12px;border-bottom:1px solid #333;text-align:right;font-weight:bold;color:{oee_renk};">%{ozet['oee']}</td></tr>
                    <tr><td style="padding:12px;border-bottom:1px solid #333;color:#aaa;">Açık Arıza</td>
                        <td style="padding:12px;border-bottom:1px solid #333;text-align:right;font-weight:bold;color:{'#d63031' if ozet['acik_ariza'] > 0 else '#00b894'};">{ozet['acik_ariza']}</td></tr>
                    <tr><td style="padding:12px;color:#aaa;">Kritik Stok</td>
                        <td style="padding:12px;text-align:right;font-weight:bold;color:{'#fdcb6e' if ozet['kritik_stok'] > 0 else '#00b894'};">{ozet['kritik_stok']}</td></tr>
                </table>
            </div>
        </div>"""


eposta_servisi = EpostaServisi()
