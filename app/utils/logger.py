import os
import logging
from logging.handlers import RotatingFileHandler
from flask import request, has_request_context

class RequestFormatter(logging.Formatter):
    """Her log satırına benzersiz Request ID, URL ve IP ekleyen formatter."""
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
            # Flask'ta request context içinde g tanımlıysa request_id eklenebilir. 
            # İleride bir before_request ile g.request_id = uuid.uuid4().hex eklenebilir.
        else:
            record.url = None
            record.remote_addr = None

        return super().format(record)

def setup_logger(app):
    """Merkezi logging konfigürasyonu."""
    
    # Log dizini oluştur
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, 'fdys.log')

    # File handler: max 10 MB, 5 yedek
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
    
    # Format
    formatter = RequestFormatter(
        '[%(asctime)s] %(levelname)s in %(module)s [%(remote_addr)s - %(url)s]: %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    # Seviye ayarı
    log_level = app.config.get('LOG_LEVEL', logging.INFO)
    file_handler.setLevel(log_level)
    
    app.logger.addHandler(file_handler)
    app.logger.setLevel(log_level)
    
    # SQLAlchemy loglarını da yönlendir (eğer DEBUG aktifse)
    if app.config.get('DEBUG_SQL'):
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
        logging.getLogger('sqlalchemy.engine').addHandler(file_handler)

    app.logger.info('FDYS Uygulaması Başlatıldı - Logging Aktif')
