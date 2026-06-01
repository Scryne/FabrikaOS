"""
FDYS — Duyuru & İletişim Servisi
Faz 6

Duyuru oluşturma, hedef kitle filtreleme, okunma takibi
ve banner (sabitlenmiş duyuru) yönetim servisleri.
"""

import logging
from datetime import datetime, timezone
from sqlalchemy import or_, func, and_

from app.extensions import db
from app.models.duyuru import Duyuru, DuyuruOkunma

logger = logging.getLogger(__name__)


def duyuru_olustur(baslik, icerik, kullanici, **kwargs):
    """
    Yeni duyuru oluşturur.

    Args:
        baslik: Duyuru başlığı
        icerik: Duyuru içeriği (HTML)
        kullanici: Yayınlayan kullanıcı
        **kwargs: tur, oncelik, hedef_kitle, hedef_deger, bitis_tarihi, sabitle

    Returns:
        Duyuru nesnesi
    """
    duyuru = Duyuru(
        baslik=baslik,
        icerik=icerik,
        tur=kwargs.get('tur', 'bilgi'),
        oncelik=kwargs.get('oncelik', 'normal'),
        hedef_kitle=kwargs.get('hedef_kitle', 'tumu'),
        hedef_deger=kwargs.get('hedef_deger', ''),
        yayinlayan_id=kullanici.id,
        yayin_tarihi=datetime.now(timezone.utc),
        bitis_tarihi=kwargs.get('bitis_tarihi'),
        sabitle=kwargs.get('sabitle', False),
    )

    db.session.add(duyuru)
    db.session.commit()

    logger.info(f"Duyuru oluşturuldu: '{baslik}' (tür: {duyuru.tur}, hedef: {duyuru.hedef_kitle})")
    return duyuru


def duyurulari_getir(kullanici, sadece_aktif=True, page=1, per_page=15):
    """
    Kullanıcının görebileceği duyuruları getirir.

    Args:
        kullanici: Duyuruları görüntüleyen kullanıcı
        sadece_aktif: Sadece aktif duyuruları getir
        page: Sayfa numarası
        per_page: Sayfa başına kayıt

    Returns:
        Paginated sorgu sonucu
    """
    query = Duyuru.query.filter_by(aktif=True)

    if sadece_aktif:
        simdi = datetime.now(timezone.utc)
        query = query.filter(
            or_(
                Duyuru.bitis_tarihi.is_(None),
                Duyuru.bitis_tarihi > simdi
            )
        )

    # Hedef kitle filtreleme (yönetici tümünü görür)
    if not kullanici.yonetici_mi():
        query = query.filter(
            or_(
                Duyuru.hedef_kitle == 'tumu',
                and_(
                    Duyuru.hedef_kitle == 'departman',
                    Duyuru.hedef_deger == kullanici.departman
                ),
                and_(
                    Duyuru.hedef_kitle == 'rol',
                    Duyuru.hedef_deger == kullanici.rol
                ),
                and_(
                    Duyuru.hedef_kitle == 'kisi',
                    Duyuru.hedef_deger.contains(str(kullanici.id))
                ),
            )
        )

    query = query.order_by(
        Duyuru.sabitle.desc(),  # Sabitlenmiş olanlar üstte
        Duyuru.yayin_tarihi.desc()
    )

    return query.paginate(page=page, per_page=per_page, error_out=False)


def sabitlenmis_duyurular(kullanici):
    """
    Sabitlenmiş (banner) duyuruları getirir.

    Args:
        kullanici: Duyuruları görüntüleyen kullanıcı

    Returns:
        list: Sabitlenmiş Duyuru listesi
    """
    simdi = datetime.now(timezone.utc)

    query = Duyuru.query.filter_by(aktif=True, sabitle=True).filter(
        or_(
            Duyuru.bitis_tarihi.is_(None),
            Duyuru.bitis_tarihi > simdi
        )
    )

    # Hedef kitle filtreleme
    if not kullanici.yonetici_mi():
        query = query.filter(
            or_(
                Duyuru.hedef_kitle == 'tumu',
                and_(
                    Duyuru.hedef_kitle == 'departman',
                    Duyuru.hedef_deger == kullanici.departman
                ),
                and_(
                    Duyuru.hedef_kitle == 'rol',
                    Duyuru.hedef_deger == kullanici.rol
                ),
                and_(
                    Duyuru.hedef_kitle == 'kisi',
                    Duyuru.hedef_deger.contains(str(kullanici.id))
                ),
            )
        )

    return query.order_by(Duyuru.yayin_tarihi.desc()).all()


def duyuru_okunma_kaydet(duyuru_id, kullanici_id):
    """
    Duyuru okunma kaydı oluşturur.

    Args:
        duyuru_id: Okunan duyurunun ID'si
        kullanici_id: Okuyan kullanıcının ID'si

    Returns:
        bool: Yeni kayıt oluşturuldu mu (False = zaten okunmuş)
    """
    duyuru = Duyuru.query.get(duyuru_id)
    if not duyuru:
        return False

    return duyuru.okunma_kaydet(kullanici_id)


def duyuru_istatistikler():
    """
    Duyuru genel istatistiklerini döner.

    Returns:
        dict: İstatistik verileri
    """
    simdi = datetime.now(timezone.utc)

    toplam = Duyuru.query.filter_by(aktif=True).count()
    aktif = Duyuru.query.filter_by(aktif=True).filter(
        or_(
            Duyuru.bitis_tarihi.is_(None),
            Duyuru.bitis_tarihi > simdi
        )
    ).count()
    sabitlenmis = Duyuru.query.filter_by(aktif=True, sabitle=True).count()

    # Tür dağılımı
    tur_dagilimi = db.session.query(
        Duyuru.tur, func.count(Duyuru.id)
    ).filter(Duyuru.aktif == True).group_by(Duyuru.tur).all()

    # Toplam okunma
    toplam_okunma = db.session.query(
        func.sum(Duyuru.okunma_sayisi)
    ).filter(Duyuru.aktif == True).scalar() or 0

    return {
        'toplam': toplam,
        'aktif': aktif,
        'sabitlenmis': sabitlenmis,
        'tur_dagilimi': [list(r) for r in tur_dagilimi],
        'toplam_okunma': int(toplam_okunma),
    }


def okunma_detay(duyuru_id):
    """
    Belirli bir duyurunun okunma detaylarını döner.

    Args:
        duyuru_id: Duyuru ID'si

    Returns:
        list: Okunma kayıtları
    """
    return DuyuruOkunma.query.filter_by(
        duyuru_id=duyuru_id
    ).order_by(DuyuruOkunma.tarih.desc()).all()
