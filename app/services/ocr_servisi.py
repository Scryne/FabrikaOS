"""
FDYS — OCR Servisi
Faz 2 — Optik Karakter Tanıma İşlemleri

Tesseract (pytesseract) ve OpenCV kullanarak
taranan belge veya görsellerden metin çıkarır.
Bu servis, belgelerin aranabilir olmasını sağlar (Özellikle CRM arşivi için).
"""

import os
import logging
import re
from flask import current_app

logger = logging.getLogger(__name__)


def extract_text_from_image(image_path):
    """
    Belirtilen görüntü dosyasından Tesseract kullanarak metin çıkarır.

    Args:
        image_path: Görüntü dosyasının tam yolu

    Returns:
        str: Çıkarılan metin (başarısız olursa boş string)
    """
    if not os.path.exists(image_path):
        logger.error(f"OCR hatası: Dosya bulunamadı - {image_path}")
        return ""

    try:
        from PIL import Image
        import pytesseract

        # Tesseract yolu config'ten alınabilir veya sistemde default kullanılabilir
        tesseract_cmd = current_app.config.get('OCR_ENGINE')
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        # Görüntüyü aç
        img = Image.open(image_path)

        # Temel görüntü ön işleme (OpenCV varsa daha iyi sonuç verir, ama PIL ile basit)
        # Siyah beyaz yap
        img = img.convert('L')

        # Türkçe (tur) ve İngilizce (eng) dillerini destekleyerek metni çıkar
        # Eğer sistemde Türkçe paketi yoksa hata verebilir, eng ile de denenebilir.
        try:
            text = pytesseract.image_to_string(img, lang='tur+eng')
        except pytesseract.TesseractError:
            logger.warning("Türkçe Tesseract paketi bulunamadı, varsayılan dille deneniyor...")
            text = pytesseract.image_to_string(img)

        # Fazla boşlukları temizle
        text = re.sub(r'\n+', '\n', text)
        return text.strip()

    except ImportError:
        logger.error("OCR hatası: pytesseract veya Pillow yüklü değil.")
        return "OCR servisi kullanılamıyor (Gerekli kütüphaneler eksik)."
    except Exception as e:
        logger.error(f"OCR çıkarma hatası: {str(e)}")
        return ""


def clean_ocr_text(text):
    """
    Çıkarılan OCR metnini temizler ve arama için optimize eder.
    (Noktalama işaretlerini azaltma, küçük harfe çevirme vb.)
    """
    if not text:
        return ""
        
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
