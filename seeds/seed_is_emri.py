"""
FabrikaOS — İş Emirleri ve Yorumlar Demo Verisi (v2)
"""
import random
from datetime import date, datetime, timedelta, timezone
from app.extensions import db
from app.models.is_emri import IsEmri, IsEmriYorum
from app.models.makine import ArizaKaydi, BakimKaydi
from app.models.kullanici import Kullanici


def seed():
    print('[19/22] İş Emirleri...')
    random.seed(888)

    teknisyenler = Kullanici.query.filter_by(rol='teknisyen').all()
    yoneticiler = Kullanici.query.filter_by(rol='yonetici').all()

    if not teknisyenler:
        print("  Uyarı: Teknisyen bulunamadı, iş emirleri atlanıyor.")
        return

    # Arıza ve bakımlara bağlı iş emirleri oluştur
    arizalar = ArizaKaydi.query.all()
    bakimlar = BakimKaydi.query.all()

    is_emirleri = []

    # Arıza iş emirleri
    for i, a in enumerate(arizalar):
        # Eğer çözüldüyse iş emri de kapalı olmalı
        durum = IsEmri.DURUM_TAMAMLANDI if a.durum == 'cozuldu' else IsEmri.DURUM_DEVAM if a.durum == 'arastiriliyor' else IsEmri.DURUM_ACIK
        baslik = f"Arıza Onarımı: {a.makine.kod if a.makine else 'Bilinmeyen'} - {a.ariza_turu}"

        atanan = a.atanan_teknisyen_id or random.choice(teknisyenler).id

        ie = IsEmri(
            is_emri_no=f"İE-A-{date.today().year}-{i+1000}",
            baslik=baslik,
            aciklama=a.aciklama,
            oncelik=a.oncelik,
            durum=durum,
            kaynak_modul='makine',
            kaynak_id=a.id,
            kategori=IsEmri.KATEGORI_ARIZA,
            olusturan_id=a.bildiren_id,
            atanan_id=atanan,
            baslama_zamani=a.baslangic_zamani if durum != IsEmri.DURUM_ACIK else None,
            tamamlanma_zamani=a.bitis_zamani if durum == IsEmri.DURUM_TAMAMLANDI else None,
            olusturma_tarihi=a.baslangic_zamani - timedelta(minutes=15)
        )
        is_emirleri.append(ie)
        db.session.add(ie)

    # Bakım iş emirleri
    for i, b in enumerate(bakimlar):
        durum = IsEmri.DURUM_TAMAMLANDI if b.tarih < date.today() else IsEmri.DURUM_ATANDI
        oncelik = IsEmri.ONCELIK_YUKSEK if b.bakim_turu == 'acil' else IsEmri.ONCELIK_NORMAL
        baslik = f"Bakım: {b.makine.kod if b.makine else 'Bilinmeyen'} - {b.bakim_turu.capitalize()}"

        atanan = b.teknisyen_id or random.choice(teknisyenler).id

        ie = IsEmri(
            is_emri_no=f"İE-B-{date.today().year}-{i+2000}",
            baslik=baslik,
            aciklama=f"{b.yapilan_islem}\n\nNotlar: {b.notlar or 'Yok'}",
            oncelik=oncelik,
            durum=durum,
            kaynak_modul='bakim',
            kaynak_id=b.id,
            kategori=IsEmri.KATEGORI_BAKIM,
            olusturan_id=yoneticiler[0].id if yoneticiler else 1,
            atanan_id=atanan,
            baslama_zamani=datetime.combine(b.tarih, datetime.min.time()).replace(tzinfo=timezone.utc) if durum == IsEmri.DURUM_TAMAMLANDI else None,
            tamamlanma_zamani=datetime.combine(b.tarih, datetime.min.time()).replace(tzinfo=timezone.utc) + timedelta(minutes=b.sure_dk) if durum == IsEmri.DURUM_TAMAMLANDI else None,
            olusturma_tarihi=datetime.combine(b.tarih, datetime.min.time()).replace(tzinfo=timezone.utc) - timedelta(days=5)
        )
        is_emirleri.append(ie)
        db.session.add(ie)

    db.session.flush()

    # İş emri yorumları
    for ie in is_emirleri:
        if ie.durum in [IsEmri.DURUM_DEVAM, IsEmri.DURUM_TAMAMLANDI]:
            # Ara yorum (bazılarına)
            if random.random() > 0.5:
                ieg2 = IsEmriYorum(
                    is_emri_id=ie.id,
                    kullanici_id=ie.atanan_id,
                    icerik="Malzeme depodan çekildi, işlem devam ediyor.",
                    olusturma_tarihi=ie.baslama_zamani + timedelta(minutes=30) if ie.baslama_zamani else ie.olusturma_tarihi + timedelta(hours=2)
                )
                db.session.add(ieg2)

        if ie.durum == IsEmri.DURUM_TAMAMLANDI:
            # Kapanış kaydı
            ieg3 = IsEmriYorum(
                is_emri_id=ie.id,
                kullanici_id=ie.atanan_id,
                icerik="İşlem tamamlandı, testler yapıldı, saha temiz bırakıldı.",
                olusturma_tarihi=ie.tamamlanma_zamani or ie.olusturma_tarihi + timedelta(hours=5)
            )
            db.session.add(ieg3)

    db.session.flush()
    print(f'  + {len(is_emirleri)} iş emri ve yorumları eklendi\n')
