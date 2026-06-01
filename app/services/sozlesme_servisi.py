"""
FDYS — Sözleşme Servisi
Faz 3 — Sözleşme, Kira Kontrat & Sigorta Poliçe İş Mantığı

Hatırlatma kontrolü, kira artışı hesaplama, standart metin doldurma,
sözleşme rapor ve istatistik servisleri.
"""

import logging
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from sqlalchemy import func, or_, and_

from app.extensions import db

logger = logging.getLogger(__name__)


# ==========================================================
# DASHBOARD & İSTATİSTİK
# ==========================================================

def sozlesme_dashboard_istatistik():
    """
    Sözleşme dashboard için KPI istatistikleri.

    Returns:
        dict: Dashboard verileri
    """
    from app.models.sozlesme import Sozlesme, KiraKontrat, SigortaPolice, StandartMetin

    bugun = date.today()

    # Toplam sayılar
    toplam_sozlesme = Sozlesme.query.filter_by(aktif=True).count()
    aktif_sozlesme = Sozlesme.query.filter_by(aktif=True, durum='aktif').count()

    # Kira kontratları
    toplam_kira = Sozlesme.query.filter_by(aktif=True, tur='kira', durum='aktif').count()

    # Sigorta poliçeleri
    toplam_police = SigortaPolice.query.filter_by(aktif=True).count()
    aktif_police = SigortaPolice.query.filter_by(aktif=True, durum='aktif').count()

    # Süresi yaklaşan sözleşmeler (30 gün içinde)
    yaklasan_tarih = bugun + timedelta(days=30)
    suresi_yaklasan = Sozlesme.query.filter(
        Sozlesme.aktif == True,
        Sozlesme.durum == 'aktif',
        Sozlesme.bitis_tarihi.isnot(None),
        Sozlesme.bitis_tarihi <= yaklasan_tarih,
        Sozlesme.bitis_tarihi >= bugun,
    ).count()

    # Süresi dolan poliçeler (30 gün içinde)
    police_yaklasan = SigortaPolice.query.filter(
        SigortaPolice.aktif == True,
        SigortaPolice.durum == 'aktif',
        SigortaPolice.police_bitis <= yaklasan_tarih,
        SigortaPolice.police_bitis >= bugun,
    ).count()

    # Süresi dolmuş sözleşmeler (hâlâ aktif olanlar)
    suresi_dolmus = Sozlesme.query.filter(
        Sozlesme.aktif == True,
        Sozlesme.durum == 'aktif',
        Sozlesme.bitis_tarihi.isnot(None),
        Sozlesme.bitis_tarihi < bugun,
    ).count()

    # Sözleşme türü dağılımı
    tur_dagilimi = db.session.query(
        Sozlesme.tur, func.count(Sozlesme.id)
    ).filter(Sozlesme.aktif == True).group_by(Sozlesme.tur).all()

    # Durum dağılımı
    durum_dagilimi = db.session.query(
        Sozlesme.durum, func.count(Sozlesme.id)
    ).filter(Sozlesme.aktif == True).group_by(Sozlesme.durum).all()

    # Aylık toplam tutar (aktif sözleşmeler)
    aylik_toplam = db.session.query(
        func.sum(Sozlesme.tutar)
    ).filter(
        Sozlesme.aktif == True,
        Sozlesme.durum == 'aktif',
        Sozlesme.odeme_periyodu == 'aylik'
    ).scalar() or 0

    # Son eklenen sözleşmeler
    son_sozlesmeler = Sozlesme.query.filter_by(aktif=True).order_by(
        Sozlesme.olusturma_tarihi.desc()
    ).limit(5).all()

    # Standart metin sayısı
    standart_metin_sayisi = StandartMetin.query.filter_by(aktif=True).count()

    return {
        'toplam_sozlesme': toplam_sozlesme,
        'aktif_sozlesme': aktif_sozlesme,
        'toplam_kira': toplam_kira,
        'toplam_police': toplam_police,
        'aktif_police': aktif_police,
        'suresi_yaklasan': suresi_yaklasan,
        'police_yaklasan': police_yaklasan,
        'suresi_dolmus': suresi_dolmus,
        'tur_dagilimi': [list(r) for r in tur_dagilimi],
        'durum_dagilimi': [list(r) for r in durum_dagilimi],
        'aylik_toplam': float(aylik_toplam),
        'son_sozlesmeler': son_sozlesmeler,
        'standart_metin_sayisi': standart_metin_sayisi,
    }


# ==========================================================
# HATIRLATMA SİSTEMİ
# ==========================================================

def hatirlatma_kontrol():
    """
    Süresi dolacak sözleşme ve poliçeleri kontrol eder.
    Celery task olarak periyodik çalıştırılabilir.

    Returns:
        dict: {'sozlesmeler': [...], 'policeler': [...]}
    """
    from app.models.sozlesme import Sozlesme, SigortaPolice

    bugun = date.today()

    # Süresi yaklaşan sözleşmeler
    yaklasan_sozlesmeler = Sozlesme.query.filter(
        Sozlesme.aktif == True,
        Sozlesme.durum == 'aktif',
        Sozlesme.bitis_tarihi.isnot(None),
        Sozlesme.bitis_tarihi >= bugun,
    ).all()

    hatirlatma_sozlesmeler = []
    for s in yaklasan_sozlesmeler:
        hatirlatma_gun = s.hatirlatma_gun or 30
        kalan = (s.bitis_tarihi - bugun).days
        if kalan <= hatirlatma_gun:
            hatirlatma_sozlesmeler.append({
                'sozlesme': s,
                'kalan_gun': kalan,
                'tip': 'sozlesme',
            })

    # Süresi yaklaşan poliçeler
    yaklasan_policeler = SigortaPolice.query.filter(
        SigortaPolice.aktif == True,
        SigortaPolice.durum == 'aktif',
        SigortaPolice.police_bitis >= bugun,
    ).all()

    hatirlatma_policeler = []
    for p in yaklasan_policeler:
        hatirlatma_gun = p.hatirlatma_gun or 30
        kalan = (p.police_bitis - bugun).days
        if kalan <= hatirlatma_gun:
            hatirlatma_policeler.append({
                'police': p,
                'kalan_gun': kalan,
                'tip': 'police',
            })

    return {
        'sozlesmeler': sorted(hatirlatma_sozlesmeler, key=lambda x: x['kalan_gun']),
        'policeler': sorted(hatirlatma_policeler, key=lambda x: x['kalan_gun']),
    }


def yaklasan_olaylar_takvim():
    """
    Takvim görünümü için tüm sözleşme bitiş tarihlerini döndürür.

    Returns:
        list: [{'title': '...', 'start': 'YYYY-MM-DD', 'color': '...', 'url': '...'}, ...]
    """
    from app.models.sozlesme import Sozlesme, SigortaPolice

    olaylar = []

    # Sözleşme bitiş tarihleri
    sozlesmeler = Sozlesme.query.filter(
        Sozlesme.aktif == True,
        Sozlesme.bitis_tarihi.isnot(None),
    ).all()

    for s in sozlesmeler:
        renk = '#10b981'  # yeşil (aktif)
        if s.suresi_doldu:
            renk = '#ef4444'  # kırmızı
        elif s.suresi_dolmak_uzere:
            renk = '#f59e0b'  # sarı

        olaylar.append({
            'id': f'soz-{s.id}',
            'title': f'{s.tur_adi}: {s.baslik[:40]}',
            'start': s.bitis_tarihi.isoformat(),
            'color': renk,
            'url': f'/sozlesme/{s.id}',
            'extendedProps': {
                'tip': 'sozlesme',
                'sozlesme_no': s.sozlesme_no,
                'taraf': s.taraf_bilgi,
                'durum': s.durum_adi,
            }
        })

    # Poliçe bitiş tarihleri
    policeler = SigortaPolice.query.filter(
        SigortaPolice.aktif == True,
    ).all()

    for p in policeler:
        renk = '#8b5cf6'  # mor (aktif)
        if p.suresi_doldu:
            renk = '#ef4444'
        elif p.suresi_dolmak_uzere:
            renk = '#f59e0b'

        olaylar.append({
            'id': f'pol-{p.id}',
            'title': f'Poliçe: {p.sigorta_sirketi} ({p.sigorta_turu_adi})',
            'start': p.police_bitis.isoformat(),
            'color': renk,
            'url': f'/sozlesme/police/{p.id}',
            'extendedProps': {
                'tip': 'police',
                'police_no': p.police_no,
                'sirket': p.sigorta_sirketi,
                'durum': p.durum_adi,
            }
        })

    return olaylar


# ==========================================================
# KİRA ARTIŞI HESAPLAMA
# ==========================================================

def kira_artisi_hesapla(kontrat_id, artis_orani=None):
    """
    Kira kontratı için artış hesaplama.
    Sabit yüzde ise verilen/kayıtlı oranı kullanır.
    TÜFE/ÜFE ise dışarıdan verilen oranı kullanır.

    Args:
        kontrat_id: KiraKontrat ID
        artis_orani: Decimal — Uygulananacak artış yüzdesi (ör: 25.00 = %25)

    Returns:
        dict: {'eski_kira': ..., 'yeni_kira': ..., 'artis_orani': ..., 'artis_tutari': ...}
    """
    from app.models.sozlesme import KiraKontrat

    kontrat = db.session.get(KiraKontrat, kontrat_id)
    if not kontrat or not kontrat.kira_tutari:
        return None

    eski_kira = kontrat.kira_tutari

    # Artış oranını belirle
    if artis_orani is not None:
        oran = Decimal(str(artis_orani))
    elif kontrat.artis_turu == 'sabit_yuzde' and kontrat.artis_orani:
        oran = kontrat.artis_orani
    else:
        return None  # Oran belirtilmemiş

    artis_tutari = eski_kira * oran / Decimal('100')
    yeni_kira = eski_kira + artis_tutari

    return {
        'eski_kira': float(eski_kira),
        'yeni_kira': float(yeni_kira),
        'artis_orani': float(oran),
        'artis_tutari': float(artis_tutari),
    }


def kira_artisi_uygula(kontrat_id, artis_orani):
    """
    Kira artışını uygular ve kontratı günceller.

    Args:
        kontrat_id: KiraKontrat ID
        artis_orani: Decimal

    Returns:
        dict: Hesaplama sonucu veya None
    """
    from app.models.sozlesme import KiraKontrat

    kontrat = db.session.get(KiraKontrat, kontrat_id)
    if not kontrat or not kontrat.kira_tutari:
        return None

    hesaplama = kira_artisi_hesapla(kontrat_id, artis_orani)
    if not hesaplama:
        return None

    # Log the history
    log_mesaji = f"[{date.today().strftime('%d.%m.%Y')}] Kira Artışı Uygulandı: %{artis_orani} oran ile kira tutarı ₺{hesaplama['eski_kira']:,.2f}'den ₺{hesaplama['yeni_kira']:,.2f}'ye yükseltildi."
    if kontrat.sozlesme:
        mevcut_not = kontrat.sozlesme.notlar or ""
        kontrat.sozlesme.notlar = f"{log_mesaji}\n{mevcut_not}".strip()
        # Üst sözleşme tutarını da güncelle
        kontrat.sozlesme.tutar = Decimal(str(hesaplama['yeni_kira']))

    # Kira tutarını güncelle
    kontrat.kira_tutari = Decimal(str(hesaplama['yeni_kira']))
    kontrat.son_artis_tarihi = date.today()

    # Sonraki artış tarihini 1 yıl sonraya ayarla
    kontrat.sonraki_artis_tarihi = date.today().replace(year=date.today().year + 1)
    kontrat.artis_orani = Decimal(str(artis_orani))

    db.session.commit()
    logger.info(f"Kira artışı uygulandı: Kontrat #{kontrat_id}, "
                f"₺{hesaplama['eski_kira']} → ₺{hesaplama['yeni_kira']} "
                f"(%{hesaplama['artis_orani']})")

    return hesaplama


# ==========================================================
# STANDART METİN ŞERVİSLERİ
# ==========================================================

def standart_metin_doldur(metin_id, degiskenler):
    """
    Standart metin şablonunu değişkenlerle doldurur.

    Args:
        metin_id: StandartMetin ID
        degiskenler: dict — {'{ortak_adi}': 'Ahmet Yılmaz', '{tutar}': '5.000'}

    Returns:
        str: Doldurulmuş metin veya None
    """
    from app.models.sozlesme import StandartMetin

    metin = db.session.get(StandartMetin, metin_id)
    if not metin:
        return None

    return metin.icerik_doldur(degiskenler)


def sozlesme_sablon_onizleme(sozlesme_id):
    """
    Sözleşme için standart metni sözleşme bilgileriyle doldurup döndürür.
    
    Args:
        sozlesme_id: Sözleşme ID
        
    Returns:
        str: HTML içerik veya None
    """
    from app.models.sozlesme import Sozlesme
    
    sozlesme = db.session.get(Sozlesme, sozlesme_id)
    if not sozlesme or not sozlesme.standart_metin_id:
        return None
        
    metin = sozlesme.standart_metin
    degerler = {}
    
    # Genel değişkenler
    taraf_adi = sozlesme.taraf_bilgi
    degerler['{taraf_adi}'] = taraf_adi
    degerler['{ortak_adi}'] = taraf_adi
    degerler['{firma_adi}'] = taraf_adi
    degerler['{sozlesme_no}'] = sozlesme.sozlesme_no
    degerler['{baslik}'] = sozlesme.baslik
    degerler['{tutar}'] = sozlesme.tutar_formatli
    degerler['{para_birimi}'] = sozlesme.para_birimi_adi
    degerler['{odeme_periyodu}'] = sozlesme.odeme_periyodu_adi
    
    # Tarihler
    degerler['{baslangic_tarihi}'] = sozlesme.baslangic_tarihi.strftime('%d.%m.%Y') if sozlesme.baslangic_tarihi else ''
    degerler['{bitis_tarihi}'] = sozlesme.bitis_tarihi.strftime('%d.%m.%Y') if sozlesme.bitis_tarihi else 'Belirsiz'
    degerler['{bugun}'] = date.today().strftime('%d.%m.%Y')
    
    # Kira detayları
    if sozlesme.tur == 'kira' and sozlesme.kira_kontrat:
        kira = sozlesme.kira_kontrat
        degerler['{daire_no}'] = kira.daire_no or ''
        degerler['{blok}'] = kira.blok or ''
        degerler['{kat}'] = kira.kat or ''
        degerler['{m2}'] = f"{kira.m2} m²" if kira.m2 else ''
        degerler['{depozito}'] = f"₺ {kira.depozito:,.2f}" if kira.depozito else ''
        degerler['{aidat}'] = f"₺ {kira.aidat_tutari:,.2f}" if kira.aidat_tutari else ''
        degerler['{konum_bilgi}'] = kira.konum_bilgi
        degerler['{odeme_gunu}'] = str(kira.odeme_gunu) if kira.odeme_gunu else ''
        degerler['{artis_orani}'] = f"%{kira.artis_orani}" if kira.artis_orani else ''
        
    return metin.icerik_doldur(degerler)


def standart_metin_listesi(tur=None):
    """
    Aktif standart metinleri listeler.

    Args:
        tur: Filtrelenecek tür (opsiyonel)

    Returns:
        list: StandartMetin listesi
    """
    from app.models.sozlesme import StandartMetin

    sorgu = StandartMetin.query.filter_by(aktif=True)
    if tur:
        sorgu = sorgu.filter_by(tur=tur)
    return sorgu.order_by(StandartMetin.baslik).all()


# ==========================================================
# RAPOR & DETAY SERVİSLERİ
# ==========================================================

def sozlesme_detay_rapor(sozlesme_id):
    """
    Sözleşme detay kartı için tüm verileri toplar.

    Args:
        sozlesme_id: Sözleşme ID

    Returns:
        dict: Detay raporu veya None
    """
    from app.models.sozlesme import Sozlesme, KiraKontrat, SigortaPolice
    from app.models.crm import Ortak, Firma

    sozlesme = db.session.get(Sozlesme, sozlesme_id)
    if not sozlesme:
        return None

    # Taraf bilgisini getir
    taraf = None
    if sozlesme.taraf_tip == 'ortak':
        taraf = db.session.get(Ortak, sozlesme.taraf_id)
    elif sozlesme.taraf_tip == 'firma':
        taraf = db.session.get(Firma, sozlesme.taraf_id)

    # Kira kontratı detayı
    kira = None
    if sozlesme.tur == 'kira':
        kira = KiraKontrat.query.filter_by(sozlesme_id=sozlesme.id).first()

    # Sigorta poliçesi detayı
    police = None
    if sozlesme.tur == 'sigorta':
        police = SigortaPolice.query.filter_by(sozlesme_id=sozlesme.id).first()

    return {
        'sozlesme': sozlesme,
        'taraf': taraf,
        'kira': kira,
        'police': police,
    }


def sozlesme_rapor(filtre=None):
    """
    Sözleşme durum raporu.

    Args:
        filtre: dict — {'tur': 'kira', 'durum': 'aktif', 'taraf_tip': 'ortak'}

    Returns:
        dict: Rapor verileri
    """
    from app.models.sozlesme import Sozlesme

    sorgu = Sozlesme.query.filter_by(aktif=True)

    if filtre:
        if filtre.get('tur'):
            sorgu = sorgu.filter(Sozlesme.tur == filtre['tur'])
        if filtre.get('durum'):
            sorgu = sorgu.filter(Sozlesme.durum == filtre['durum'])
        if filtre.get('taraf_tip'):
            sorgu = sorgu.filter(Sozlesme.taraf_tip == filtre['taraf_tip'])

    sozlesmeler = sorgu.order_by(Sozlesme.bitis_tarihi.asc()).all()

    # Toplam tutar
    toplam_tutar = sum(float(s.tutar or 0) for s in sozlesmeler)

    return {
        'sozlesmeler': sozlesmeler,
        'toplam': len(sozlesmeler),
        'toplam_tutar': toplam_tutar,
    }


# ==========================================================
# NUMARA ÜRETEÇLERİ
# ==========================================================

def sonraki_sozlesme_no():
    """
    Sıradaki sözleşme numarasını üretir.

    Returns:
        str: Yeni sözleşme no (ör: "SZL-2026-00001")
    """
    from app.models.sozlesme import Sozlesme

    yil = datetime.now().year
    prefix = f'SZL-{yil}-'

    son = Sozlesme.query.filter(
        Sozlesme.sozlesme_no.like(f'{prefix}%')
    ).order_by(Sozlesme.sozlesme_no.desc()).first()

    if son:
        try:
            sayi = int(son.sozlesme_no.split('-')[-1]) + 1
        except (ValueError, IndexError):
            sayi = 1
    else:
        sayi = 1

    return f'{prefix}{sayi:05d}'


def sonraki_police_no():
    """
    Sıradaki poliçe numarasını üretir.

    Returns:
        str: Yeni poliçe no (ör: "PLÇ-2026-00001")
    """
    from app.models.sozlesme import SigortaPolice

    yil = datetime.now().year
    prefix = f'PLC-{yil}-'

    son = SigortaPolice.query.filter(
        SigortaPolice.police_no.like(f'{prefix}%')
    ).order_by(SigortaPolice.police_no.desc()).first()

    if son:
        try:
            sayi = int(son.police_no.split('-')[-1]) + 1
        except (ValueError, IndexError):
            sayi = 1
    else:
        sayi = 1

    return f'{prefix}{sayi:05d}'


# ==========================================================
# YARDIMCI FONKSİYONLAR
# ==========================================================

def taraf_secenekleri(taraf_tip='ortak'):
    """
    Form için taraf (ortak/firma) seçeneklerini döndürür.

    Args:
        taraf_tip: 'ortak' veya 'firma'

    Returns:
        list: [(id, ad), ...]
    """
    if taraf_tip == 'ortak':
        from app.models.crm import Ortak
        taraflar = Ortak.query.filter_by(aktif=True, durum='aktif').order_by(Ortak.ad_soyad).all()
        return [(t.id, f'{t.ortak_no} — {t.ad_soyad}') for t in taraflar]
    else:
        from app.models.crm import Firma
        taraflar = Firma.query.filter_by(aktif=True, durum='aktif').order_by(Firma.unvan).all()
        return [(t.id, f'{t.firma_no} — {t.unvan}') for t in taraflar]


def standart_metin_secenekleri():
    """
    Form için standart metin seçeneklerini döndürür.

    Returns:
        list: [(id, baslik), ...]
    """
    from app.models.sozlesme import StandartMetin
    metinler = StandartMetin.query.filter_by(aktif=True).order_by(StandartMetin.baslik).all()
    return [(0, '— Şablon Seçin —')] + [(m.id, f'{m.tur_adi}: {m.baslik}') for m in metinler]


def sozlesme_excel_export(filtre=None):
    """
    Sözleşmeleri Excel formatında dışa aktarır.

    Returns:
        bytes: Excel dosya içeriği
    """
    from app.models.sozlesme import Sozlesme
    import io

    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill
    except ImportError:
        logger.warning("openpyxl yüklü değil, Excel export yapılamıyor.")
        return None

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Sözleşmeler'

    basliklar = [
        'Sözleşme No', 'Tür', 'Başlık', 'Taraf Tipi', 'Taraf',
        'Başlangıç', 'Bitiş', 'Tutar', 'Para Birimi', 'Ödeme Periyodu',
        'Durum', 'Kalan Gün', 'Notlar',
    ]
    ws.append(basliklar)

    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='6366F1', end_color='6366F1', fill_type='solid')
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill

    sorgu = Sozlesme.query.filter_by(aktif=True)
    if filtre and filtre.get('tur'):
        sorgu = sorgu.filter(Sozlesme.tur == filtre['tur'])

    sozlesmeler = sorgu.order_by(Sozlesme.sozlesme_no).all()

    for s in sozlesmeler:
        ws.append([
            s.sozlesme_no, s.tur_adi, s.baslik, s.taraf_tip_adi,
            s.taraf_bilgi,
            s.baslangic_tarihi.strftime('%d.%m.%Y') if s.baslangic_tarihi else '',
            s.bitis_tarihi.strftime('%d.%m.%Y') if s.bitis_tarihi else '',
            float(s.tutar) if s.tutar else '',
            s.para_birimi, s.odeme_periyodu_adi, s.durum_adi,
            s.kalan_gun if s.kalan_gun is not None else '',
            s.notlar or '',
        ])

    for col in ws.columns:
        max_len = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_len:
                    max_len = len(str(cell.value))
            except Exception:
                pass
        ws.column_dimensions[column].width = min(max_len + 2, 40)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()
