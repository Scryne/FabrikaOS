"""
FDYS — Satın Alma Modülü Servisi
Faz 7

İş mantığı: talep oluşturma, onay, sipariş, teslim alma,
teklif karşılaştırma, istatistik ve raporlama.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import func, extract, and_

from app.extensions import db
from app.models.satin_alma import SatinAlmaTalebi, SatinAlmaSiparis, TeklifKarsilastirma
from app.models.stok import Tedarikci

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# TALEP SERVİSLERİ
# ══════════════════════════════════════════════════════════════════

def talep_olustur(talep_eden, **kwargs):
    """Yeni satın alma talebi oluşturur."""
    talep = SatinAlmaTalebi(
        talep_no=SatinAlmaTalebi.talep_no_olustur(),
        talep_eden_id=talep_eden.id,
        malzeme_hizmet=kwargs.get('malzeme_hizmet', 'malzeme'),
        kalem_adi=kwargs['kalem_adi'],
        miktar=kwargs.get('miktar', 1),
        birim=kwargs.get('birim', 'adet'),
        tahmini_birim_fiyat=kwargs.get('tahmini_birim_fiyat'),
        aciklama=kwargs.get('aciklama'),
        gerekce=kwargs.get('gerekce'),
        aciliyet=kwargs.get('aciliyet', 'normal'),
        departman=kwargs.get('departman'),
        istenen_teslim_tarihi=kwargs.get('istenen_teslim_tarihi'),
        tedarikci_id=kwargs.get('tedarikci_id') if kwargs.get('tedarikci_id') else None,
        durum=SatinAlmaTalebi.DURUM_BEKLIYOR,
    )
    db.session.add(talep)
    db.session.flush()
    logger.info(f'Satın alma talebi oluşturuldu: {talep.talep_no} by {talep_eden.ad_soyad}')
    return talep


def talep_onayla(talep_id, onaylayan):
    """Satın alma talebini onaylar."""
    talep = db.session.get(SatinAlmaTalebi, talep_id)
    if not talep:
        return None, 'Talep bulunamadı.'
    if talep.durum != SatinAlmaTalebi.DURUM_BEKLIYOR:
        return None, 'Bu talep onay bekliyor durumunda değil.'

    talep.durum = SatinAlmaTalebi.DURUM_ONAYLANDI
    talep.onaylayan_id = onaylayan.id
    talep.onay_tarihi = datetime.now(timezone.utc)
    db.session.flush()
    logger.info(f'Talep onaylandı: {talep.talep_no} by {onaylayan.ad_soyad}')
    return talep, None


def talep_reddet(talep_id, onaylayan, red_nedeni):
    """Satın alma talebini reddeder."""
    talep = db.session.get(SatinAlmaTalebi, talep_id)
    if not talep:
        return None, 'Talep bulunamadı.'
    if talep.durum != SatinAlmaTalebi.DURUM_BEKLIYOR:
        return None, 'Bu talep onay bekliyor durumunda değil.'

    talep.durum = SatinAlmaTalebi.DURUM_REDDEDILDI
    talep.onaylayan_id = onaylayan.id
    talep.onay_tarihi = datetime.now(timezone.utc)
    talep.red_nedeni = red_nedeni
    db.session.flush()
    logger.info(f'Talep reddedildi: {talep.talep_no} by {onaylayan.ad_soyad} — {red_nedeni[:50]}')
    return talep, None


def talep_iptal(talep_id):
    """Satın alma talebini iptal eder."""
    talep = db.session.get(SatinAlmaTalebi, talep_id)
    if not talep:
        return None, 'Talep bulunamadı.'
    if talep.durum in (SatinAlmaTalebi.DURUM_TESLIM_ALINDI, SatinAlmaTalebi.DURUM_IPTAL):
        return None, 'Bu talep iptal edilemez.'

    talep.durum = SatinAlmaTalebi.DURUM_IPTAL
    db.session.flush()
    logger.info(f'Talep iptal edildi: {talep.talep_no}')
    return talep, None


# ══════════════════════════════════════════════════════════════════
# SİPARİŞ SERVİSLERİ
# ══════════════════════════════════════════════════════════════════

def siparis_olustur(talep_id, olusturan, **kwargs):
    """Onaylanmış bir talepten sipariş oluşturur."""
    talep = db.session.get(SatinAlmaTalebi, talep_id)
    if not talep:
        return None, 'Talep bulunamadı.'
    if talep.durum != SatinAlmaTalebi.DURUM_ONAYLANDI:
        return None, 'Bu talep henüz onaylanmamış veya başka bir aşamada.'

    birim_fiyat = kwargs.get('birim_fiyat', Decimal('0'))
    miktar = kwargs.get('miktar', talep.miktar)
    kdv_orani = kwargs.get('kdv_orani', Decimal('20'))

    toplam_tutar = Decimal(str(birim_fiyat)) * Decimal(str(miktar))
    kdv_tutar = toplam_tutar * Decimal(str(kdv_orani)) / Decimal('100')
    genel_toplam = toplam_tutar + kdv_tutar

    siparis = SatinAlmaSiparis(
        siparis_no=SatinAlmaSiparis.siparis_no_olustur(),
        talep_id=talep.id,
        tedarikci_id=kwargs.get('tedarikci_id') if kwargs.get('tedarikci_id') else talep.tedarikci_id,
        birim_fiyat=birim_fiyat,
        miktar=miktar,
        toplam_tutar=toplam_tutar,
        kdv_orani=kdv_orani,
        genel_toplam=genel_toplam,
        beklenen_teslim=kwargs.get('beklenen_teslim'),
        fatura_no=kwargs.get('fatura_no'),
        notlar=kwargs.get('notlar'),
        olusturan_id=olusturan.id,
        durum=SatinAlmaSiparis.DURUM_SIPARIS_VERILDI,
    )
    db.session.add(siparis)

    # Talebin durumunu güncelle
    talep.durum = SatinAlmaTalebi.DURUM_SIPARIS_VERILDI
    db.session.flush()
    logger.info(f'Sipariş oluşturuldu: {siparis.siparis_no} talep: {talep.talep_no}')
    return siparis, None


def siparis_teslim_al(siparis_id, teslim_alan, gercek_teslim, fatura_no=None, notlar=None):
    """Siparişi teslim alır."""
    siparis = db.session.get(SatinAlmaSiparis, siparis_id)
    if not siparis:
        return None, 'Sipariş bulunamadı.'
    if siparis.durum in (SatinAlmaSiparis.DURUM_TESLIM_ALINDI, SatinAlmaSiparis.DURUM_IPTAL):
        return None, 'Bu sipariş zaten teslim alınmış veya iptal.'

    siparis.durum = SatinAlmaSiparis.DURUM_TESLIM_ALINDI
    siparis.gercek_teslim = gercek_teslim
    siparis.teslim_alan_id = teslim_alan.id
    if fatura_no:
        siparis.fatura_no = fatura_no
    if notlar:
        siparis.notlar = (siparis.notlar or '') + '\n' + notlar

    # Talebin durumunu da güncelle
    if siparis.talep:
        siparis.talep.durum = SatinAlmaTalebi.DURUM_TESLIM_ALINDI

    db.session.flush()
    logger.info(f'Sipariş teslim alındı: {siparis.siparis_no}')
    return siparis, None


def siparis_kargoda(siparis_id):
    """Siparişi kargo aşamasına geçirir."""
    siparis = db.session.get(SatinAlmaSiparis, siparis_id)
    if not siparis:
        return None, 'Sipariş bulunamadı.'
    if siparis.durum != SatinAlmaSiparis.DURUM_SIPARIS_VERILDI:
        return None, 'Bu sipariş yalnızca "Sipariş Verildi" durumundayken kargoya gönderilebilir.'

    siparis.durum = SatinAlmaSiparis.DURUM_KARGO
    db.session.flush()
    return siparis, None


# ══════════════════════════════════════════════════════════════════
# TEKLİF SERVİSLERİ
# ══════════════════════════════════════════════════════════════════

def teklif_ekle(talep_id, **kwargs):
    """Teklif karşılaştırma tablosuna yeni teklif ekler."""
    talep = db.session.get(SatinAlmaTalebi, talep_id)
    if not talep:
        return None, 'Talep bulunamadı.'

    teklif = TeklifKarsilastirma(
        talep_id=talep.id,
        tedarikci_id=kwargs.get('tedarikci_id') if kwargs.get('tedarikci_id') else None,
        birim_fiyat=kwargs.get('birim_fiyat'),
        toplam_fiyat=kwargs.get('toplam_fiyat'),
        teslimat_suresi=kwargs.get('teslimat_suresi'),
        garanti_suresi=kwargs.get('garanti_suresi'),
        notlar=kwargs.get('notlar'),
    )
    db.session.add(teklif)
    db.session.flush()
    logger.info(f'Teklif eklendi talep: {talep.talep_no}')
    return teklif, None


def teklif_sec(teklif_id):
    """Bir teklifi seçer ve diğerlerinin seçimini kaldırır."""
    teklif = db.session.get(TeklifKarsilastirma, teklif_id)
    if not teklif:
        return None, 'Teklif bulunamadı.'

    # Aynı talepteki diğer tekliflerin seçimini kaldır
    TeklifKarsilastirma.query.filter_by(
        talep_id=teklif.talep_id
    ).update({'secildi_mi': False})

    teklif.secildi_mi = True
    db.session.flush()
    logger.info(f'Teklif seçildi: ID={teklif.id} talep_id={teklif.talep_id}')
    return teklif, None


def teklif_sil(teklif_id):
    """Bir teklifi siler."""
    teklif = db.session.get(TeklifKarsilastirma, teklif_id)
    if not teklif:
        return None, 'Teklif bulunamadı.'

    db.session.delete(teklif)
    db.session.flush()
    return True, None


# ══════════════════════════════════════════════════════════════════
# İSTATİSTİK VE RAPORLAMA
# ══════════════════════════════════════════════════════════════════

def satin_alma_istatistikler():
    """Satın alma modülü dashboard istatistikleri."""
    toplam = SatinAlmaTalebi.query.filter_by(aktif=True).count()
    bekleyen = SatinAlmaTalebi.query.filter_by(aktif=True, durum='bekliyor').count()
    onaylanan = SatinAlmaTalebi.query.filter_by(aktif=True, durum='onaylandi').count()
    siparis_verilen = SatinAlmaTalebi.query.filter_by(aktif=True, durum='siparis_verildi').count()
    teslim_alinan = SatinAlmaTalebi.query.filter_by(aktif=True, durum='teslim_alindi').count()
    reddedilen = SatinAlmaTalebi.query.filter_by(aktif=True, durum='reddedildi').count()

    # Toplam sipariş tutarı
    toplam_tutar = db.session.query(
        func.coalesce(func.sum(SatinAlmaSiparis.genel_toplam), 0)
    ).filter(
        SatinAlmaSiparis.aktif == True,
        SatinAlmaSiparis.durum != 'iptal'
    ).scalar() or 0

    # Aktif sipariş sayısı
    aktif_siparis = SatinAlmaSiparis.query.filter(
        SatinAlmaSiparis.aktif == True,
        SatinAlmaSiparis.durum.in_(['siparis_verildi', 'kargo'])
    ).count()

    # Geciken sipariş sayısı
    geciken_siparis = SatinAlmaSiparis.query.filter(
        SatinAlmaSiparis.aktif == True,
        SatinAlmaSiparis.durum.in_(['siparis_verildi', 'kargo']),
        SatinAlmaSiparis.beklenen_teslim < datetime.now(timezone.utc).date()
    ).count()

    # Acil talep sayısı
    acil_talep = SatinAlmaTalebi.query.filter_by(
        aktif=True, durum='bekliyor', aciliyet='acil'
    ).count()

    return {
        'toplam': toplam,
        'bekleyen': bekleyen,
        'onaylanan': onaylanan,
        'siparis_verilen': siparis_verilen,
        'teslim_alinan': teslim_alinan,
        'reddedilen': reddedilen,
        'toplam_tutar': float(toplam_tutar),
        'aktif_siparis': aktif_siparis,
        'geciken_siparis': geciken_siparis,
        'acil_talep': acil_talep,
    }


def tedarikci_performans_ozeti():
    """Tedarikçi bazında sipariş ve gecikme istatistikleri."""
    tedarikciler = Tedarikci.query.filter_by(aktif=True).all()
    sonuc = []
    for t in tedarikciler:
        siparis_sayisi = SatinAlmaSiparis.query.filter_by(
            tedarikci_id=t.id, aktif=True
        ).count()
        if siparis_sayisi == 0:
            continue
        teslim_alinan = SatinAlmaSiparis.query.filter_by(
            tedarikci_id=t.id, aktif=True, durum='teslim_alindi'
        ).count()
        toplam = db.session.query(
            func.coalesce(func.sum(SatinAlmaSiparis.genel_toplam), 0)
        ).filter(
            SatinAlmaSiparis.tedarikci_id == t.id,
            SatinAlmaSiparis.aktif == True
        ).scalar() or 0

        sonuc.append({
            'tedarikci': t,
            'siparis_sayisi': siparis_sayisi,
            'teslim_alinan': teslim_alinan,
            'toplam_tutar': float(toplam),
        })

    return sorted(sonuc, key=lambda x: x['siparis_sayisi'], reverse=True)


def aylik_harcama_ozeti(yil=None):
    """Aylık satın alma harcama özeti."""
    if yil is None:
        yil = datetime.now().year

    sonuc = db.session.query(
        extract('month', SatinAlmaSiparis.siparis_tarihi).label('ay'),
        func.count(SatinAlmaSiparis.id).label('siparis_sayisi'),
        func.coalesce(func.sum(SatinAlmaSiparis.genel_toplam), 0).label('toplam_tutar')
    ).filter(
        SatinAlmaSiparis.aktif == True,
        SatinAlmaSiparis.durum != 'iptal',
        extract('year', SatinAlmaSiparis.siparis_tarihi) == yil
    ).group_by(
        extract('month', SatinAlmaSiparis.siparis_tarihi)
    ).order_by(
        extract('month', SatinAlmaSiparis.siparis_tarihi)
    ).all()

    ay_isimleri = {
        1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan',
        5: 'Mayıs', 6: 'Haziran', 7: 'Temmuz', 8: 'Ağustos',
        9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
    }

    return [{
        'ay': int(r.ay),
        'ay_adi': ay_isimleri.get(int(r.ay), ''),
        'siparis_sayisi': r.siparis_sayisi,
        'toplam_tutar': float(r.toplam_tutar),
    } for r in sonuc]
