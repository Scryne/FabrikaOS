import sys
import os

# Proje kök dizinini Python yoluna ekle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db

def test_api():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        client = app.test_client()
        
        # Endpoints
        print("Testing /api/v1/endpoints ...")
        res = client.get('/api/v1/endpoints')
        print(f"Status: {res.status_code}")
        
        # Test stats
        print("Testing /api/v1/istatistik/ozet (unauthorized) ...")
        res = client.get('/api/v1/istatistik/ozet')
        print(f"Status: {res.status_code}") # Should be 401
        
        db.drop_all()
        print("API Test script completed.")

if __name__ == '__main__':
    test_api()
