"""
FabrikaOS — Duyurular Demo Verisi (v2)
Duyuru kayıtları ve okunma istatistikleri
"""
import random
from datetime import datetime, timedelta, timezone
from app.extensions import db
from app.models.duyuru import Duyuru, DuyuruOkunma
from app.models.kullanici import Kullanici


def seed():
    print('[27/22] Duyurular...')

    yoneticiler = Kullanici.query.filter_by(rol='yonetici').all()
    ik = Kullanici.query.filter_by(rol='ik_uzmani').first()
    isg = Kullanici.query.filter_by(rol='isg_uzmani').first()
    kullanicilar = Kullanici.query.filter_by(aktif=True).all()
    bugun = datetime.now(timezone.utc)

    olusturan_id = yoneticiler[0].id if yoneticiler else 1

    duyurular_data = [
        {'baslik': 'FabrikaOS Yeni Sürüm Yayında', 'icerik': 'Sistemimizin v2.1 sürümü devreye alınmıştır. Yeni arayüzü ve performans iyileştirmelerini deneyimleyebilirsiniz.', 'tur': 'bilgi', 'oncelik': 'normal', 'yayinlayan_id': olusturan_id, 'gun_once': 1},
        {'baslik': 'Haftalık Üretim Toplantısı', 'icerik': 'Cuma günü saat 15:00\'te konferans salonunda haftalık genel değerlendirme toplantısı yapılacaktır.', 'tur': 'toplanti', 'oncelik': 'onemli', 'yayinlayan_id': olusturan_id, 'gun_once': 3},
        {'baslik': 'Kalite Denetimi Başarısı', 'icerik': 'Geçtiğimiz hafta yapılan ISO 9001 ara denetimi sıfır majör uygunsuzlukla tamamlanmıştır. Tüm ekibe teşekkürler.', 'tur': 'bilgi', 'oncelik': 'normal', 'yayinlayan_id': olusturan_id, 'gun_once': 15},
        {'baslik': 'KKD Kullanım Zorunluluğu', 'icerik': 'Üretim alanında yan siperlikli gözlük takma zorunluluğuna harfiyen uyulması gerekmektedir. İhlal durumunda tutanak tutulacaktır.', 'tur': 'acil', 'oncelik': 'acil', 'yayinlayan_id': isg.id if isg else olusturan_id, 'gun_once': 5},
        {'baslik': 'Yıllık İzin Planlamaları', 'icerik': 'Yaz dönemi (Haziran-Ağustos) yıllık izin planlamalarının en geç Mayıs ayı sonuna kadar sisteme girilmesi rica olunur.', 'tur': 'bilgi', 'oncelik': 'normal', 'yayinlayan_id': ik.id if ik else olusturan_id, 'gun_once': 20},
        {'baslik': 'Servis Güzergahı Değişikliği', 'icerik': 'Yol çalışması nedeniyle Gebze 2. hat servis güzergahında geçici değişiklik yapılmıştır. Detaylar DYS üzerinden incelenebilir.', 'tur': 'bakim', 'oncelik': 'normal', 'yayinlayan_id': ik.id if ik else olusturan_id, 'gun_once': 8},
        {'baslik': 'Kan Bağışı Kampanyası', 'icerik': 'Kızılay mobil kan bağışı aracı Perşembe günü fabrika bahçemizde olacaktır.', 'tur': 'etkinlik', 'oncelik': 'normal', 'yayinlayan_id': ik.id if ik else olusturan_id, 'gun_once': 40},
    ]

    duyuru_objeleri = []
    for d in duyurular_data:
        dy = Duyuru(
            baslik=d['baslik'],
            icerik=d['icerik'],
            tur=d['tur'],
            oncelik=d['oncelik'],
            yayinlayan_id=d['yayinlayan_id'],
            olusturma_tarihi=bugun - timedelta(days=d['gun_once']),
            yayin_tarihi=bugun - timedelta(days=d['gun_once']),
            hedef_kitle='tumu'
        )
        db.session.add(dy)
        duyuru_objeleri.append(dy)

    db.session.flush()

    # Okunma istatistikleri
    for dy in duyuru_objeleri:
        okuyanlar = random.sample(kullanicilar, k=int(len(kullanicilar) * random.uniform(0.4, 0.9)))
        for k in okuyanlar:
            ok = DuyuruOkunma(
                duyuru_id=dy.id,
                kullanici_id=k.id,
                tarih=dy.olusturma_tarihi + timedelta(hours=random.randint(1, 48))
            )
            db.session.add(ok)

    db.session.flush()
    print('  OK\n')
