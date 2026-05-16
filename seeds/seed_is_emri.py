"""
FabrikaOS — İş Emri Demo Verileri
Senaryo: AnadoluTech Metal Sanayi A.Ş.
"""

from datetime import datetime, timedelta, timezone
from app.extensions import db
from app.models.is_emri import IsEmri, IsEmriYorum
from app.models.kullanici import Kullanici


def seed():
    print('[10/12] İş Emri demo verileri yükleniyor...')

    # Kullanıcıları al
    admin = Kullanici.query.filter_by(kullanici_adi='admin').first()
    teknisyen1 = Kullanici.query.filter_by(kullanici_adi='mehmet.kaya').first()
    teknisyen2 = Kullanici.query.filter_by(kullanici_adi='ayse.ozkan').first()
    operator1 = Kullanici.query.filter_by(kullanici_adi='ahmet.yilmaz').first()

    if not admin:
        print('  ! Kullanıcılar bulunamadı, is_emri seed atlanıyor.')
        return

    simdi = datetime.now(timezone.utc)
    sayac = [0]

    def _numara():
        sayac[0] += 1
        return f'IE-2026-{sayac[0]:04d}'

    is_emirleri = [
            # Tamamlanmış arıza iş emri
            {
                'is_emri_no': _numara(), 'baslik': 'CNC-01 Spindle Motor Arızası',
                'aciklama': 'Spindle motor aşırı ısınma tespit edildi. Acil müdahale gerekiyor.',
                'kaynak_modul': 'makine', 'kategori': 'ariza', 'oncelik': 'kritik', 'durum': 'onaylandi',
                'olusturan_id': operator1.id if operator1 else admin.id,
                'atanan_id': teknisyen1.id if teknisyen1 else admin.id,
                'onaylayan_id': admin.id, 'sla_saat': 4,
                'baslama_zamani': simdi - timedelta(days=5, hours=3),
                'tamamlanma_zamani': simdi - timedelta(days=5, hours=1),
                'onay_zamani': simdi - timedelta(days=4),
                'gercek_sure_dk': 120, 'cozum_notu': 'Motor rulmanları değiştirildi, soğutma sistemi temizlendi.',
                'olusturma_tarihi': simdi - timedelta(days=6),
            },
            # Devam eden bakım
            {
                'is_emri_no': _numara(), 'baslik': 'Pres-03 Periyodik Bakım',
                'aciklama': '90 günlük periyodik bakım planına göre bakım yapılması gerekmektedir.',
                'kaynak_modul': 'bakim', 'kategori': 'bakim', 'oncelik': 'normal', 'durum': 'devam',
                'olusturan_id': admin.id,
                'atanan_id': teknisyen2.id if teknisyen2 else admin.id,
                'sla_saat': 24,
                'baslama_zamani': simdi - timedelta(hours=4),
                'olusturma_tarihi': simdi - timedelta(days=1),
            },
            # Açık satın alma talebi
            {
                'is_emri_no': _numara(), 'baslik': 'Hidrolik Yağ Acil Satın Alma',
                'aciklama': 'Hidrolik yağ stoku kritik seviyenin altına düştü. Acil tedarik gerekli.',
                'kaynak_modul': 'stok', 'kategori': 'satin_alma', 'oncelik': 'yuksek', 'durum': 'acik',
                'olusturan_id': admin.id, 'sla_saat': 8,
                'olusturma_tarihi': simdi - timedelta(hours=6),
            },
            # Atandı durumunda
            {
                'is_emri_no': _numara(), 'baslik': 'Kaynak Robotu Kalibrasyon',
                'aciklama': 'Kaynak robotu R-02 kalibrasyon sapması gösteriyor. Yeniden kalibrasyon yapılmalı.',
                'kaynak_modul': 'makine', 'kategori': 'bakim', 'oncelik': 'yuksek', 'durum': 'atandi',
                'olusturan_id': admin.id,
                'atanan_id': teknisyen1.id if teknisyen1 else admin.id,
                'sla_saat': 8,
                'olusturma_tarihi': simdi - timedelta(hours=3),
            },
            # Tamamlandı ama onay bekliyor
            {
                'is_emri_no': _numara(), 'baslik': 'ISG Eğitim Salonu Düzenlemesi',
                'aciklama': 'Yeni personel için ISG eğitim salonu yeniden düzenlenmeli, güvenlik ekipmanları kontrol edilmeli.',
                'kaynak_modul': 'isg', 'kategori': 'egitim', 'oncelik': 'dusuk', 'durum': 'tamamlandi',
                'olusturan_id': admin.id,
                'atanan_id': operator1.id if operator1 else admin.id,
                'sla_saat': 72,
                'tamamlanma_zamani': simdi - timedelta(hours=2),
                'cozum_notu': 'Salon düzenlendi, ekipmanlar kontrol edildi ve eksikler tamamlandı.',
                'olusturma_tarihi': simdi - timedelta(days=2),
            },
            # Eski tamamlanmış iş emirleri
            {
                'is_emri_no': _numara(), 'baslik': 'Torna T-02 Rulman Değişimi',
                'aciklama': 'Torna T-02 ana miller rulmanlarından titreşim algılandı.',
                'kaynak_modul': 'makine', 'kategori': 'ariza', 'oncelik': 'yuksek', 'durum': 'onaylandi',
                'olusturan_id': operator1.id if operator1 else admin.id,
                'atanan_id': teknisyen1.id if teknisyen1 else admin.id,
                'onaylayan_id': admin.id, 'sla_saat': 8,
                'gercek_sure_dk': 180, 'cozum_notu': 'Rulmanlar değiştirildi, titreşim testi başarılı.',
                'olusturma_tarihi': simdi - timedelta(days=10),
            },
            {
                'is_emri_no': _numara(), 'baslik': 'Kompresör Filtre Değişimi',
                'aciklama': 'Basınçlı hava kompresörü filtre ömrünü tamamladı.',
                'kaynak_modul': 'bakim', 'kategori': 'bakim', 'oncelik': 'normal', 'durum': 'onaylandi',
                'olusturan_id': admin.id,
                'atanan_id': teknisyen2.id if teknisyen2 else admin.id,
                'onaylayan_id': admin.id, 'sla_saat': 24,
                'gercek_sure_dk': 45, 'cozum_notu': 'Filtreler değiştirildi, basınç testi yapıldı.',
                'olusturma_tarihi': simdi - timedelta(days=8),
            },
            # Genel iş emri
            {
                'is_emri_no': _numara(), 'baslik': 'Üretim Alanı Zemin Boyama',
                'aciklama': '5S kapsamında üretim alanı zemin çizgileri yenilenecek.',
                'kaynak_modul': 'manuel', 'kategori': 'genel', 'oncelik': 'dusuk', 'durum': 'acik',
                'olusturan_id': admin.id, 'sla_saat': 72,
                'olusturma_tarihi': simdi - timedelta(days=1),
            },
            # İptal edilmiş
            {
                'is_emri_no': _numara(), 'baslik': 'CNC-03 Soğutma Suyu Kaçağı',
                'aciklama': 'Soğutma suyu kaçağı rapor edildi ancak yanlış alarm olduğu tespit edildi.',
                'kaynak_modul': 'makine', 'kategori': 'ariza', 'oncelik': 'normal', 'durum': 'iptal',
                'olusturan_id': operator1.id if operator1 else admin.id,
                'sla_saat': 24,
                'olusturma_tarihi': simdi - timedelta(days=3),
            },
            # Kritik açık
            {
                'is_emri_no': _numara(), 'baslik': 'Elektrik Panosu Isınma Sorunu',
                'aciklama': 'Ana elektrik panosunda anormal ısınma tespit edildi. Yangın riski mevcut.',
                'kaynak_modul': 'makine', 'kategori': 'ariza', 'oncelik': 'kritik', 'durum': 'acik',
                'olusturan_id': admin.id, 'sla_saat': 4,
                'olusturma_tarihi': simdi - timedelta(hours=2),
            },
        ]

    for ie_data in is_emirleri:
        ie = IsEmri(**ie_data)
        ie.sla_hesapla()
        ie.sla_kontrol()
        db.session.add(ie)
    db.session.flush()

    # Yorumlar ekle
    tum_emirler = IsEmri.query.all()
    yorumlar = [
        ('Müdahale işlemi başladı.', teknisyen1),
        ('Yedek parça depoya geldi, montaj başlıyor.', teknisyen1),
        ('İş tamamlandı, test sonuçları olumlu.', teknisyen1),
        ('Bakım formu dolduruldu, kontrol listesi tamamlandı.', teknisyen2),
        ('Tedarikçi ile iletişime geçildi, 2 gün içinde teslimat bekleniyor.', admin),
    ]

    for i, ie in enumerate(tum_emirler[:5]):
        icerik, kullanici = yorumlar[i % len(yorumlar)]
        yorum = IsEmriYorum(
            is_emri_id=ie.id,
            kullanici_id=(kullanici.id if kullanici else admin.id),
            icerik=icerik,
            olusturma_tarihi=ie.olusturma_tarihi + timedelta(hours=1)
        )
        db.session.add(yorum)

    print(f'  OK {len(is_emirleri)} iş emri ve {min(5, len(tum_emirler))} yorum oluşturuldu')
