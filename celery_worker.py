"""
FDYS — Celery Worker Başlatıcı

Asenkron görevleri (e-posta, SMS, OCR vb.) arka planda çalıştırmak için 
kullanılan Celery worker'ını başlatır.

Çalıştırmak için: celery -A celery_worker.celery worker --loglevel=info
"""

import os
from app import create_app
from celery import Celery

def make_celery(app):
    """Flask uygulaması ile entegre bir Celery nesnesi oluşturur."""
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    # Celery task'larının Flask uygulama context'i içinde çalışmasını sağlayan class
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

# Uygulamayı yükle
app = create_app(os.environ.get('FDYS_CONFIG', 'development'))

# Celery nesnesini oluştur
celery = make_celery(app)

# Task'ları projeden içeri aktar (kaydedilmesi için gerekli)
import app.tasks
