"""
FDYS — DYS (Doküman Yönetim Sistemi) Servisi
Faz 6

Doküman yükleme, versiyon kontrolü, OCR entegrasyonu,
tam metin arama ve istatistik servisleri.
"""

import os
import uuid
import logging
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
from sqlalchemy import or_, func

from app.extensions import db
from app.models.dys import Dokuman

logger = logging.getLogger(__name__)


# İzin verilen dosya uzantıları
DYS_IZIN_VERILEN_UZANTILAR = {
    'jpg', 'jpeg', 'png', 'gif', 'webp',
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv',
    'txt', 'md', 'ppt', 'pptx', 'zip', 'rar', '7z'
}


def uzanti_gecerli_mi(dosya_adi):
    """Dosya uzantısının DYS'ye yüklenebilir olup olmadığını kontrol eder."""
    return '.' in dosya_adi and dosya_adi.rsplit('.', 1)[1].lower() in DYS_IZIN_VERILEN_UZANTILAR


def guvenli_dosya_adi(dosya_adi):
    """UUID prefix ile benzersiz dosya adı oluşturur."""
    return f"{uuid.uuid4().hex[:12]}_{secure_filename(dosya_adi)}"


def dokuman_yukle(dosya, baslik, kategori, kullanici, **kwargs):
    """
    Yeni doküman yükler ve veritabanına kaydeder.

    Args:
        dosya: FileStorage nesnesi (werkzeug)
        baslik: Doküman başlığı
        kategori: Doküman kategorisi
        kullanici: Yükleyen kullanıcı nesnesi
        **kwargs: Ek alanlar (alt_kategori, etiketler, departman, erisim_seviyesi, aciklama, onay_gonder)

    Returns:
        tuple: (Dokuman nesnesi, hata_mesaji)
    """
    from flask import current_app

    if not dosya or dosya.filename == '':
        return None, 'Dosya seçilmedi.'

    if not uzanti_gecerli_mi(dosya.filename):
        return None, 'Desteklenmeyen dosya formatı.'

    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    if not upload_folder:
        return None, 'Yükleme klasörü yapılandırılmamış.'

    # DYS alt klasörü
    hedef_klasor = os.path.join(upload_folder, 'dys')
    os.makedirs(hedef_klasor, exist_ok=True)

    # Dosyayı kaydet
    guvenli_ad = guvenli_dosya_adi(dosya.filename)
    dosya_yolu = os.path.join(hedef_klasor, guvenli_ad)

    try:
        dosya.save(dosya_yolu)
        dosya_boyutu = os.path.getsize(dosya_yolu)
    except Exception as e:
        logger.error(f"DYS dosya kaydetme hatası: {e}")
        return None, 'Dosya kaydedilirken bir hata oluştu.'

    # Etiketleri ayrıştır
    etiketler_metin = kwargs.get('etiketler_metin', '')
    etiketler = [
        e.strip() for e in etiketler_metin.split(',') if e.strip()
    ] if etiketler_metin else []

    # Onay durumunu belirle
    onay_gonder = kwargs.get('onay_gonder', False)
    onay_durumu = 'onay_bekliyor' if onay_gonder else 'taslak'

    # OCR işlemini dene (PDF ve resim dosyaları için)
    ocr_metin = None
    uzanti = dosya.filename.rsplit('.', 1)[-1].lower() if '.' in dosya.filename else ''
    if uzanti in ('pdf', 'jpg', 'jpeg', 'png', 'gif', 'webp'):
        ocr_metin = ocr_tarama_yap(dosya_yolu, uzanti)

    dokuman = Dokuman(
        baslik=baslik,
        kategori=kategori,
        alt_kategori=kwargs.get('alt_kategori', ''),
        etiketler=etiketler,
        dosya_adi=f"dys/{guvenli_ad}",
        orijinal_adi=dosya.filename,
        mime_type=dosya.content_type,
        dosya_boyutu=dosya_boyutu,
        versiyon=1,
        sahip_id=kullanici.id,
        departman=kwargs.get('departman', ''),
        erisim_seviyesi=kwargs.get('erisim_seviyesi', 'herkese_acik'),
        ocr_metin=ocr_metin,
        onay_durumu=onay_durumu,
        aciklama=kwargs.get('aciklama', ''),
    )

    db.session.add(dokuman)
    db.session.commit()

    logger.info(f"DYS: Doküman yüklendi — {baslik} (v1) by {kullanici.ad_soyad}")
    return dokuman, None


def dokuman_yeni_versiyon(mevcut_dokuman_id, dosya, kullanici):
    """
    Mevcut dokümanın yeni versiyonunu yükler.

    Args:
        mevcut_dokuman_id: Mevcut dokümanın ID'si
        dosya: FileStorage nesnesi
        kullanici: Yükleyen kullanıcı

    Returns:
        tuple: (Yeni Dokuman nesnesi, hata_mesaji)
    """
    from flask import current_app

    mevcut = Dokuman.query.get(mevcut_dokuman_id)
    if not mevcut:
        return None, 'Mevcut doküman bulunamadı.'

    if not dosya or dosya.filename == '':
        return None, 'Dosya seçilmedi.'

    if not uzanti_gecerli_mi(dosya.filename):
        return None, 'Desteklenmeyen dosya formatı.'

    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    hedef_klasor = os.path.join(upload_folder, 'dys')
    os.makedirs(hedef_klasor, exist_ok=True)

    guvenli_ad = guvenli_dosya_adi(dosya.filename)
    dosya_yolu = os.path.join(hedef_klasor, guvenli_ad)

    try:
        dosya.save(dosya_yolu)
        dosya_boyutu = os.path.getsize(dosya_yolu)
    except Exception as e:
        logger.error(f"DYS versiyon yükleme hatası: {e}")
        return None, 'Dosya kaydedilirken bir hata oluştu.'

    # OCR
    ocr_metin = None
    uzanti = dosya.filename.rsplit('.', 1)[-1].lower() if '.' in dosya.filename else ''
    if uzanti in ('pdf', 'jpg', 'jpeg', 'png', 'gif', 'webp'):
        ocr_metin = ocr_tarama_yap(dosya_yolu, uzanti)

    yeni_versiyon = Dokuman(
        baslik=mevcut.baslik,
        kategori=mevcut.kategori,
        alt_kategori=mevcut.alt_kategori,
        etiketler=mevcut.etiketler,
        dosya_adi=f"dys/{guvenli_ad}",
        orijinal_adi=dosya.filename,
        mime_type=dosya.content_type,
        dosya_boyutu=dosya_boyutu,
        versiyon=mevcut.versiyon + 1,
        onceki_versiyon_id=mevcut.id,
        sahip_id=kullanici.id,
        departman=mevcut.departman,
        erisim_seviyesi=mevcut.erisim_seviyesi,
        ocr_metin=ocr_metin,
        onay_durumu='taslak',
        aciklama=mevcut.aciklama,
    )

    db.session.add(yeni_versiyon)
    db.session.commit()

    logger.info(f"DYS: Yeni versiyon — {mevcut.baslik} (v{yeni_versiyon.versiyon})")
    return yeni_versiyon, None


def dokuman_ara(arama_metni='', kategori='', departman='', onay_durumu='',
                kullanici=None, page=1, per_page=15):
    """
    Doküman tam metin araması.

    Args:
        arama_metni: Aranacak metin (başlık, etiket, OCR içerik)
        kategori: Kategori filtresi
        departman: Departman filtresi
        onay_durumu: Onay durumu filtresi
        kullanici: Erişim kontrolü için kullanıcı
        page: Sayfa numarası
        per_page: Sayfa başına kayıt

    Returns:
        Paginated sorgu sonucu
    """
    query = Dokuman.query.filter_by(aktif=True)

    # Metin araması
    if arama_metni:
        arama_pattern = f'%{arama_metni}%'
        query = query.filter(
            or_(
                Dokuman.baslik.ilike(arama_pattern),
                Dokuman.aciklama.ilike(arama_pattern),
                Dokuman.ocr_metin.ilike(arama_pattern),
                Dokuman.orijinal_adi.ilike(arama_pattern),
                Dokuman.alt_kategori.ilike(arama_pattern),
            )
        )

    # Filtreler
    if kategori:
        query = query.filter(Dokuman.kategori == kategori)
    if departman:
        query = query.filter(Dokuman.departman == departman)
    if onay_durumu:
        query = query.filter(Dokuman.onay_durumu == onay_durumu)

    # Sıralama
    query = query.order_by(Dokuman.olusturma_tarihi.desc())

    return query.paginate(page=page, per_page=per_page, error_out=False)


def dokuman_istatistikler():
    """
    DYS genel istatistiklerini döner.

    Returns:
        dict: İstatistik verileri
    """
    toplam = Dokuman.query.filter_by(aktif=True).count()

    # Kategori dağılımı
    kategori_dagilimi = db.session.query(
        Dokuman.kategori, func.count(Dokuman.id)
    ).filter(
        Dokuman.aktif == True
    ).group_by(Dokuman.kategori).all()

    # Onay durumu dağılımı
    onay_dagilimi = db.session.query(
        Dokuman.onay_durumu, func.count(Dokuman.id)
    ).filter(
        Dokuman.aktif == True
    ).group_by(Dokuman.onay_durumu).all()

    # Onay bekleyen sayısı
    onay_bekleyen = Dokuman.query.filter_by(
        aktif=True, onay_durumu='onay_bekliyor'
    ).count()

    # Toplam indirme
    toplam_indirme = db.session.query(
        func.sum(Dokuman.indirme_sayisi)
    ).filter(Dokuman.aktif == True).scalar() or 0

    # Toplam boyut
    toplam_boyut = db.session.query(
        func.sum(Dokuman.dosya_boyutu)
    ).filter(Dokuman.aktif == True).scalar() or 0

    # Son yüklenenler
    son_yuklemeler = Dokuman.query.filter_by(aktif=True).order_by(
        Dokuman.olusturma_tarihi.desc()
    ).limit(5).all()

    # En çok indirilenler
    en_cok_indirilen = Dokuman.query.filter_by(aktif=True).order_by(
        Dokuman.indirme_sayisi.desc()
    ).limit(5).all()

    return {
        'toplam': toplam,
        'kategori_dagilimi': [list(r) for r in kategori_dagilimi],
        'onay_dagilimi': [list(r) for r in onay_dagilimi],
        'onay_bekleyen': onay_bekleyen,
        'toplam_indirme': int(toplam_indirme),
        'toplam_boyut': int(toplam_boyut),
        'toplam_boyut_formatli': _boyut_formatla(int(toplam_boyut)),
        'son_yuklemeler': son_yuklemeler,
        'en_cok_indirilen': en_cok_indirilen,
    }


def ocr_tarama_yap(dosya_yolu, uzanti):
    """
    Dosya üzerinde OCR taraması yapar.
    pytesseract yoksa sessizce None döner.

    Args:
        dosya_yolu: Dosyanın fiziksel yolu
        uzanti: Dosya uzantısı

    Returns:
        str veya None: OCR metin çıktısı
    """
    try:
        from app.services.ocr_servisi import extract_text_from_image, clean_ocr_text
        ham_metin = extract_text_from_image(dosya_yolu)
        return clean_ocr_text(ham_metin) if ham_metin else None
    except ImportError:
        logger.debug("OCR servisi mevcut değil, OCR atlanıyor.")
        return None
    except Exception as e:
        logger.warning(f"OCR tarama hatası: {e}")
        return None


def _boyut_formatla(boyut_byte):
    """Byte cinsinden boyutu okunabilir formata dönüştürür."""
    if not boyut_byte:
        return '0 B'
    if boyut_byte < 1024:
        return f'{boyut_byte} B'
    elif boyut_byte < 1024 * 1024:
        return f'{boyut_byte / 1024:.1f} KB'
    elif boyut_byte < 1024 * 1024 * 1024:
        return f'{boyut_byte / (1024 * 1024):.1f} MB'
    else:
        return f'{boyut_byte / (1024 * 1024 * 1024):.2f} GB'
