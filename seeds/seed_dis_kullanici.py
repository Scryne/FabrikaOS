"""
FabrikaOS — Dış Kullanıcı Demo Verisi (YENİ MODÜL)
Taşeron, Müşteri ve Tedarikçiler için portal erişimi, borç ve tahsilat kayıtları
"""
import random
from datetime import datetime, timedelta, timezone
from app.extensions import db
from app.models.dis_kullanici import DisKullanici, Borc, Tahsilat
from app.models.crm import Firma


def seed():
    print('[28/22] Dış Kullanıcılar ve Finans (YENİ)...') # Sembolik

    firmalar = Firma.query.all()
    bugun = datetime.now(timezone.utc)

    if not firmalar:
        print("  Uyarı: Firma bulunamadı, dış kullanıcılar atlanıyor.")
        return

    # ── DIŞ KULLANICI HESAPLARI ──
    dis_kullanicilar = []
    
    # 2 Müşteri, 2 Tedarikçi, 1 Taşeron
    firma_kullanicilari = [
        {'firma': firmalar[0], 'ad': 'Merve Aydın', 'email': 'merve@ford.com.tr', 'kullanici_adi': 'merve.aydin', 'sifre': 'musteri123'},
        {'firma': firmalar[1], 'ad': 'Seda Yılmaz', 'email': 'seda@renault.com.tr', 'kullanici_adi': 'seda.yilmaz', 'sifre': 'musteri123'},
        {'firma': firmalar[2], 'ad': 'Ercan Koçak', 'email': 'ercan@borusan.com.tr', 'kullanici_adi': 'ercan.kocak', 'sifre': 'tedarikci123'},
        {'firma': firmalar[3], 'ad': 'Hakan Demir', 'email': 'hakan@kardemir.com.tr', 'kullanici_adi': 'hakan.demir', 'sifre': 'tedarikci123'},
        {'firma': firmalar[4], 'ad': 'Ali Vefa', 'email': 'ali@abcmakina.com.tr', 'kullanici_adi': 'ali.vefa', 'sifre': 'taseron123'},
    ]

    for fk in firma_kullanicilari:
        dk = DisKullanici(
            kullanici_adi=fk['kullanici_adi'],
            ad_soyad=fk['ad'],
            eposta=fk['email'],
            firma_id=fk['firma'].id,
            aktif=True,
            son_giris=bugun - timedelta(days=random.randint(1, 10)),
            gecici_sifre=False
        )
        dk.sifre_belirle(fk['sifre'])
        db.session.add(dk)
        dis_kullanicilar.append(dk)

    db.session.flush()

    # ── BORÇ KAYITLARI (Faturalar) ──
    borclar = []
    for _ in range(15):
        dk = random.choice(dis_kullanicilar)
        tutar = round(random.uniform(5000, 150000), 2)
        vade = bugun + timedelta(days=random.randint(-15, 45))
        
        borc = Borc(
            ilgili_tip='firma',
            ilgili_id=dk.firma_id,
            borc_turu='diger',
            aciklama=f"{vade.strftime('%B %Y')} Dönemi Faturası",
            donem=vade.strftime('%Y-%m'),
            tutar=tutar,
            odenen_tutar=0,
            son_odeme_tarihi=vade.date(),
            durum='odenmedi' if vade > bugun else 'gecikti' if random.random() > 0.5 else 'kismi_odendi'
        )
        db.session.add(borc)
        borclar.append(borc)

    db.session.flush()

    # ── TAHSİLAT KAYITLARI (Ödemeler) ──
    for b in borclar:
        if b.durum == 'odenmedi':
            continue
            
        odenen = b.tutar if b.durum != 'kismi_odendi' else float(b.tutar) * random.uniform(0.3, 0.7)
        b.odenen_tutar = odenen
        b.durum_guncelle()

        tahsilat = Tahsilat(
            borc_id=b.id,
            tutar=odenen,
            odeme_turu=random.choice(['havale', 'kredi_karti', 'nakit']),
            makbuz_no=f"TRX-{random.randint(100000, 999999)}",
            islem_tarihi=bugun - timedelta(days=random.randint(1, 20))
        )
        db.session.add(tahsilat)

    db.session.flush()
    print('  OK\n')
