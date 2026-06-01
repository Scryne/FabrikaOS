"""
FDYS — SMS Servisi
Faz 4 — SMS gateway entegrasyonu ve bildirim gönderimi

Desteklenen Gateway'ler:
    - NetGSM
    - İletimerkezi
    - Mock (geliştirme ortamı)

Kullanım:
    from app.services.sms_servisi import sms_gonder
    sms_gonder('5551234567', 'Talep #TLP-2026-00001 oluşturuldu.')
"""

import logging
import re
from flask import current_app

logger = logging.getLogger(__name__)


class SMSGonderimSonucu:
    """SMS gönderim sonucu wrapper sınıfı."""
    def __init__(self, basarili, mesaj_id=None, hata=None):
        self.basarili = basarili
        self.mesaj_id = mesaj_id
        self.hata = hata

    def __repr__(self):
        durum = 'Başarılı' if self.basarili else 'Başarısız'
        return f'<SMSGonderimSonucu {durum}: {self.mesaj_id or self.hata}>'


def telefon_formatla(telefon):
    """
    Telefon numarasını standart formata çevirir.
    Giriş: +90 555 123 45 67, 05551234567, 5551234567
    Çıkış: 905551234567
    """
    if not telefon:
        return None

    # Sadece rakamları al
    rakamlar = re.sub(r'[^\d]', '', telefon)

    # Başındaki 0'ı kaldır
    if rakamlar.startswith('0'):
        rakamlar = rakamlar[1:]

    # 90 ekle
    if not rakamlar.startswith('90'):
        rakamlar = '90' + rakamlar

    # 12 haneli olmalı
    if len(rakamlar) != 12:
        logger.warning(f'Geçersiz telefon numarası: {telefon} → {rakamlar}')
        return None

    return rakamlar


def sms_gonder(telefon, mesaj):
    """
    SMS gönderir. Gateway yapılandırmasına göre uygun yöntemi kullanır.

    Args:
        telefon: Alıcı telefon numarası
        mesaj: Gönderilecek mesaj metni

    Returns:
        SMSGonderimSonucu nesnesi
    """
    formatli_tel = telefon_formatla(telefon)
    if not formatli_tel:
        return SMSGonderimSonucu(basarili=False, hata='Geçersiz telefon numarası.')

    gateway = current_app.config.get('SMS_GATEWAY', 'mock')

    try:
        if gateway == 'netgsm':
            return _netgsm_gonder(formatli_tel, mesaj)
        elif gateway == 'iletimerkezi':
            return _iletimerkezi_gonder(formatli_tel, mesaj)
        else:
            return _mock_gonder(formatli_tel, mesaj)
    except Exception as e:
        logger.error(f'SMS gönderim hatası: {e}')
        return SMSGonderimSonucu(basarili=False, hata=str(e))


def _mock_gonder(telefon, mesaj):
    """Geliştirme ortamı için mock SMS gönderimi. Loglar ama gerçekte göndermez."""
    logger.info(f'[MOCK SMS] → {telefon}: {mesaj[:80]}...')
    return SMSGonderimSonucu(basarili=True, mesaj_id=f'MOCK-{telefon[-4:]}')


def _netgsm_gonder(telefon, mesaj):
    """NetGSM API ile SMS gönderimi."""
    try:
        import requests
    except ImportError:
        logger.error('requests kütüphanesi eksik, SMS gönderilemedi.')
        return SMSGonderimSonucu(basarili=False, hata='requests kütüphanesi eksik.')

    api_url = current_app.config.get('SMS_NETGSM_URL', 'https://api.netgsm.com.tr/sms/send/get')
    params = {
        'usercode': current_app.config.get('SMS_NETGSM_USER', ''),
        'password': current_app.config.get('SMS_NETGSM_PASS', ''),
        'gsmno': telefon,
        'message': mesaj,
        'msgheader': current_app.config.get('SMS_NETGSM_HEADER', 'FDYS'),
    }

    response = requests.get(api_url, params=params, timeout=10)
    code = response.text.strip().split(' ')[0]

    if code in ('00', '01', '02'):
        logger.info(f'SMS gönderildi (NetGSM): {telefon}')
        return SMSGonderimSonucu(basarili=True, mesaj_id=response.text.strip())
    else:
        logger.error(f'NetGSM hata: {response.text.strip()}')
        return SMSGonderimSonucu(basarili=False, hata=f'NetGSM kodu: {code}')


def _iletimerkezi_gonder(telefon, mesaj):
    """İletimerkezi API ile SMS gönderimi."""
    try:
        import requests
    except ImportError:
        return SMSGonderimSonucu(basarili=False, hata='requests kütüphanesi eksik.')

    api_url = 'https://api.iletimerkezi.com/v1/send-sms/get/'
    params = {
        'username': current_app.config.get('SMS_ILETI_USER', ''),
        'password': current_app.config.get('SMS_ILETI_PASS', ''),
        'text': mesaj,
        'receipents': telefon,
        'sender': current_app.config.get('SMS_ILETI_HEADER', 'FDYS'),
    }

    response = requests.get(api_url, params=params, timeout=10)

    if response.status_code == 200:
        logger.info(f'SMS gönderildi (İletimerkezi): {telefon}')
        return SMSGonderimSonucu(basarili=True, mesaj_id='ILETI-OK')
    else:
        logger.error(f'İletimerkezi hata: {response.status_code} — {response.text[:200]}')
        return SMSGonderimSonucu(basarili=False, hata=f'HTTP {response.status_code}')


# ──────────────────────────────────────────────
# ŞABLON MESAJLARI
# ──────────────────────────────────────────────

def talep_olusturuldu_sms(telefon, talep_no, baslik):
    """Talep oluşturuldu bildirim SMS'i."""
    mesaj = f"FDYS: {talep_no} nolu talebiniz alınmıştır. Konu: {baslik[:60]}. Durumu 'Taleplerim' bölümünden takip edebilirsiniz."
    return sms_gonder(telefon, mesaj)


def talep_durum_sms(telefon, talep_no, yeni_durum_adi):
    """Talep durum değişikliği bildirim SMS'i."""
    mesaj = f"FDYS: {talep_no} nolu talebinizin durumu '{yeni_durum_adi}' olarak güncellendi."
    return sms_gonder(telefon, mesaj)


def talep_tamamlandi_sms(telefon, talep_no):
    """Talep tamamlandı bildirim SMS'i."""
    mesaj = f"FDYS: {talep_no} nolu talebiniz tamamlanmıştır. Memnuniyet değerlendirmenizi panelimizden yapabilirsiniz."
    return sms_gonder(telefon, mesaj)


def borc_hatirlatma_sms(telefon, kalan_tutar, son_odeme_tarihi):
    """Borç hatırlatma SMS'i."""
    mesaj = f"FDYS: {kalan_tutar:.2f} TL tutarında ödenmemiş borcunuz bulunmaktadır. Son ödeme: {son_odeme_tarihi}. Detaylar panelimizde."
    return sms_gonder(telefon, mesaj)
