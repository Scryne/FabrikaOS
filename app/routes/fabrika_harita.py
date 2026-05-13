"""
FDYS — İnteraktif Fabrika Haritası (Dijital İkiz Lite)
v2.0 — Production-Grade

Özellikler:
    - SVG tabanlı 2D fabrika haritası (üstten bakış)
    - Renk kodlu makine durumları
    - Hover popup (OEE, arıza, operatör)
    - Admin: Sürükle-bırak makine yerleşimi
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.extensions import db, csrf
from app.models.makine import Makine, UretimVerisi, ArizaKaydi, BakimKaydi
from app.utils.decorators import modul_erisim_gerekli
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from sqlalchemy.orm import joinedload

fabrika_harita_bp = Blueprint('fabrika_harita', __name__, url_prefix='/fabrika-harita')

# ── Zone definitions matching SVG layout in index.html ──
# Each zone: (x_start, y_start, x_end, y_end)
ZONES = {
    'a':      (35,  35,  590, 325),   # Üretim Hattı A (sol üst)
    'b':      (610, 35,  1165, 325),  # Üretim Hattı B (sağ üst)
    'montaj': (35,  345, 790, 645),   # Montaj & Final (sol alt)
    'depo':   (810, 345, 1165, 645),  # Depo (sağ alt)
}
NODE_W, NODE_H = 150, 85
NODE_PAD = 20  # spacing between nodes


def _lokasyon_to_zone(lokasyon):
    """Lokasyon string'inden zone key belirle."""
    if not lokasyon:
        return 'a'
    loc = lokasyon.lower().strip()
    if any(k in loc for k in ['b hattı', 'b hatti', 'hat b', 'hattı b', 'hatti b', 'b hat']):
        return 'b'
    if any(k in loc for k in ['montaj', 'final', 'assembly']):
        return 'montaj'
    if any(k in loc for k in ['depo', 'ambar', 'stok', 'warehouse']):
        return 'depo'
    # Default: A Hattı or any other
    return 'a'


def otomatik_konum_ata(makine):
    """Yeni makineye fabrika haritasında otomatik konum atar.

    Lokasyon alanına göre uygun bölgeyi belirler,
    o bölgedeki boş bir slota yerleştirir.
    """
    zone_key = _lokasyon_to_zone(makine.lokasyon)
    zx1, zy1, zx2, zy2 = ZONES[zone_key]

    # Mevcut makinelerin konumlarını al
    mevcut = Makine.query.filter(
        Makine.aktif == True,
        Makine.konum_x.isnot(None),
        Makine.konum_y.isnot(None)
    ).all()

    occupied = set()
    for m in mevcut:
        occupied.add((int(m.konum_x), int(m.konum_y)))

    # Grid üzerinde boş slot bul (Sliding window tekniği)
    padding_top = 40  # zone label için boşluk
    start_x = zx1 + NODE_PAD
    start_y = zy1 + padding_top

    y = start_y
    while y + NODE_H + NODE_PAD <= zy2:
        x = start_x
        while x + NODE_W + NODE_PAD <= zx2:
            # Bu pozisyonda çakışma var mı?
            collision = False
            for ox, oy in occupied:
                # Top-left tabanlı overlap kontrolü (10px güvenlik payı ile)
                if x < ox + NODE_W + 10 and x + NODE_W + 10 > ox and \
                   y < oy + NODE_H + 10 and y + NODE_H + 10 > oy:
                    collision = True
                    break
            
            if not collision:
                makine.konum_x = x
                makine.konum_y = y
                makine.konum_w = NODE_W
                makine.konum_h = NODE_H
                return
            
            # Eğer çakışma varsa, katı grid atlamak yerine 20 piksel kayarak devam et
            x += 20
        y += 20

    # Tüm alan doluysa, makineleri birbirinden ayırt edilebilir kaskad (şelale) offset ile yerleştir
    offset_multiplier = len(occupied) % 10
    makine.konum_x = start_x + (offset_multiplier * 15)
    makine.konum_y = start_y + (offset_multiplier * 15)
    makine.konum_w = NODE_W
    makine.konum_h = NODE_H


@fabrika_harita_bp.route('/')
@login_required
@modul_erisim_gerekli('makine')
def index():
    """İnteraktif fabrika haritası ana sayfası."""
    makineler = Makine.query.filter_by(aktif=True).all()

    toplam = len(makineler)
    calisir = sum(1 for m in makineler if m.durum == 'aktif')
    arizali = sum(1 for m in makineler if m.durum == 'arizali')
    bakimda = sum(1 for m in makineler if m.durum == 'bakimda')

    yedi_gun_once = datetime.now(timezone.utc).date() - timedelta(days=7)
    ortalama_oee = db.session.query(func.avg(UretimVerisi.oee_yuzde)) \
        .filter(UretimVerisi.tarih >= yedi_gun_once).scalar() or 0

    return render_template('fabrika_harita/index.html',
                           is_admin=current_user.yonetici_mi(),
                           stats={
                               'toplam': toplam,
                               'calisir': calisir,
                               'arizali': arizali,
                               'bakimda': bakimda,
                               'ort_oee': round(float(ortalama_oee), 1),
                           })


@fabrika_harita_bp.route('/api/makineler')
@login_required
def api_makineler():
    """Tüm aktif makinelerin konum ve durum bilgilerini JSON olarak döner.

    v2.0: N+1 query düzeltmesi — tüm veriler batch subquery ile alınır.
    """
    try:
        makineler = Makine.query.filter_by(aktif=True).all()
        makine_idler = [m.id for m in makineler]

        if not makine_idler:
            return jsonify([])

        bugun = datetime.now(timezone.utc).date()
        yedi_gun_once = bugun - timedelta(days=7)

        # Batch: tüm makineler için OEE ortalamaları (tek sorgu)
        oee_results = db.session.query(
            UretimVerisi.makine_id,
            func.avg(UretimVerisi.oee_yuzde)
        ).filter(
            UretimVerisi.makine_id.in_(makine_idler),
            UretimVerisi.tarih >= yedi_gun_once
        ).group_by(UretimVerisi.makine_id).all()
        oee_map = {r[0]: round(float(r[1]), 1) if r[1] else None for r in oee_results}

        # Batch: bugünkü üretim toplamları (tek sorgu)
        uretim_results = db.session.query(
            UretimVerisi.makine_id,
            func.sum(UretimVerisi.gercek_uretim)
        ).filter(
            UretimVerisi.makine_id.in_(makine_idler),
            UretimVerisi.tarih == bugun
        ).group_by(UretimVerisi.makine_id).all()
        uretim_map = {r[0]: int(r[1]) if r[1] else 0 for r in uretim_results}

        # Batch: son operatör bilgisi (window function yerine subquery — tek sorgu)
        from app.models.personel import Calisan
        son_uretim_sub = db.session.query(
            UretimVerisi.makine_id,
            func.max(UretimVerisi.id).label('max_id')
        ).filter(
            UretimVerisi.makine_id.in_(makine_idler)
        ).group_by(UretimVerisi.makine_id).subquery()

        son_operator_results = db.session.query(
            UretimVerisi.makine_id,
            Calisan.ad_soyad
        ).join(son_uretim_sub, UretimVerisi.id == son_uretim_sub.c.max_id)\
         .join(Calisan, UretimVerisi.calisan_id == Calisan.id).all()
        operator_map = {r[0]: r[1] for r in son_operator_results}

        # Batch: son arızalar (tek sorgu)
        son_ariza_sub = db.session.query(
            ArizaKaydi.makine_id,
            func.max(ArizaKaydi.id).label('max_id')
        ).filter(
            ArizaKaydi.makine_id.in_(makine_idler)
        ).group_by(ArizaKaydi.makine_id).subquery()

        son_ariza_results = db.session.query(
            ArizaKaydi.makine_id,
            ArizaKaydi.ariza_turu,
            ArizaKaydi.durum,
            ArizaKaydi.baslangic_zamani
        ).join(son_ariza_sub, ArizaKaydi.id == son_ariza_sub.c.max_id).all()

        ariza_map = {r[0]: {
            'tur': r[1], 'durum': r[2],
            'tarih': r[3].strftime('%d.%m.%Y') if r[3] else None,
        } for r in son_ariza_results}

        # Batch: Mini OEE trend (son 7 gün, her makine için — tek sorgu)
        oee_trend_results = db.session.query(
            UretimVerisi.makine_id,
            UretimVerisi.tarih,
            func.avg(UretimVerisi.oee_yuzde).label('ort_oee')
        ).filter(
            UretimVerisi.makine_id.in_(makine_idler),
            UretimVerisi.tarih >= yedi_gun_once
        ).group_by(UretimVerisi.makine_id, UretimVerisi.tarih)\
         .order_by(UretimVerisi.makine_id, UretimVerisi.tarih).all()

        trend_map = {}
        for r in oee_trend_results:
            if r[0] not in trend_map:
                trend_map[r[0]] = []
            trend_map[r[0]].append(round(float(r[2]), 1) if r[2] else 0)

        sonuc = []
        for m in makineler:
            sonuc.append({
                'id': m.id,
                'ad': m.ad,
                'kod': m.kod,
                'durum': m.durum,
                'lokasyon': m.lokasyon or '',
                'konum_x': m.konum_x,
                'konum_y': m.konum_y,
                'konum_w': m.konum_w or 150,
                'konum_h': m.konum_h or 85,
                'oee': oee_map.get(m.id),
                'hedef_oee': float(m.hedef_oee) if m.hedef_oee else 85.0,
                'operator': operator_map.get(m.id),
                'son_ariza': ariza_map.get(m.id),
                'son_bakim_tarihi': m.son_bakim_tarihi.strftime('%d.%m.%Y') if m.son_bakim_tarihi else None,
                'sonraki_bakim': m.sonraki_bakim_tarihi.strftime('%d.%m.%Y') if m.sonraki_bakim_tarihi else None,
                'bakim_gecikti': m.bakim_gecikti_mi,
                'bugun_uretim': uretim_map.get(m.id, 0),
                'teorik_kapasite': m.teorik_kapasite,
                'oee_trend': trend_map.get(m.id, []),
            })

        return jsonify(sonuc)

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Fabrika harita API hatası: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@fabrika_harita_bp.route('/api/toplu-konum-guncelle', methods=['POST'])
@login_required
def toplu_konum_guncelle():
    """Admin: Birden fazla makinenin konumunu tek seferde günceller."""
    if not current_user.yonetici_mi():
        return jsonify({'error': 'Yetki yok'}), 403

    try:
        data = request.get_json()
        if not data or 'makineler' not in data:
            return jsonify({'error': 'Geçersiz veri'}), 400

        guncellenen = 0
        for item in data['makineler']:
            makine_id = item.get('makine_id')
            if not makine_id:
                continue
            makine = db.session.get(Makine, makine_id)
            if makine:
                makine.konum_x = item.get('konum_x')
                makine.konum_y = item.get('konum_y')
                if item.get('konum_w') is not None:
                    makine.konum_w = item.get('konum_w')
                if item.get('konum_h') is not None:
                    makine.konum_h = item.get('konum_h')
                guncellenen += 1

        db.session.commit()
        return jsonify({'success': True, 'message': f'{guncellenen} makine konumu güncellendi'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
