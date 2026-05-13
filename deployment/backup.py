"""
FDYS — Otomatik Yedekleme Betiği
Bu betik, üretim ortamındaki veritabanını ve yüklenen dosyaları
düzenli aralıklarla yedeklemek için tasarlanmıştır. Windows Görev Zamanlayıcı
(Task Scheduler) veya Linux Cron ile günlük çalıştırılabilir.
"""

import os
import zipfile
import shutil
from datetime import datetime, timedelta

# Dizin ayarları
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'fdys.db')
UPLOADS_PATH = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')
RETENTION_DAYS = 7  # Kaç günlük yedek tutulacak?

def create_backup():
    """Veritabanı ve yüklemeleri zipleyerek yedeğini alır."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"fdys_backup_{timestamp}.zip"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    print(f"[*] Yedekleme başlatılıyor: {backup_filename}")

    try:
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Veritabanını ekle
            if os.path.exists(DB_PATH):
                zipf.write(DB_PATH, os.path.basename(DB_PATH))
                print(f" [+] Eklendi: {os.path.basename(DB_PATH)}")
            else:
                print(" [-] UYARI: fdys.db bulunamadı!")

            # Uploads klasörünü ekle
            if os.path.exists(UPLOADS_PATH):
                for root, dirs, files in os.walk(UPLOADS_PATH):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, BASE_DIR)
                        zipf.write(file_path, arcname)
                print(" [+] Eklendi: uploads/ klasörü")
            
        print(f"[OK] Yedekleme başarıyla tamamlandı: {backup_path}")
    except Exception as e:
        print(f"[ERR] Yedekleme sırasında hata oluştu: {e}")

def cleanup_old_backups():
    """Belirtilen günden eski yedek dosyalarını temizler."""
    print(f"[*] Eski yedekler temizleniyor (Eşik: {RETENTION_DAYS} gün)")
    now = datetime.now()
    count = 0
    
    if not os.path.exists(BACKUP_DIR):
        return

    for filename in os.listdir(BACKUP_DIR):
        if not filename.endswith('.zip'):
            continue
            
        file_path = os.path.join(BACKUP_DIR, filename)
        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        
        if now - file_time > timedelta(days=RETENTION_DAYS):
            try:
                os.remove(file_path)
                print(f" [-] Silindi: {filename}")
                count += 1
            except Exception as e:
                print(f" [ERR] Silinirken hata oluştu ({filename}): {e}")
                
    print(f"[OK] {count} adet eski yedek silindi.")

if __name__ == '__main__':
    print("="*50)
    print("FDYS YEDEKLEME SİSTEMİ BAŞLATILDI")
    print("="*50)
    create_backup()
    cleanup_old_backups()
    print("="*50)
