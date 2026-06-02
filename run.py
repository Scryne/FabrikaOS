"""
FDYS - Fabrika Dijital Yönetim Sistemi
Ana Başlatma Dosyası

Kullanım:
    python run.py                    → Geliştirme modunda başlat
    FDYS_CONFIG=production python run.py → Üretim modunda başlat

LAN Erişimi:
    host='0.0.0.0' ayarı sayesinde aynı ağdaki tüm bilgisayarlar
    http://[sunucu-ip]:5000 adresinden sisteme erişebilir.
"""

import os
from app import create_app
from app.extensions import socketio

# Ortam değişkeninden yapılandırma seç (varsayılan: development)
config_name = os.environ.get('FDYS_CONFIG', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    host = os.environ.get('FDYS_HOST', '0.0.0.0')
    port = int(os.environ.get('FDYS_PORT', 5000))
    debug = config_name == 'development'

    print(f"""
    +------------------------------------------------------+
    |     FDYS - Fabrika Dijital Yonetim Sistemi          |
    |     Surum: 1.0.0                                   |
    +------------------------------------------------------+
    |  Sunucu: http://{host}:{port}                       |
    |  Ortam:  {config_name.upper():50s}|
    |  Debug:  {str(debug):50s}|
    +------------------------------------------------------+
    """)

    # Yaşayan Demo - Mock Data Engine'i Başlat
    try:
        from app.services.mock_engine import MockDataEngine
        mock_engine = MockDataEngine(app)
        mock_engine.start()
    except Exception:
        pass

    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=debug  # Sadece geliştirme ortamında izin ver
    )
