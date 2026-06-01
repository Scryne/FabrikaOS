from app.extensions import db
from app.models.kalite import HataKaydi
from app import create_app
from sqlalchemy import func
from datetime import datetime, timedelta, timezone

app = create_app()
with app.app_context():
    yedi_gun_once = datetime.now(timezone.utc) - timedelta(days=7)
    gunluk_trend = db.session.query(
        func.date(HataKaydi.tarih), func.sum(HataKaydi.adet)
    ).filter(HataKaydi.tarih >= yedi_gun_once)\
     .group_by(func.date(HataKaydi.tarih))\
     .order_by(func.date(HataKaydi.tarih)).all()

    print("gunluk_trend:", gunluk_trend)
    trend_labels = [d[0] if isinstance(d[0], str) else d[0].strftime('%d.%m') if d[0] else '' for d in gunluk_trend]
    trend_values = [int(d[1]) for d in gunluk_trend]
    print("trend_labels:", trend_labels)
    print("trend_values:", trend_values)
