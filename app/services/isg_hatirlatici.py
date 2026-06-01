"""
FDYS — İSG Hatırlatıcı Servisi
Faz 5 — İSG Genişletme + İK Entegrasyonu

Eğitim süresi, muayene tarihi, risk gözden geçirme ve
İSG doküman geçerlilik hatırlatmalarını yönetir.

Celery task olarak çalıştırılabilir veya manuel tetiklenebilir.
"""

import logging
from datetime import date, timedelta
from app.extensions import db

logger = logging.getLogger(__name__)


def muayene_hatirlatma_kontrol():
    """
    Yaklaşan ve gecikmiş sağlık muayenelerini kontrol eder.

    Returns:
        dict: {
            'yaklasan': list[dict]  — Hatırlatma aralığındaki muayeneler,
            'geciken': list[dict]   — Tarihi geçmiş muayeneler,
            'toplam_uyari': int
        }
    """
    from app.models.isg import SaglikMuayenesi

    bugun = date.today()
    yaklasan = []
    geciken = []

    muayeneler = SaglikMuayenesi.query.filter(
        SaglikMuayenesi.aktif == True,
        SaglikMuayenesi.sonraki_muayene_tarihi.isnot(None),
    ).all()

    for m in muayeneler:
        kalan_gun = (m.sonraki_muayene_tarihi - bugun).days
        hatirlatma = m.hatirlatma_gun or 30

        if kalan_gun < 0:
            # Muayene gecikmiş
            geciken.append({
                'muayene': m,
                'calisan': m.calisan,
                'kalan_gun': kalan_gun,
                'gecikme_gun': abs(kalan_gun),
            })
        elif kalan_gun <= hatirlatma:
            # Muayene yaklaşıyor
            yaklasan.append({
                'muayene': m,
                'calisan': m.calisan,
                'kalan_gun': kalan_gun,
            })

    # Sıralama: en acil önce
    yaklasan.sort(key=lambda x: x['kalan_gun'])
    geciken.sort(key=lambda x: x['kalan_gun'])

    return {
        'yaklasan': yaklasan,
        'geciken': geciken,
        'toplam_uyari': len(yaklasan) + len(geciken),
    }


def egitim_hatirlatma_kontrol():
    """
    Süresi dolmak üzere olan ve dolmuş İSG eğitimlerini kontrol eder.

    Returns:
        dict: {
            'yaklasan': list[dict]  — 30 gün içinde süresi dolacak eğitimler,
            'geciken': list[dict]   — Süresi dolmuş eğitimler,
            'toplam_uyari': int
        }
    """
    from app.models.isg import IsgEgitimi

    bugun = date.today()
    yaklasan = []
    geciken = []

    egitimler = IsgEgitimi.query.filter(
        IsgEgitimi.aktif == True,
        IsgEgitimi.durum == 'gecerli',
        IsgEgitimi.gecerlilik_bitis.isnot(None),
    ).all()

    for e in egitimler:
        kalan_gun = (e.gecerlilik_bitis - bugun).days

        if kalan_gun < 0:
            geciken.append({
                'egitim': e,
                'calisan': e.calisan,
                'kalan_gun': kalan_gun,
                'gecikme_gun': abs(kalan_gun),
            })
            # Durumu otomatik güncelle
            if e.durum == 'gecerli':
                e.durum = 'suresi_doldu'
        elif kalan_gun <= 30:
            yaklasan.append({
                'egitim': e,
                'calisan': e.calisan,
                'kalan_gun': kalan_gun,
            })

    try:
        db.session.commit()
    except Exception as ex:
        logger.error(f"Eğitim durum güncelleme hatası: {ex}")
        db.session.rollback()

    yaklasan.sort(key=lambda x: x['kalan_gun'])
    geciken.sort(key=lambda x: x['kalan_gun'])

    return {
        'yaklasan': yaklasan,
        'geciken': geciken,
        'toplam_uyari': len(yaklasan) + len(geciken),
    }


def risk_gozden_gecirme_kontrol():
    """
    Gözden geçirme tarihi gelmiş veya geçmiş riskleri kontrol eder.

    Returns:
        dict: {
            'yaklasan': list[dict]  — 30 gün içinde gözden geçirilmesi gereken riskler,
            'geciken': list[dict]   — Gözden geçirme tarihi geçmiş riskler,
            'toplam_uyari': int
        }
    """
    from app.models.isg import RiskDegerlendirme

    bugun = date.today()
    yaklasan = []
    geciken = []

    riskler = RiskDegerlendirme.query.filter(
        RiskDegerlendirme.aktif == True,
        RiskDegerlendirme.durum.in_(['acik', 'devam']),
        RiskDegerlendirme.gozden_gecirme_tarihi.isnot(None),
    ).all()

    for r in riskler:
        kalan_gun = (r.gozden_gecirme_tarihi - bugun).days

        if kalan_gun < 0:
            geciken.append({
                'risk': r,
                'kalan_gun': kalan_gun,
                'gecikme_gun': abs(kalan_gun),
            })
        elif kalan_gun <= 30:
            yaklasan.append({
                'risk': r,
                'kalan_gun': kalan_gun,
            })

    yaklasan.sort(key=lambda x: x['kalan_gun'])
    geciken.sort(key=lambda x: x['kalan_gun'])

    return {
        'yaklasan': yaklasan,
        'geciken': geciken,
        'toplam_uyari': len(yaklasan) + len(geciken),
    }


def dokuman_gecerlilik_kontrol():
    """
    Geçerlilik tarihi yaklaşan veya dolan İSG dokümanlarını kontrol eder.

    Returns:
        dict: {
            'yaklasan': list[dict]  — 30 gün içinde süresi dolacak dokümanlar,
            'geciken': list[dict]   — Süresi dolmuş dokümanlar,
            'toplam_uyari': int
        }
    """
    from app.models.isg import IsgDokumani

    bugun = date.today()
    yaklasan = []
    geciken = []

    dokumanlar = IsgDokumani.query.filter(
        IsgDokumani.aktif == True,
        IsgDokumani.gecerlilik_tarihi.isnot(None),
        IsgDokumani.onay_durumu == 'onaylandi',
    ).all()

    for d in dokumanlar:
        kalan_gun = (d.gecerlilik_tarihi - bugun).days

        if kalan_gun < 0:
            geciken.append({
                'dokuman': d,
                'kalan_gun': kalan_gun,
                'gecikme_gun': abs(kalan_gun),
            })
        elif kalan_gun <= 30:
            yaklasan.append({
                'dokuman': d,
                'kalan_gun': kalan_gun,
            })

    yaklasan.sort(key=lambda x: x['kalan_gun'])
    geciken.sort(key=lambda x: x['kalan_gun'])

    return {
        'yaklasan': yaklasan,
        'geciken': geciken,
        'toplam_uyari': len(yaklasan) + len(geciken),
    }


def tum_hatirlatmalar():
    """
    Tüm İSG hatırlatmalarını toplar — dashboard ve bildirim sistemi için.

    Returns:
        dict: Tüm kategorilerdeki hatırlatmaları içerir.
    """
    muayene = muayene_hatirlatma_kontrol()
    egitim = egitim_hatirlatma_kontrol()
    risk = risk_gozden_gecirme_kontrol()
    dokuman = dokuman_gecerlilik_kontrol()

    toplam_uyari = (
        muayene['toplam_uyari'] +
        egitim['toplam_uyari'] +
        risk['toplam_uyari'] +
        dokuman['toplam_uyari']
    )

    return {
        'muayene': muayene,
        'egitim': egitim,
        'risk': risk,
        'dokuman': dokuman,
        'toplam_uyari': toplam_uyari,
    }


def isg_bildirimleri_gonder():
    """
    Gecikmiş İSG öğeleri için otomatik bildirim oluşturur.
    Celery periyodik task olarak çalıştırılabilir.
    """
    from app.services.bildirim_motoru import bildirim_motoru
    from app.models.kullanici import Kullanici

    hatirlatmalar = tum_hatirlatmalar()

    # İSG uzmanlarını ve yöneticileri bul
    hedef_kullanicilar = Kullanici.query.filter(
        Kullanici.aktif == True,
        Kullanici.rol.in_(['yonetici', 'isg_uzmani'])
    ).all()

    if not hedef_kullanicilar:
        logger.warning("İSG bildirimi gönderilecek kullanıcı bulunamadı.")
        return

    # Gecikmiş muayeneler
    for m_data in hatirlatmalar['muayene']['geciken']:
        calisan_adi = m_data['calisan'].ad_soyad
        gecikme = m_data['gecikme_gun']
        for k in hedef_kullanicilar:
            try:
                bildirim_motoru.bildirim_olustur(
                    kullanici_id=k.id,
                    baslik="İSG: Gecikmiş Sağlık Muayenesi",
                    mesaj=f"{calisan_adi} çalışanının periyodik sağlık muayenesi {gecikme} gün gecikmiştir!",
                    seviye="uyari",
                    modul="isg",
                    url="/isg/saglik-muayeneleri"
                )
            except Exception as e:
                logger.error(f"Muayene bildirimi hatası: {e}")

    # Gecikmiş eğitimler
    for e_data in hatirlatmalar['egitim']['geciken']:
        calisan_adi = e_data['calisan'].ad_soyad
        egitim_adi = e_data['egitim'].egitim_adi
        for k in hedef_kullanicilar:
            try:
                bildirim_motoru.bildirim_olustur(
                    kullanici_id=k.id,
                    baslik="İSG: Süresi Dolmuş Eğitim",
                    mesaj=f"{calisan_adi} — '{egitim_adi}' eğitiminin süresi dolmuştur!",
                    seviye="uyari",
                    modul="isg",
                    url="/isg/egitimler"
                )
            except Exception as e:
                logger.error(f"Eğitim bildirimi hatası: {e}")

    # Gecikmiş risk gözden geçirmeleri
    for r_data in hatirlatmalar['risk']['geciken']:
        risk = r_data['risk']
        for k in hedef_kullanicilar:
            try:
                bildirim_motoru.bildirim_olustur(
                    kullanici_id=k.id,
                    baslik="İSG: Gecikmiş Risk Gözden Geçirme",
                    mesaj=f"'{risk.tehlike[:50]}' riski gözden geçirme tarihi geçmiştir ({risk.bolum}).",
                    seviye="uyari",
                    modul="isg",
                    url="/isg/hatirlatmalar"
                )
            except Exception as e:
                logger.error(f"Risk bildirimi hatası: {e}")

    toplam = hatirlatmalar['toplam_uyari']
    logger.info(f"İSG hatırlatma kontrol tamamlandı: {toplam} uyarı")
    return toplam
