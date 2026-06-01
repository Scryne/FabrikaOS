"""
FDYS - Fabrika Dijital Yönetim Sistemi
Konfigürasyon Dosyası

Geliştirme (Development) ve Üretim (Production) ortamlarının
ayrı yapılandırması bu dosyada tanımlanmıştır.
"""

import os
from datetime import timedelta

# Proje kök dizini
basedir = os.path.abspath(os.path.dirname(__file__))


def _is_sqlite(uri):
    """Veritabanı URI'sinin SQLite olup olmadığını kontrol eder."""
    return uri and uri.startswith('sqlite')


class Config:
    """Temel yapılandırma sınıfı — tüm ortamların ortak ayarları."""

    # Flask Güvenlik
    SECRET_KEY = os.environ.get('FDYS_SECRET_KEY') or 'degistir-bu-anahtari-uretimde'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # CSRF token geçerlilik süresi: 1 saat
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1) # Oturum 1 saat sonra kapanır

    # JWT Ayarları
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-degistir-bu-anahtari-uretimde'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ['headers']

    # SocketIO
    SOCKETIO_CORS_ALLOWED_ORIGINS = os.environ.get('SOCKETIO_CORS_ALLOWED_ORIGINS', '*')

    # Veritabanı
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'fdys.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'check_same_thread': False},  # SQLite varsayılan
    }

    # Oturum Yönetimi
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Flask-Login
    LOGIN_DISABLED = False

    # Flask-Limiter — Brute Force Koruması
    RATELIMIT_DEFAULT = "200 per hour"
    RATELIMIT_STORAGE_URI = "memory://"

    # Flask-Caching
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300  # 5 dakika

    # Uygulama Ayarları
    FDYS_ADMIN_USERNAME = 'admin'
    FDYS_APP_NAME = 'FDYS — Fabrika Dijital Yönetim Sistemi'
    FDYS_VERSION = '1.0.0'

    # Dosya Yükleme
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32 MB maksimum dosya boyutu
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv'}

    # Logging Ayarları
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    DEBUG_SQL = os.environ.get('DEBUG_SQL', 'False').lower() == 'true'

    # Celery & Asenkron Görevler
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

    # SMS Gateway Ayarları (Faz 4 için altyapı)
    SMS_GATEWAY_URL = os.environ.get('SMS_GATEWAY_URL', '')
    SMS_API_KEY = os.environ.get('SMS_API_KEY', '')
    SMS_SENDER_ID = os.environ.get('SMS_SENDER_ID', 'FABRIKA_OS')

    # OCR Ayarları (Faz 2 için altyapı)
    OCR_ENGINE = os.environ.get('OCR_ENGINE', 'tesseract')

    # SQLite WAL Modu (Performans + Yazma Güvenliği) — Sadece SQLite'da etkindir
    SQLITE_WAL_MODE = True

    @staticmethod
    def init_app(app):
        """Uygulama başlatma kancası — veritabanı türüne göre engine ayarlarını yapılandırır."""
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if not _is_sqlite(db_uri):
            # PostgreSQL / diğer veritabanları için connection pooling
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),
                'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 20)),
                'pool_timeout': 30,
                'pool_recycle': 1800,   # 30 dk'da bir bağlantıyı yenile
                'pool_pre_ping': True,  # Bağlantı sağlığını kontrol et
            }


class DevelopmentConfig(Config):
    """Geliştirme ortamı yapılandırması."""

    DEBUG = True
    SQLALCHEMY_ECHO = False  # SQL sorgularını loglama (gerektiğinde True yap)

    # Geliştirmede daha rahat rate limit
    RATELIMIT_DEFAULT = "1000 per hour"


class ProductionConfig(Config):
    """Üretim ortamı yapılandırması."""

    DEBUG = False

    # Üretimde PostgreSQL önerilir
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'fdys.db')

    # Üretimde güvenlik sıkılaştırma
    SESSION_COOKIE_SECURE = True  # Üretimde HTTPS olmalı
    SESSION_COOKIE_HTTPONLY = True
    WTF_CSRF_TIME_LIMIT = 1800  # 30 dakika

    # SocketIO CORS
    SOCKETIO_CORS_ALLOWED_ORIGINS = os.environ.get('SOCKETIO_CORS_ALLOWED_ORIGINS', '').split(',') if os.environ.get('SOCKETIO_CORS_ALLOWED_ORIGINS') else []

    # Daha sıkı rate limit
    RATELIMIT_DEFAULT = "100 per hour"

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        # Üretimde SECRET_KEY kontrolü zorunludur
        if app.config.get('SECRET_KEY') == 'degistir-bu-anahtari-uretimde' or not app.config.get('SECRET_KEY'):
            raise ValueError(
                'KRİTİK GÜVENLİK HATASI: Üretim ortamında (production) uygulamanın çalışabilmesi için '
                'geçerli bir FDYS_SECRET_KEY ortam değişkeni tanımlanmalıdır!'
            )


class TestingConfig(Config):
    """Test ortamı yapılandırması."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    LOGIN_DISABLED = False


# Yapılandırma haritası
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
