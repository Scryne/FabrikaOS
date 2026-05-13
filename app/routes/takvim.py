"""
FDYS — Takvim Görünümü Rotaları
Faz 5 — FullCalendar.js Entegrasyonu

Bakım, vardiya ve izin takvimlerini birleşik görünümde sunar.
"""

import logging
from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.makine import Makine, BakimKaydi
from app.models.personel import Calisan, VardiyaPlani, IzinTalebi

logger = logging.getLogger(__name__)

takvim_bp = Blueprint('takvim', __name__, url_prefix='/takvim')

VARDIYA_RENKLERI = {
    'sabah': '#3b82f6',
    'ogleden_sonra': '#f59e0b',
    'gece': '#8b5cf6',
    'off': '#6b7280',
}


@takvim_bp.route('/')
@login_required
def index():
    """Birleşik takvim sayfası."""
    return render_template('takvim/index.html')


@takvim_bp.route('/api/etkinlikler')
@login_required
def api_etkinlikler():
    """FullCalendar event feed — tüm etkinlik türleri."""
    start_str = request.args.get('start', '')
    end_str = request.args.get('end', '')
    filtre = request.args.get('filtre', 'hepsi')  # hepsi, bakim, vardiya, izin

    try:
        start = datetime.fromisoformat(start_str.replace('Z', '+00:00')).date() if start_str else (datetime.now() - timedelta(days=30)).date()
        end = datetime.fromisoformat(end_str.replace('Z', '+00:00')).date() if end_str else (datetime.now() + timedelta(days=60)).date()
    except (ValueError, TypeError):
        start = (datetime.now() - timedelta(days=30)).date()
        end = (datetime.now() + timedelta(days=60)).date()

    events = []

    if filtre in ('hepsi', 'bakim'):
        events.extend(_bakim_etkinlikleri(start, end))

    if filtre in ('hepsi', 'vardiya'):
        events.extend(_vardiya_etkinlikleri(start, end))

    if filtre in ('hepsi', 'izin'):
        events.extend(_izin_etkinlikleri(start, end))

    return jsonify(events)


def _bakim_etkinlikleri(start, end):
    """Planlanan bakım tarihlerini event olarak döner."""
    events = []
    bugun = datetime.now(timezone.utc).date()
    makineler = Makine.query.filter_by(aktif=True).all()

    for m in makineler:
        sonraki = m.sonraki_bakim_tarihi
        if sonraki and start <= sonraki <= end:
            gecikti = sonraki < bugun
            events.append({
                'id': f'bakim_{m.id}',
                'title': f'🔧 {m.ad} — Bakım',
                'start': sonraki.isoformat(),
                'allDay': True,
                'color': '#ef4444' if gecikti else '#22c55e',
                'textColor': '#ffffff',
                'extendedProps': {
                    'tip': 'bakim',
                    'makine_kod': m.kod,
                    'makine_ad': m.ad,
                    'gecikti': gecikti,
                    'detay': f'Periyodik bakım ({m.periyodik_bakim_gun} gün)'
                }
            })

    # Son yapılan bakımlar
    bakimlar = BakimKaydi.query.filter(
        BakimKaydi.tarih >= start,
        BakimKaydi.tarih <= end,
        BakimKaydi.aktif == True
    ).all()

    for b in bakimlar:
        events.append({
            'id': f'bakim_yapilan_{b.id}',
            'title': f'✅ {b.makine.ad} — {b.bakim_turu}',
            'start': b.tarih.isoformat(),
            'allDay': True,
            'color': '#059669',
            'textColor': '#ffffff',
            'extendedProps': {
                'tip': 'bakim_yapilan',
                'makine_ad': b.makine.ad if b.makine else '—',
                'bakim_turu': b.bakim_turu,
                'detay': b.yapilan_islem[:100] if b.yapilan_islem else ''
            }
        })

    return events


def _vardiya_etkinlikleri(start, end):
    """Vardiya planlarını event olarak döner."""
    events = []

    # Yöneticiler tüm vardiyaları, diğerleri sadece kendilerini görür
    query = VardiyaPlani.query.filter(
        VardiyaPlani.tarih >= start,
        VardiyaPlani.tarih <= end,
        VardiyaPlani.aktif == True
    )

    if not current_user.yonetici_mi():
        if current_user.calisan:
            query = query.filter(VardiyaPlani.calisan_id == current_user.calisan.id)
        else:
            return events

    vardiyalar = query.all()

    for v in vardiyalar:
        renk = VARDIYA_RENKLERI.get(v.vardiya_turu, '#6b7280')
        tur_etiket = {'sabah': 'Sabah', 'ogleden_sonra': 'Öğleden Sonra', 'gece': 'Gece', 'off': 'İzinli'}.get(v.vardiya_turu, v.vardiya_turu)

        events.append({
            'id': f'vardiya_{v.id}',
            'title': f'{v.calisan.ad_soyad} — {tur_etiket}',
            'start': v.tarih.isoformat(),
            'allDay': True,
            'color': renk,
            'textColor': '#ffffff',
            'extendedProps': {
                'tip': 'vardiya',
                'calisan': v.calisan.ad_soyad,
                'vardiya_turu': tur_etiket,
                'saat': f'{v.baslangic.strftime("%H:%M")} - {v.bitis.strftime("%H:%M")}',
                'detay': v.notlar or ''
            }
        })

    return events


def _izin_etkinlikleri(start, end):
    """Onaylanan izinleri event olarak döner."""
    events = []

    query = IzinTalebi.query.filter(
        IzinTalebi.durum == 'onaylandi',
        IzinTalebi.bitis_tarihi >= start,
        IzinTalebi.baslangic_tarihi <= end
    )

    if not current_user.yonetici_mi():
        if current_user.calisan:
            query = query.filter(IzinTalebi.calisan_id == current_user.calisan.id)
        else:
            return events

    izinler = query.all()

    tur_renkleri = {'yillik': '#06b6d4', 'mazeret': '#f97316', 'saglik': '#ef4444', 'ucretsiz': '#78716c'}
    tur_etiket = {'yillik': 'Yıllık İzin', 'mazeret': 'Mazeret İzni', 'saglik': 'Sağlık İzni', 'ucretsiz': 'Ücretsiz İzin'}

    for iz in izinler:
        renk = tur_renkleri.get(iz.tur, '#6b7280')
        events.append({
            'id': f'izin_{iz.id}',
            'title': f'🏖️ {iz.calisan.ad_soyad} — {tur_etiket.get(iz.tur, iz.tur)}',
            'start': iz.baslangic_tarihi.isoformat(),
            'end': (iz.bitis_tarihi + timedelta(days=1)).isoformat(),
            'allDay': True,
            'color': renk,
            'textColor': '#ffffff',
            'extendedProps': {
                'tip': 'izin',
                'calisan': iz.calisan.ad_soyad,
                'izin_turu': tur_etiket.get(iz.tur, iz.tur),
                'detay': iz.aciklama or ''
            }
        })

    return events
