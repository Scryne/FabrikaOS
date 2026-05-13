"""
FDYS — Veritabanı Yedekleme Servisi

SQLite ve PostgreSQL veritabanları için yedekleme, listeleme ve silme işlemleri.
Admin panelinden tetiklenir.
"""

import os
import shutil
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Yedekleme dizini: proje_kök/instance/backups
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'instance', 'backups')
MAX_BACKUPS = 10  # Saklanacak maksimum yedek sayısı


def _ensure_backup_dir():
    """Yedekleme dizininin mevcut olduğundan emin olur."""
    os.makedirs(BACKUP_DIR, exist_ok=True)


def yedek_olustur(app):
    """
    Veritabanı yedeği oluşturur.
    
    SQLite: DB dosyasını kopyalar.
    PostgreSQL: pg_dump komutu çalıştırır.
    
    Returns:
        dict: {'basarili': bool, 'dosya_adi': str, 'mesaj': str}
    """
    _ensure_backup_dir()
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    zaman_damgasi = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')

    if db_uri.startswith('sqlite'):
        return _yedekle_sqlite(db_uri, zaman_damgasi)
    elif 'postgresql' in db_uri or 'postgres' in db_uri:
        return _yedekle_postgresql(db_uri, zaman_damgasi)
    else:
        return {
            'basarili': False,
            'dosya_adi': None,
            'mesaj': f'Desteklenmeyen veritabanı türü: {db_uri.split("://")[0]}'
        }


def _yedekle_sqlite(db_uri, zaman_damgasi):
    """SQLite veritabanı dosyasını kopyalar."""
    try:
        # sqlite:///path/to/db → path/to/db
        db_path = db_uri.replace('sqlite:///', '')
        if not os.path.exists(db_path):
            return {'basarili': False, 'dosya_adi': None, 'mesaj': 'Veritabanı dosyası bulunamadı.'}

        dosya_adi = f'fdys_yedek_{zaman_damgasi}.db'
        hedef_yol = os.path.join(BACKUP_DIR, dosya_adi)

        # SQLite WAL modunda güvenli kopyalama
        shutil.copy2(db_path, hedef_yol)

        # WAL ve SHM dosyaları varsa onları da yedekle
        for ext in ('.db-wal', '.db-shm'):
            wal_path = db_path + ext.replace('.db', '')
            if os.path.exists(wal_path):
                shutil.copy2(wal_path, hedef_yol + ext.replace('.db', ''))

        boyut = os.path.getsize(hedef_yol)
        logger.info(f"SQLite yedekleme başarılı: {dosya_adi} ({boyut} bytes)")

        # Eski yedekleri temizle
        _eski_yedekleri_temizle()

        return {
            'basarili': True,
            'dosya_adi': dosya_adi,
            'mesaj': f'Yedekleme başarılı: {dosya_adi} ({_boyut_formatla(boyut)})'
        }
    except Exception as e:
        logger.error(f"SQLite yedekleme hatası: {e}")
        return {'basarili': False, 'dosya_adi': None, 'mesaj': f'Yedekleme hatası: {str(e)}'}


def _yedekle_postgresql(db_uri, zaman_damgasi):
    """PostgreSQL veritabanını pg_dump ile yedekler."""
    try:
        import subprocess
        from urllib.parse import urlparse

        parsed = urlparse(db_uri)
        dosya_adi = f'fdys_yedek_{zaman_damgasi}.sql'
        hedef_yol = os.path.join(BACKUP_DIR, dosya_adi)

        env = os.environ.copy()
        if parsed.password:
            env['PGPASSWORD'] = parsed.password

        cmd = [
            'pg_dump',
            '-h', parsed.hostname or 'localhost',
            '-p', str(parsed.port or 5432),
            '-U', parsed.username or 'postgres',
            '-d', parsed.path.lstrip('/'),
            '-F', 'p',  # Plain text format
            '-f', hedef_yol,
        ]

        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            return {
                'basarili': False,
                'dosya_adi': None,
                'mesaj': f'pg_dump hatası: {result.stderr[:200]}'
            }

        boyut = os.path.getsize(hedef_yol)
        logger.info(f"PostgreSQL yedekleme başarılı: {dosya_adi} ({boyut} bytes)")
        _eski_yedekleri_temizle()

        return {
            'basarili': True,
            'dosya_adi': dosya_adi,
            'mesaj': f'Yedekleme başarılı: {dosya_adi} ({_boyut_formatla(boyut)})'
        }
    except FileNotFoundError:
        return {'basarili': False, 'dosya_adi': None, 'mesaj': 'pg_dump komutu bulunamadı. PostgreSQL client kurulu olmalıdır.'}
    except Exception as e:
        logger.error(f"PostgreSQL yedekleme hatası: {e}")
        return {'basarili': False, 'dosya_adi': None, 'mesaj': f'Yedekleme hatası: {str(e)}'}


def yedekleri_listele():
    """
    Mevcut yedek dosyalarını listeler.
    
    Returns:
        list[dict]: [{'dosya_adi': str, 'boyut': int, 'boyut_str': str, 'tarih': str}]
    """
    _ensure_backup_dir()
    yedekler = []

    for dosya in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if dosya.startswith('fdys_yedek_') and (dosya.endswith('.db') or dosya.endswith('.sql')):
            yol = os.path.join(BACKUP_DIR, dosya)
            boyut = os.path.getsize(yol)
            mod_zamani = datetime.fromtimestamp(os.path.getmtime(yol), tz=timezone.utc)

            yedekler.append({
                'dosya_adi': dosya,
                'boyut': boyut,
                'boyut_str': _boyut_formatla(boyut),
                'tarih': mod_zamani.strftime('%d.%m.%Y %H:%M'),
                'tur': 'SQLite' if dosya.endswith('.db') else 'PostgreSQL',
            })

    return yedekler


def yedek_sil(dosya_adi):
    """
    Belirtilen yedek dosyasını güvenli bir şekilde siler.
    
    Returns:
        dict: {'basarili': bool, 'mesaj': str}
    """
    # Güvenlik: sadece yedek dosyalarına izin ver
    if not dosya_adi.startswith('fdys_yedek_') or '..' in dosya_adi:
        return {'basarili': False, 'mesaj': 'Geçersiz dosya adı.'}

    yol = os.path.join(BACKUP_DIR, dosya_adi)
    if not os.path.exists(yol):
        return {'basarili': False, 'mesaj': 'Dosya bulunamadı.'}

    try:
        os.remove(yol)
        # İlişkili WAL/SHM dosyalarını da sil
        for ext in ('-wal', '-shm'):
            ilgili = yol + ext
            if os.path.exists(ilgili):
                os.remove(ilgili)

        logger.info(f"Yedek silindi: {dosya_adi}")
        return {'basarili': True, 'mesaj': f'{dosya_adi} silindi.'}
    except Exception as e:
        logger.error(f"Yedek silme hatası: {e}")
        return {'basarili': False, 'mesaj': f'Silme hatası: {str(e)}'}


def yedek_yolu(dosya_adi):
    """
    Yedek dosyasının tam yolunu döner (indirme için).
    Güvenlik kontrolü yapar.
    """
    if not dosya_adi.startswith('fdys_yedek_') or '..' in dosya_adi:
        return None

    yol = os.path.join(BACKUP_DIR, dosya_adi)
    return yol if os.path.exists(yol) else None


def veritabani_boyutu(app):
    """Aktif veritabanının boyutunu döner."""
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_uri.startswith('sqlite'):
        db_path = db_uri.replace('sqlite:///', '')
        if os.path.exists(db_path):
            return _boyut_formatla(os.path.getsize(db_path))
    return 'Bilinmiyor'


def _eski_yedekleri_temizle():
    """MAX_BACKUPS'tan fazla yedek varsa en eskileri siler."""
    yedekler = yedekleri_listele()
    if len(yedekler) > MAX_BACKUPS:
        silinecekler = yedekler[MAX_BACKUPS:]
        for yedek in silinecekler:
            yedek_sil(yedek['dosya_adi'])
            logger.info(f"Eski yedek otomatik temizlendi: {yedek['dosya_adi']}")


def _boyut_formatla(boyut_byte):
    """Byte cinsinden boyutu okunabilir formata çevirir."""
    if boyut_byte < 1024:
        return f'{boyut_byte} B'
    elif boyut_byte < 1024 * 1024:
        return f'{boyut_byte / 1024:.1f} KB'
    elif boyut_byte < 1024 * 1024 * 1024:
        return f'{boyut_byte / (1024 * 1024):.1f} MB'
    else:
        return f'{boyut_byte / (1024 * 1024 * 1024):.1f} GB'
