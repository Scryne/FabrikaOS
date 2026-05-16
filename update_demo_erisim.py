"""Mevcut demo hesaplarının modül erişimlerini günceller."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.extensions import db
from app.models.kullanici import Kullanici
import json

app = create_app()

UPDATES = {
    'ahmet.yilmaz': {'personel': True, 'makine': True, 'stok': True, 'kalite': True, 'isg': True},
    'fatma.demir': {'personel': True, 'makine': True, 'stok': True, 'kalite': True, 'isg': True},
    'mehmet.kaya': {'makine': True, 'stok': True, 'enerji': True, 'isg': True},
    'ayse.ozkan': {'makine': True, 'stok': True, 'enerji': True, 'isg': True},
}

with app.app_context():
    for username, erisim in UPDATES.items():
        user = Kullanici.query.filter_by(kullanici_adi=username).first()
        if user:
            user.modul_erisim = erisim
            print(f"[OK] {user.ad_soyad} ({username}) guncellendi: {json.dumps(erisim)}")
        else:
            print(f"[!] {username} bulunamadi")
    db.session.commit()
    print("\nTum demo hesaplar basariyla guncellendi!")
