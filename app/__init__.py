"""
FDYS — Fabrika Dijital Yönetim Sistemi
Uygulama Fabrikası (Application Factory)

Bu dosya Flask uygulama fabrikası pattern'ini kullanarak
uygulamayı oluşturur. Bu yapı test, geliştirme ve üretim
ortamlarının aynı kod tabanıyla çalışmasını sağlar.
"""

import os
from flask import Flask
from config import config


def create_app(config_name=None):
    """
    Flask uygulamasını oluşturur ve yapılandırır.

    Args:
        config_name: Yapılandırma adı ('development', 'production', 'testing')

    Returns:
        Yapılandırılmış Flask uygulama nesnesi
    """
    if config_name is None:
        config_name = os.environ.get('FDYS_CONFIG', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # ── Uzantıları Başlat ──
    _register_extensions(app)

    # ── Blueprint'leri Kaydet ──
    _register_blueprints(app)

    # ── Hata İşleyicileri ──
    _register_error_handlers(app)

    # ── Shell Context ──
    _register_shell_context(app)

    # ── Jinja2 Yardımcıları ──
    _register_template_helpers(app)

    # ── Güvenlik Başlıkları ──
    _register_security_headers(app)

    # ── SQLite WAL Modu ──
    _configure_sqlite(app)

    # ── Instance klasörünü oluştur ──
    _ensure_instance_folder(app)

    return app


def _register_extensions(app):
    """Tüm Flask uzantılarını uygulamaya bağlar."""
    from app.extensions import (
        db, migrate, login_manager, bcrypt,
        csrf, cache, limiter, socketio
    )

    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    socketio.init_app(app, async_mode='eventlet', cors_allowed_origins=app.config.get('SOCKETIO_CORS_ALLOWED_ORIGINS', '*'))

    # Flask-Login kullanıcı yükleyici
    from app.models.kullanici import Kullanici

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Kullanici, int(user_id))


def _register_blueprints(app):
    """Tüm blueprint'leri uygulamaya kaydeder."""
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.personel import personel_bp
    from app.routes.makine import makine_bp
    from app.routes.stok import stok_bp
    from app.routes.kalite import kalite_bp
    from app.routes.enerji import enerji_bp
    from app.routes.isg import isg_bp
    from app.routes.rapor import rapor_bp
    from app.routes.admin import admin_bp
    from app.routes.fabrika_harita import fabrika_harita_bp
    from app.routes.tahmin import tahmin_bp
    from app.routes.is_emri import is_emri_bp
    from app.routes.analitik import analitik_bp
    from app.routes.otomasyon import otomasyon_bp
    from app.routes.dosya import dosya_bp
    from app.routes.takvim import takvim_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(personel_bp)
    app.register_blueprint(makine_bp)
    app.register_blueprint(stok_bp)
    app.register_blueprint(kalite_bp)
    app.register_blueprint(enerji_bp)
    app.register_blueprint(isg_bp)
    app.register_blueprint(rapor_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(fabrika_harita_bp)
    app.register_blueprint(tahmin_bp)
    app.register_blueprint(is_emri_bp)
    app.register_blueprint(analitik_bp)
    app.register_blueprint(otomasyon_bp)
    app.register_blueprint(dosya_bp)
    app.register_blueprint(takvim_bp)


def _register_error_handlers(app):
    """HTTP hata işleyicilerini kaydeder."""
    from flask import render_template

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500


def _register_shell_context(app):
    """Flask shell için bağlam nesneleri sağlar."""
    from app.extensions import db
    from app.models.kullanici import Kullanici
    from app.models.personel import Calisan, VardiyaPlani, IzinTalebi
    from app.models.makine import Makine, UretimVerisi, ArizaKaydi
    from app.models.stok import Malzeme, StokHareketi, Tedarikci
    from app.models.kalite import HataKaydi, DuzelticiFaaliyet
    from app.models.enerji import EnerjiTuketimi
    from app.models.isg import IsKazasi, RiskDegerlendirme, IsgEgitimi
    from app.models.is_emri import IsEmri, IsEmriYorum

    @app.shell_context_processor
    def make_shell_context():
        return {
            'db': db,
            'Kullanici': Kullanici,
            'Calisan': Calisan,
            'VardiyaPlani': VardiyaPlani,
            'IzinTalebi': IzinTalebi,
            'Makine': Makine,
            'UretimVerisi': UretimVerisi,
            'ArizaKaydi': ArizaKaydi,
            'Malzeme': Malzeme,
            'StokHareketi': StokHareketi,
            'Tedarikci': Tedarikci,
            'HataKaydi': HataKaydi,
            'DuzelticiFaaliyet': DuzelticiFaaliyet,
            'EnerjiTuketimi': EnerjiTuketimi,
            'IsKazasi': IsKazasi,
            'RiskDegerlendirme': RiskDegerlendirme,
            'IsgEgitimi': IsgEgitimi,
            'IsEmri': IsEmri,
            'IsEmriYorum': IsEmriYorum,
        }


def _register_template_helpers(app):
    """Jinja2 template yardımcı fonksiyonlarını kaydeder."""
    from datetime import datetime
    from app.models.kurumsal import KurumsalAyarlar

    @app.context_processor
    def utility_processor():
        # Veritabanı henüz hazır değilse hata vermesin diye try-except eklenebilir, 
        # ancak uygulamanın düzgün çalışması için DB'nin hazır olması beklenir.
        try:
            kurumsal = KurumsalAyarlar.ayarlari_getir()
        except Exception:
            kurumsal = None

        return {
            'app_name': app.config.get('FDYS_APP_NAME', 'FDYS'),
            'app_version': app.config.get('FDYS_VERSION', '1.0.0'),
            'current_year': datetime.now().year,
            'now': datetime.now,
            'kurumsal_ayarlar': kurumsal,
        }

def _register_security_headers(app):
    """Güvenlik başlıklarını (Security Headers) tüm yanıtlara ekler."""
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Sıkı bir Content-Security-Policy (CSP) (Dış kaynaklara izin veren ancak inline script'leri hash/nonce harici reddeden)
        # Geliştirme kolaylığı için şimdilik biraz esnek, production'da sıkılaştırılabilir.
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.socket.io; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' ws: wss:;"
        )
        response.headers['Content-Security-Policy'] = csp
        return response

def _configure_sqlite(app):
    """SQLite WAL modunu ve optimizasyonlarını etkinleştirir (sadece SQLite için)."""
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if not db_uri.startswith('sqlite'):
        return  # PostgreSQL veya diğer DB'lerde SQLite PRAGMA'ları çalıştırılmaz

    if app.config.get('SQLITE_WAL_MODE'):
        from sqlalchemy import event
        from sqlalchemy.engine import Engine

        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
            cursor.execute("PRAGMA mmap_size=268435456")  # 256MB mmap
            cursor.close()


def _ensure_instance_folder(app):
    """Instance klasörünün var olmasını sağlar."""
    instance_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance')
    os.makedirs(instance_path, exist_ok=True)

    # Upload klasörünü oluştur
    upload_path = app.config.get('UPLOAD_FOLDER')
    if upload_path:
        os.makedirs(upload_path, exist_ok=True)
