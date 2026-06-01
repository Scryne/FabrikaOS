import logging
from celery_worker import celery
from flask import current_app

logger = logging.getLogger(__name__)

@celery.task(bind=True, max_retries=3)
def eposta_gonder_task(self, alici, konu, icerik):
    """
    Asenkron e-posta gönderme görevi.
    Gerçek SMTP bağlantısı yapılandırılana kadar simüle eder.
    """
    logger.info(f"E-POSTA GÖNDERİLİYOR: -> {alici} | Konu: {konu}")
    
    try:
        # İleride e-posta servisi buraya entegre edilecek (Örn: Flask-Mail)
        # from app.services.eposta_servisi import mail_gonder
        # mail_gonder(alici, konu, icerik)
        
        logger.info(f"E-POSTA BAŞARIYLA GÖNDERİLDİ: -> {alici}")
        return True
    except Exception as exc:
        logger.error(f"E-POSTA GÖNDERİM HATASI: {exc}")
        self.retry(exc=exc, countdown=60) # 60 saniye sonra tekrar dene


@celery.task(bind=True, max_retries=3)
def sms_gonder_task(self, telefon, mesaj):
    """
    Asenkron SMS gönderme görevi.
    Gerçek SMS Gateway API bağlantısı yapılandırılana kadar simüle eder.
    """
    logger.info(f"SMS GÖNDERİLİYOR: -> {telefon} | Mesaj: {mesaj}")
    
    try:
        # İleride SMS servisi buraya entegre edilecek
        # from app.services.sms_servisi import sms_api_cagir
        # api_key = current_app.config.get('SMS_API_KEY')
        # sender = current_app.config.get('SMS_SENDER_ID')
        # sms_api_cagir(telefon, mesaj, api_key, sender)
        
        logger.info(f"SMS BAŞARIYLA GÖNDERİLDİ: -> {telefon}")
        return True
    except Exception as exc:
        logger.error(f"SMS GÖNDERİM HATASI: {exc}")
        self.retry(exc=exc, countdown=60)


@celery.task
def periyodik_hatirlatma_task():
    """
    Periyodik kontrol görevi (Sözleşme süreleri, eğitimler, bakım zamanları).
    Celery Beat ile her gün gece 02:00'de çalıştırılmak üzere planlanabilir.
    """
    logger.info("PERİYODİK HATIRLATMA GÖREVİ BAŞLADI.")
    
    # İleride her modülün servis fonksiyonu çağrılacak:
    # sozlesme_servisi.hatirlatma_kontrol()
    # isg_hatirlatici.kontrol_et()
    
    logger.info("PERİYODİK HATIRLATMA GÖREVİ TAMAMLANDI.")
    return True
