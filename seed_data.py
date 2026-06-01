"""
FabrikaOS — Ana Veri Doldurma Scripti (v2 — Kapsamlı Demo Verisi)
Senaryo: AnadoluTech Metal Sanayi A.Ş.

Bu script, veritabanını sıfırlayarak tüm modüller için
kapsamlı ve birbiriyle ilişkili, gerçekçi endüstriyel demo verisi üretir.

UYARI: ÇALIŞTIRMADAN ÖNCE VERİTABANINDAKİ TÜM VERİLER SİLİNECEKTİR!
"""
import os
import sys

# Proje kök dizinini Python yoluna ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db

# Seed modüllerini içe aktar
from seeds import (
    seed_kullanici,
    seed_makine,
    seed_uretim,
    seed_stok,
    seed_vardiya,
    seed_kalite,
    seed_enerji,
    seed_isg,
    seed_ik,
    seed_bildirim,
    seed_is_emri,
    seed_analitik,
    seed_tahmin,
    seed_crm,
    seed_sozlesme,
    seed_talep,
    seed_satin_alma,
    seed_dys,
    seed_duyuru,
    seed_dis_kullanici
)


def reset_database():
    """Veritabanını sıfırlar ve tabloları yeniden oluşturur."""
    print("🗑️  Mevcut veritabanı temizleniyor...")
    db.drop_all()
    print("🏗️  Tablolar yeniden oluşturuluyor...")
    db.create_all()
    print("✅ Veritabanı başarıyla sıfırlandı.\n")


def run_seeds():
    """Tüm seed fonksiyonlarını bağımlılık sırasına göre çalıştırır."""
    app = create_app()
    with app.app_context():
        print("="*60)
        print("  🏭 FabrikaOS Demo Veri Oluşturucu v2 (Tam Kapsam) 🏭")
        print("="*60)
        
        reset_database()
        
        # SIRA ÖNEMLİDİR (Bağımlılık zinciri)
        try:
            # 1. Temel Tanımlar (Kullanıcı ve Çalışanlar)
            seed_kullanici.seed()
            
            # 2. Makine ve Üretim Temeli
            seed_makine.seed()
            seed_uretim.seed()
            
            # 3. Lojistik ve Personel Operasyonları
            seed_stok.seed()
            seed_vardiya.seed()
            
            # 4. Kalite ve Enerji
            seed_kalite.seed()
            seed_enerji.seed()
            
            # 5. İSG ve İK
            seed_isg.seed()
            seed_ik.seed()
            
            # 6. CRM ve Finans
            seed_crm.seed()
            seed_dis_kullanici.seed()
            
            # 7. İş Akışları ve Talepler
            seed_sozlesme.seed()
            seed_talep.seed()
            seed_satin_alma.seed()
            
            # 8. İş Emirleri ve Bakım Süreçleri
            seed_is_emri.seed()
            
            # 9. Kurumsal Modüller
            seed_dys.seed()
            seed_duyuru.seed()
            
            # 10. Sistem ve Analitik
            seed_bildirim.seed()
            seed_analitik.seed()
            seed_tahmin.seed()

            db.session.commit()
            
            print("="*60)
            print("🎉 BÜTÜN DEMO VERİLERİ BAŞARIYLA OLUŞTURULDU! 🎉")
            print("="*60)
            print("\nGiriş yapabileceğiniz bazı hesaplar:")
            print("  Yönetici       : admin / admin123")
            print("  İSG Uzmanı     : selin.aktas / demo123")
            print("  Bakım Teknisyeni: mehmet.kaya / demo123")
            print("  Müşteri        : merve@ford.com.tr / musteri123")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ HATA OLUŞTU: {str(e)}")
            print("İşlem geri alındı.")
            raise e

if __name__ == '__main__':
    run_seeds()
