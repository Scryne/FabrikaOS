from app import create_app
from app.services.ai.oee_tahmin import oee_tahmin_servisi
from app.models.makine import Makine

app = create_app()
with app.app_context():
    makineler = Makine.query.all()
    for m in makineler:
        tahmin = oee_tahmin_servisi._makine_oee_tahmin(m)
        if tahmin:
            print(f"Makine: {m.ad}")
            print(f"Gecmis: {tahmin['gecmis']['values']}")
            print(f"Tahmin: {tahmin['tahmin']['values']}")
            print(f"Risk: {tahmin['risk_skoru']}")
            print("---")
