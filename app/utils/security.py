"""
FDYS — Güvenlik Yardımcı Fonksiyonları (Faz 2)
"""

import os

def is_secure_image(file_stream, filename):
    """
    Yüklenen dosyanın gerçekten bir resim dosyası (JPEG/PNG) olup olmadığını magic bytes kontrolü ile yapar.
    Ayrıca uzantı kontrolü de içerir.
    """
    ext = filename.split('.')[-1].lower()
    if ext not in ['jpg', 'jpeg', 'png']:
        return False

    # Magic bytes kontrolü için ilk 32 byte'ı oku
    header = file_stream.read(32)
    file_stream.seek(0)  # Stream'i tekrar başa sar

    if ext in ['jpg', 'jpeg']:
        # JPEG dosyaları \xFF\xD8\xFF ile başlar
        return header.startswith(b'\xff\xd8\xff')
    elif ext == 'png':
        # PNG dosyaları \x89PNG\r\n\x1a\n ile başlar
        return header.startswith(b'\x89PNG\r\n\x1a\n')
    
    return False

def is_strong_password(password):
    """
    Şifrenin güvenlik politikasını karşılayıp karşılamadığını kontrol eder:
    - En az 8 karakter
    - En az 1 büyük harf
    - En az 1 küçük harf
    - En az 1 rakam
    - En az 1 özel karakter
    """
    if len(password) < 8:
        return False, "Şifre en az 8 karakter olmalıdır."
    if not any(char.isupper() for char in password):
        return False, "Şifre en az 1 büyük harf içermelidir."
    if not any(char.islower() for char in password):
        return False, "Şifre en az 1 küçük harf içermelidir."
    if not any(char.isdigit() for char in password):
        return False, "Şifre en az 1 rakam içermelidir."
    if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?" for char in password):
        return False, "Şifre en az 1 özel karakter (!@#$%^&* vb.) içermelidir."
        
    return True, ""
