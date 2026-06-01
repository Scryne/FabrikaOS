"""
FDYS — İK Servisi
Faz 1 — İnsan Kaynakları İş Mantığı

İzin bakiye hesaplama, kıdem hesaplama, fazla mesai özeti,
sertifika hatırlatma kontrol ve 360° personel raporu servisleri.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import func, extract

from app.extensions import db

logger = logging.getLogger(__name__)


def izin_bakiye_hesapla(calisan_id, yil=None):
    """
    Çalışanın yıllık izin bakiyesini hesaplar.

    Türk İş Kanunu'na göre yıllık izin hakları:
        - 1-5 yıl: 14 gün
        - 5-15 yıl: 20 gün
        - 15+ yıl: 26 gün

    Args:
        calisan_id: Çalışan ID
        yil: Hesaplanacak yıl (varsayılan: mevcut yıl)

    Returns:
        dict: {'yillik': {'hak': int, 'kullanilan': int, 'kalan': int},
               'mazeret': {'hak': int, 'kullanilan': int, 'kalan': int},
               'saglik': {'hak': int, 'kullanilan': int, 'kalan': int},
               'toplam_kullanilan': int}
    """
    from app.models.personel import Calisan, IzinTalebi

    if yil is None:
        yil = date.today().year

    calisan = db.session.get(Calisan, calisan_id)
    if not calisan:
        return None

    # Kıdem yılına göre yıllık izin hakkı
    kidem_yili = kidem_hesapla(calisan_id)
    if kidem_yili < 1:
        yillik_hak = 0  # 1 yıldan az çalışan henüz izin hakkı kazanmamış
    elif kidem_yili <= 5:
        yillik_hak = 14
    elif kidem_yili <= 15:
        yillik_hak = 20
    else:
        yillik_hak = 26

    # Mazeret ve sağlık izin hakları (şirket politikasına göre)
    mazeret_hak = 5
    saglik_hak = 10  # Sağlık raporu süresi dahil değil

    # Kullanılan izinleri hesapla
    izin_sorgusu = IzinTalebi.query.filter(
        IzinTalebi.calisan_id == calisan_id,
        IzinTalebi.durum == 'onaylandi',
        extract('year', IzinTalebi.baslangic_tarihi) == yil
    )

    kullanilan = {}
    for tur in ['yillik', 'mazeret', 'saglik', 'ucretsiz']:
        izinler = izin_sorgusu.filter(IzinTalebi.tur == tur).all()
        toplam_gun = 0
        for izin in izinler:
            gun_sayisi = (izin.bitis_tarihi - izin.baslangic_tarihi).days + 1
            toplam_gun += gun_sayisi
        kullanilan[tur] = toplam_gun

    return {
        'yillik': {
            'hak': yillik_hak,
            'kullanilan': kullanilan.get('yillik', 0),
            'kalan': max(0, yillik_hak - kullanilan.get('yillik', 0)),
        },
        'mazeret': {
            'hak': mazeret_hak,
            'kullanilan': kullanilan.get('mazeret', 0),
            'kalan': max(0, mazeret_hak - kullanilan.get('mazeret', 0)),
        },
        'saglik': {
            'hak': saglik_hak,
            'kullanilan': kullanilan.get('saglik', 0),
            'kalan': max(0, saglik_hak - kullanilan.get('saglik', 0)),
        },
        'ucretsiz': {
            'hak': None,  # Sınırsız (onaya bağlı)
            'kullanilan': kullanilan.get('ucretsiz', 0),
            'kalan': None,
        },
        'toplam_kullanilan': sum(kullanilan.values()),
    }


def kidem_hesapla(calisan_id):
    """
    Çalışanın kıdem yılını hesaplar.

    Args:
        calisan_id: Çalışan ID

    Returns:
        int: Kıdem yılı (tam yıl)
    """
    from app.models.personel import Calisan

    calisan = db.session.get(Calisan, calisan_id)
    if not calisan or not calisan.ise_baslama:
        return 0

    bugun = date.today()
    # İşten ayrılmışsa ayrılma tarihini kullan
    referans_tarih = calisan.isten_ayrilma if calisan.isten_ayrilma else bugun
    delta = referans_tarih - calisan.ise_baslama
    return delta.days // 365


def fazla_mesai_ozeti(calisan_id, ay=None, yil=None):
    """
    Çalışanın aylık fazla mesai özetini hesaplar.

    Args:
        calisan_id: Çalışan ID
        ay: Ay (1-12, varsayılan: mevcut ay)
        yil: Yıl (varsayılan: mevcut yıl)

    Returns:
        dict: {'toplam_saat': float, 'onaylanan_saat': float,
               'bekleyen_saat': float, 'hafta_ici': float,
               'hafta_sonu': float, 'resmi_tatil': float,
               'kayitlar': list}
    """
    from app.models.ik import FazlaMesai

    if ay is None:
        ay = date.today().month
    if yil is None:
        yil = date.today().year

    mesailer = FazlaMesai.query.filter(
        FazlaMesai.calisan_id == calisan_id,
        FazlaMesai.aktif == True,
        extract('month', FazlaMesai.tarih) == ay,
        extract('year', FazlaMesai.tarih) == yil,
    ).all()

    toplam = Decimal('0')
    onaylanan = Decimal('0')
    bekleyen = Decimal('0')
    hafta_ici = Decimal('0')
    hafta_sonu = Decimal('0')
    resmi_tatil = Decimal('0')

    for m in mesailer:
        saat = m.toplam_saat or Decimal('0')
        toplam += saat
        if m.onay_durumu == 'onaylandi':
            onaylanan += saat
        elif m.onay_durumu == 'bekliyor':
            bekleyen += saat

        if m.mesai_turu == 'hafta_ici':
            hafta_ici += saat
        elif m.mesai_turu == 'hafta_sonu':
            hafta_sonu += saat
        elif m.mesai_turu == 'resmi_tatil':
            resmi_tatil += saat

    return {
        'toplam_saat': float(toplam),
        'onaylanan_saat': float(onaylanan),
        'bekleyen_saat': float(bekleyen),
        'hafta_ici': float(hafta_ici),
        'hafta_sonu': float(hafta_sonu),
        'resmi_tatil': float(resmi_tatil),
        'kayitlar': mesailer,
    }


def sertifika_hatirlatma_kontrol():
    """
    Süresi dolacak sertifikaları kontrol eder.
    Hatırlatma gün sayısı içindeki sertifikaları döner.

    Returns:
        list[dict]: [{'sertifika': SertifikaTakip, 'kalan_gun': int, 'calisan': Calisan}]
    """
    from app.models.ik import SertifikaTakip

    bugun = date.today()
    yaklaşan = []

    sertifikalar = SertifikaTakip.query.filter(
        SertifikaTakip.aktif == True,
        SertifikaTakip.durum.in_(['gecerli', 'suresi_doldu']),
        SertifikaTakip.gecerlilik_bitis.isnot(None),
    ).all()

    for s in sertifikalar:
        kalan_gun = (s.gecerlilik_bitis - bugun).days
        hatirlatma = s.hatirlatma_gun or 30

        if kalan_gun <= hatirlatma:
            yaklaşan.append({
                'sertifika': s,
                'kalan_gun': kalan_gun,
                'calisan': s.calisan,
            })

            # Süresi dolduysa durumu güncelle
            if kalan_gun < 0 and s.durum == 'gecerli':
                s.durum = 'suresi_doldu'

    # Durumları değişenleri kaydet
    try:
        db.session.commit()
    except Exception as e:
        logger.error(f"Sertifika durum güncelleme hatası: {e}")
        db.session.rollback()

    # Kalan güne göre sırala (en yakın önce)
    yaklaşan.sort(key=lambda x: x['kalan_gun'])
    return yaklaşan


def personel_360_rapor(calisan_id):
    """
    Tek sayfada tüm çalışan verisini toplayan 360° rapor servisi.

    Args:
        calisan_id: Çalışan ID

    Returns:
        dict: Tüm İK verilerini içeren kapsamlı rapor sözlüğü
    """
    from app.models.personel import Calisan, IzinTalebi, VardiyaPlani
    from app.models.ik import (
        SavunmaTutanak, FazlaMesai, SertifikaTakip,
        MaasSkalasi, ZimmetKaydi, GirisCikisEvrak
    )
    from app.models.isg import IsKazasi, IsgEgitimi, SaglikMuayenesi

    calisan = db.session.get(Calisan, calisan_id)
    if not calisan:
        return None

    bugun = date.today()
    yil = bugun.year

    # İzin bakiyesi
    izin_bakiye = izin_bakiye_hesapla(calisan_id, yil)

    # Kıdem
    kidem = kidem_hesapla(calisan_id)

    # Savunma/Tutanaklar
    savunmalar = SavunmaTutanak.query.filter_by(
        calisan_id=calisan_id, aktif=True
    ).order_by(SavunmaTutanak.olusturma_tarihi.desc()).all()

    # Fazla mesai (mevcut ay)
    mesai_ozeti = fazla_mesai_ozeti(calisan_id, bugun.month, yil)

    # Sertifikalar
    sertifikalar = SertifikaTakip.query.filter_by(
        calisan_id=calisan_id, aktif=True
    ).order_by(SertifikaTakip.gecerlilik_bitis.asc()).all()

    # Maaş geçmişi
    maas_gecmisi = MaasSkalasi.query.filter_by(
        calisan_id=calisan_id, aktif=True
    ).order_by(MaasSkalasi.donem_baslangic.desc()).all()

    # Güncel maaş
    guncel_maas = MaasSkalasi.query.filter_by(
        calisan_id=calisan_id, aktif=True, donem_bitis=None
    ).first()

    # Zimmet kayıtları
    zimmetler = ZimmetKaydi.query.filter_by(
        calisan_id=calisan_id, aktif=True
    ).order_by(ZimmetKaydi.teslim_tarihi.desc()).all()

    aktif_zimmetler = [z for z in zimmetler if z.iade_edilmedi_mi]

    # Giriş/çıkış evrakları
    giris_evraklar = GirisCikisEvrak.query.filter_by(
        calisan_id=calisan_id, aktif=True, evrak_turu='ise_giris'
    ).all()
    cikis_evraklar = GirisCikisEvrak.query.filter_by(
        calisan_id=calisan_id, aktif=True, evrak_turu='isten_cikis'
    ).all()

    # Evrak tamamlanma yüzdesi
    def evrak_tamamlanma(evraklar):
        if not evraklar:
            return 0
        tamamlanan = sum(1 for e in evraklar if e.durum == 'tamamlandi')
        return round(tamamlanan / len(evraklar) * 100)

    # Son izinler
    son_izinler = IzinTalebi.query.filter_by(
        calisan_id=calisan_id
    ).order_by(IzinTalebi.baslangic_tarihi.desc()).limit(10).all()

    # İSG bilgileri
    isg_egitimleri = IsgEgitimi.query.filter_by(
        calisan_id=calisan_id, aktif=True
    ).order_by(IsgEgitimi.egitim_tarihi.desc()).all()

    kazalar = IsKazasi.query.filter_by(
        calisan_id=calisan_id, aktif=True
    ).order_by(IsKazasi.tarih.desc()).all()

    muayeneler = SaglikMuayenesi.query.filter_by(
        calisan_id=calisan_id, aktif=True
    ).order_by(SaglikMuayenesi.muayene_tarihi.desc()).all()

    return {
        'calisan': calisan,
        'kidem_yili': kidem,
        'izin_bakiye': izin_bakiye,
        'savunmalar': savunmalar,
        'savunma_sayisi': len(savunmalar),
        'mesai_ozeti': mesai_ozeti,
        'sertifikalar': sertifikalar,
        'suresi_dolan_sertifika': sum(1 for s in sertifikalar if s.suresi_doluyor_mu),
        'maas_gecmisi': maas_gecmisi,
        'guncel_maas': guncel_maas,
        'zimmetler': zimmetler,
        'aktif_zimmetler': aktif_zimmetler,
        'giris_evraklar': giris_evraklar,
        'cikis_evraklar': cikis_evraklar,
        'giris_tamamlanma': evrak_tamamlanma(giris_evraklar),
        'cikis_tamamlanma': evrak_tamamlanma(cikis_evraklar),
        'son_izinler': son_izinler,
        'isg_egitimleri': isg_egitimleri,
        'kazalar': kazalar,
        'muayeneler': muayeneler,
    }
