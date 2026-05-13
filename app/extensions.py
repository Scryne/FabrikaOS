"""
FDYS — Fabrika Dijital Yönetim Sistemi
Flask Uzantıları (Extensions)

Tüm Flask uzantıları burada başlatılır ve create_app()
tarafından uygulamaya bağlanır. Bu pattern, döngüsel import
sorunlarını önler.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO
from flask_migrate import Migrate

# ── Veritabanı ──
from sqlalchemy import MetaData

naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))

# ── Veritabanı Migration ──
migrate = Migrate()

# ── Kimlik Doğrulama ──
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Bu sayfaya erişmek için giriş yapmanız gerekiyor.'
login_manager.login_message_category = 'warning'
login_manager.session_protection = 'strong'

# ── Şifre Hashleme ──
bcrypt = Bcrypt()

# ── CSRF Koruması ──
csrf = CSRFProtect()

# ── Önbellek ──
cache = Cache()

# ── Rate Limiting ──
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per hour"],
    storage_uri="memory://"
)

# ── WebSocket (Gerçek Zamanlı Bildirimler) ──
socketio = SocketIO()
