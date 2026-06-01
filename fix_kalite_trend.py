from app.extensions import db
from app.models.kalite import HataKaydi
from app import create_app
import random
from datetime import datetime, timedelta, timezone

app = create_app()
with app.app_context():
    hatalar = HataKaydi.query.all()
    for h in hatalar:
        # Rastgele 1 ila 14 gün öncesine yay
        gun_once = random.randint(1, 14)
        h.tarih = datetime.now(timezone.utc) - timedelta(days=gun_once)
    db.session.commit()
    print(f"{len(hatalar)} hata kaydının tarihleri güncellendi.")
