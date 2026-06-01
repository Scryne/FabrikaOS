"""
FDYS — Sanayi Sitesi İnteraktif Haritası
Faz 8 — Leaflet.js / OpenStreetMap Tabanlı

Özellikler:
    - CRM ortak/firma lokasyonlarını harita üzerinde gösterme (marker + popup)
    - Blok/bina bazlı filtreleme
    - Sözleşme durumu renk kodu (aktif: yeşil, sona eriyor: sarı, sona ermiş: kırmızı)
    - Katman kontrolleri (ortaklar, firmalar, arızalar, talepler)
    - İstatistik dashboard kartları
    - API endpoint'leri (JSON)
"""

import logging
from datetime import date

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func, and_, or_

from app.extensions import db, csrf
from app.models.crm import Ortak, Firma
from app.models.sozlesme import Sozlesme
from app.models.talep import Talep
from app.utils.decorators import modul_erisim_gerekli

logger = logging.getLogger(__name__)

site_harita_bp = Blueprint('site_harita', __name__, url_prefix='/sanayi-harita')


# ────────────────────────────────────────────────────────────
# Ana Sayfa
# ────────────────────────────────────────────────────────────
@site_harita_bp.route('/')
@login_required
@modul_erisim_gerekli('crm')
def index():
    """Sanayi sitesi interaktif harita ana sayfası."""
    try:
        # İstatistikler
        toplam_ortak = Ortak.query.filter_by(aktif=True).count()
        aktif_ortak = Ortak.query.filter_by(aktif=True, durum='aktif').count()
        toplam_firma = Firma.query.filter_by(aktif=True).count()
        aktif_firma = Firma.query.filter_by(aktif=True, durum='aktif').count()

        # Koordinatlı kayıtlar (haritada gösterilebilecek)
        haritali_ortak = Ortak.query.filter(
            Ortak.aktif == True,
            Ortak.harita_enlem.isnot(None),
            Ortak.harita_boylam.isnot(None)
        ).count()
        haritali_firma = Firma.query.filter(
            Firma.aktif == True,
            Firma.harita_enlem.isnot(None),
            Firma.harita_boylam.isnot(None)
        ).count()

        # Sözleşme durumu özeti
        bugun = date.today()
        aktif_sozlesme = Sozlesme.query.filter_by(aktif=True, durum='aktif').count()
        sona_eriyor = Sozlesme.query.filter(
            Sozlesme.aktif == True,
            Sozlesme.durum == 'aktif',
            Sozlesme.bitis_tarihi.isnot(None),
            Sozlesme.bitis_tarihi > bugun,
            Sozlesme.bitis_tarihi <= func.date(bugun, '+30 days')
        ).count()

        # Açık talepler
        acik_talep = Talep.query.filter(
            Talep.aktif == True,
            Talep.durum.in_(['acik', 'yonlendirildi', 'devam'])
        ).count()

        # Blok listesi (filtreleme için)
        bloklar_ortak = db.session.query(Ortak.blok).filter(
            Ortak.aktif == True,
            Ortak.blok.isnot(None),
            Ortak.blok != ''
        ).distinct().all()
        bloklar_firma = db.session.query(Firma.blok).filter(
            Firma.aktif == True,
            Firma.blok.isnot(None),
            Firma.blok != ''
        ).distinct().all()
        bloklar = sorted(set(
            [b[0] for b in bloklar_ortak] + [b[0] for b in bloklar_firma]
        ))

        stats = {
            'toplam_ortak': toplam_ortak,
            'aktif_ortak': aktif_ortak,
            'toplam_firma': toplam_firma,
            'aktif_firma': aktif_firma,
            'haritali_ortak': haritali_ortak,
            'haritali_firma': haritali_firma,
            'aktif_sozlesme': aktif_sozlesme,
            'sona_eriyor_sozlesme': sona_eriyor,
            'acik_talep': acik_talep,
        }

        return render_template('site_harita/index.html',
                               stats=stats,
                               bloklar=bloklar)
    except Exception as e:
        logger.error(f"Sanayi harita sayfası hatası: {e}", exc_info=True)
        return render_template('site_harita/index.html',
                               stats={},
                               bloklar=[])


# ────────────────────────────────────────────────────────────
# API: Harita Verileri
# ────────────────────────────────────────────────────────────
@site_harita_bp.route('/api/veriler')
@login_required
def api_veriler():
    """
    Harita için tüm ortak/firma/talep verilerini JSON olarak döner.
    Sözleşme durumu renk kodu ile birlikte.

    Query Params:
        blok: Blok filtresi (opsiyonel)
        katman: Katman filtresi (ortaklar|firmalar|talepler) — virgülle ayrılmış
    """
    try:
        blok_filtre = request.args.get('blok', '').strip()
        katman_filtre = request.args.get('katman', 'ortaklar,firmalar,talepler').split(',')

        sonuc = {
            'ortaklar': [],
            'firmalar': [],
            'talepler': [],
            'istatistik': {}
        }

        bugun = date.today()

        # ── Ortaklar ──
        if 'ortaklar' in katman_filtre:
            ortak_sorgu = Ortak.query.filter(
                Ortak.aktif == True,
                Ortak.harita_enlem.isnot(None),
                Ortak.harita_boylam.isnot(None)
            )
            if blok_filtre:
                ortak_sorgu = ortak_sorgu.filter(Ortak.blok == blok_filtre)

            ortaklar = ortak_sorgu.all()

            # Batch: Her ortak için sözleşme durumu (tek sorgu)
            ortak_idler = [o.id for o in ortaklar]
            sozlesme_map = {}
            if ortak_idler:
                sozlesme_rows = db.session.query(
                    Sozlesme.taraf_id,
                    Sozlesme.durum,
                    Sozlesme.bitis_tarihi
                ).filter(
                    Sozlesme.taraf_tip == 'ortak',
                    Sozlesme.taraf_id.in_(ortak_idler),
                    Sozlesme.aktif == True
                ).all()

                for row in sozlesme_rows:
                    oid = row[0]
                    if oid not in sozlesme_map:
                        sozlesme_map[oid] = []
                    kalan = (row[2] - bugun).days if row[2] else None
                    sozlesme_map[oid].append({
                        'durum': row[1],
                        'bitis': row[2].isoformat() if row[2] else None,
                        'kalan_gun': kalan
                    })

            for o in ortaklar:
                sozlesmeler = sozlesme_map.get(o.id, [])
                renk_kodu = _hesapla_renk_kodu(sozlesmeler, bugun)

                sonuc['ortaklar'].append({
                    'id': o.id,
                    'ortak_no': o.ortak_no,
                    'ad_soyad': o.ad_soyad,
                    'telefon': o.telefon,
                    'ortak_tipi': o.ortak_tipi_adi,
                    'blok': o.blok,
                    'daire_no': o.daire_no,
                    'konum': o.konum_bilgi,
                    'm2': float(o.m2) if o.m2 else None,
                    'durum': o.durum,
                    'durum_adi': o.durum_adi,
                    'lat': o.harita_enlem,
                    'lng': o.harita_boylam,
                    'sozlesme_renk': renk_kodu,
                    'sozlesme_sayisi': len(sozlesmeler),
                    'baslangic_harfler': o.baslangic_harfler,
                })

        # ── Firmalar ──
        if 'firmalar' in katman_filtre:
            firma_sorgu = Firma.query.filter(
                Firma.aktif == True,
                Firma.harita_enlem.isnot(None),
                Firma.harita_boylam.isnot(None)
            )
            if blok_filtre:
                firma_sorgu = firma_sorgu.filter(Firma.blok == blok_filtre)

            firmalar = firma_sorgu.all()

            firma_idler = [f.id for f in firmalar]
            firma_sozlesme_map = {}
            if firma_idler:
                firma_sozlesme_rows = db.session.query(
                    Sozlesme.taraf_id,
                    Sozlesme.durum,
                    Sozlesme.bitis_tarihi
                ).filter(
                    Sozlesme.taraf_tip == 'firma',
                    Sozlesme.taraf_id.in_(firma_idler),
                    Sozlesme.aktif == True
                ).all()

                for row in firma_sozlesme_rows:
                    fid = row[0]
                    if fid not in firma_sozlesme_map:
                        firma_sozlesme_map[fid] = []
                    kalan = (row[2] - bugun).days if row[2] else None
                    firma_sozlesme_map[fid].append({
                        'durum': row[1],
                        'bitis': row[2].isoformat() if row[2] else None,
                        'kalan_gun': kalan
                    })

            for f in firmalar:
                sozlesmeler = firma_sozlesme_map.get(f.id, [])
                renk_kodu = _hesapla_renk_kodu(sozlesmeler, bugun)

                sonuc['firmalar'].append({
                    'id': f.id,
                    'firma_no': f.firma_no,
                    'unvan': f.unvan,
                    'telefon': f.telefon,
                    'sektor': f.sektor_adi,
                    'blok': f.blok,
                    'daire_no': f.daire_no,
                    'konum': f.konum_bilgi,
                    'm2': float(f.m2) if f.m2 else None,
                    'calisan_sayisi': f.calisan_sayisi,
                    'durum': f.durum,
                    'durum_adi': f.durum_adi,
                    'lat': f.harita_enlem,
                    'lng': f.harita_boylam,
                    'sozlesme_renk': renk_kodu,
                    'sozlesme_sayisi': len(sozlesmeler),
                    'baslangic_harfler': f.baslangic_harfler,
                })

        # ── Talepler (konum bilgisi olan açık talepler) ──
        if 'talepler' in katman_filtre:
            talep_sorgu = Talep.query.filter(
                Talep.aktif == True,
                Talep.durum.in_(['acik', 'yonlendirildi', 'devam']),
                Talep.konum_bilgi.isnot(None),
                Talep.konum_bilgi != ''
            )

            talepler = talep_sorgu.limit(200).all()

            for t in talepler:
                # Talepleri konum bilgisine göre ilişkili ortağa bağla
                # GPS koordinatı talep modelinde yok — bu talepler popup'ta gösterilir
                sonuc['talepler'].append({
                    'id': t.id,
                    'talep_no': t.talep_no,
                    'baslik': t.baslik,
                    'kategori': t.kategori_adi,
                    'oncelik': t.oncelik,
                    'oncelik_adi': t.oncelik_adi,
                    'durum': t.durum,
                    'durum_adi': t.durum_adi,
                    'konum_bilgi': t.konum_bilgi,
                    'gecen_sure': t.gecen_sure_str,
                })

        # ── İstatistikler ──
        sonuc['istatistik'] = {
            'ortak_sayisi': len(sonuc['ortaklar']),
            'firma_sayisi': len(sonuc['firmalar']),
            'talep_sayisi': len(sonuc['talepler']),
        }

        return jsonify(sonuc)

    except Exception as e:
        logger.error(f"Sanayi harita API hatası: {e}", exc_info=True)
        return jsonify({'error': 'Veriler yüklenirken bir hata oluştu'}), 500


# ────────────────────────────────────────────────────────────
# API: Blok/Bina Detay
# ────────────────────────────────────────────────────────────
@site_harita_bp.route('/api/blok/<string:blok_adi>')
@login_required
def api_blok_detay(blok_adi):
    """Belirli bir blok/binadaki ortak ve firma listesi."""
    try:
        ortaklar = Ortak.query.filter_by(aktif=True, blok=blok_adi).all()
        firmalar = Firma.query.filter_by(aktif=True, blok=blok_adi).all()

        return jsonify({
            'blok': blok_adi,
            'ortaklar': [{
                'id': o.id,
                'ortak_no': o.ortak_no,
                'ad_soyad': o.ad_soyad,
                'daire_no': o.daire_no,
                'ortak_tipi': o.ortak_tipi_adi,
                'durum': o.durum_adi,
            } for o in ortaklar],
            'firmalar': [{
                'id': f.id,
                'firma_no': f.firma_no,
                'unvan': f.unvan,
                'daire_no': f.daire_no,
                'sektor': f.sektor_adi,
                'durum': f.durum_adi,
            } for f in firmalar],
            'toplam': len(ortaklar) + len(firmalar),
        })
    except Exception as e:
        logger.error(f"Blok detay API hatası: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ────────────────────────────────────────────────────────────
# API: Koordinat Güncelleme
# ────────────────────────────────────────────────────────────
@site_harita_bp.route('/api/koordinat-guncelle', methods=['POST'])
@login_required
def api_koordinat_guncelle():
    """
    Ortak veya firma koordinatını günceller (admin sürükle-bırak).

    Body:
        {
            "tip": "ortak" | "firma",
            "id": 123,
            "lat": 41.0082,
            "lng": 28.9784
        }
    """
    if not current_user.yonetici_mi():
        return jsonify({'error': 'Yetki yok'}), 403

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Geçersiz veri'}), 400

        tip = data.get('tip')
        obj_id = data.get('id')
        lat = data.get('lat')
        lng = data.get('lng')

        if not all([tip, obj_id, lat is not None, lng is not None]):
            return jsonify({'error': 'Eksik parametre'}), 400

        if tip == 'ortak':
            kayit = db.session.get(Ortak, obj_id)
        elif tip == 'firma':
            kayit = db.session.get(Firma, obj_id)
        else:
            return jsonify({'error': 'Geçersiz tip'}), 400

        if not kayit:
            return jsonify({'error': 'Kayıt bulunamadı'}), 404

        kayit.harita_enlem = float(lat)
        kayit.harita_boylam = float(lng)
        db.session.commit()

        logger.info(f"Koordinat güncellendi: {tip} #{obj_id} → ({lat}, {lng})")
        return jsonify({
            'success': True,
            'message': f'{tip.capitalize()} koordinatı güncellendi'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Koordinat güncelleme hatası: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ────────────────────────────────────────────────────────────
# API: Toplu Koordinat Atama
# ────────────────────────────────────────────────────────────
@site_harita_bp.route('/api/toplu-koordinat', methods=['POST'])
@login_required
def api_toplu_koordinat():
    """
    Koordinatsız ortaklara / firmalara otomatik koordinat atar.
    Blok bazlı grid yerleşim algoritması kullanır.

    Body:
        {
            "merkez_lat": 41.0082,
            "merkez_lng": 28.9784,
            "tip": "ortak" | "firma" | "hepsi"
        }
    """
    if not current_user.yonetici_mi():
        return jsonify({'error': 'Yetki yok'}), 403

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Geçersiz veri'}), 400

        merkez_lat = float(data.get('merkez_lat', 41.0082))
        merkez_lng = float(data.get('merkez_lng', 28.9784))
        tip = data.get('tip', 'hepsi')

        guncellenen = 0
        blok_offset = {}

        if tip in ('ortak', 'hepsi'):
            eksik_ortaklar = Ortak.query.filter(
                Ortak.aktif == True,
                or_(Ortak.harita_enlem.is_(None), Ortak.harita_boylam.is_(None))
            ).all()

            for o in eksik_ortaklar:
                blok = o.blok or 'bilinmeyen'
                if blok not in blok_offset:
                    blok_offset[blok] = 0
                offset = blok_offset[blok]

                # Izgara mantığıyla blok bazlı yerleşim
                row = offset // 10
                col = offset % 10
                o.harita_enlem = merkez_lat + (row * 0.0003) + (hash(blok) % 100) * 0.00005
                o.harita_boylam = merkez_lng + (col * 0.0003) + (hash(blok) % 100) * 0.00005
                blok_offset[blok] = offset + 1
                guncellenen += 1

        if tip in ('firma', 'hepsi'):
            eksik_firmalar = Firma.query.filter(
                Firma.aktif == True,
                or_(Firma.harita_enlem.is_(None), Firma.harita_boylam.is_(None))
            ).all()

            for f in eksik_firmalar:
                blok = f.blok or 'bilinmeyen'
                if blok not in blok_offset:
                    blok_offset[blok] = 0
                offset = blok_offset[blok]

                row = offset // 10
                col = offset % 10
                f.harita_enlem = merkez_lat + 0.002 + (row * 0.0003) + (hash(blok) % 100) * 0.00005
                f.harita_boylam = merkez_lng + 0.002 + (col * 0.0003) + (hash(blok) % 100) * 0.00005
                blok_offset[blok] = offset + 1
                guncellenen += 1

        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'{guncellenen} kayıta koordinat atandı',
            'guncellenen': guncellenen,
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Toplu koordinat hatası: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ────────────────────────────────────────────────────────────
# Yardımcı Fonksiyonlar
# ────────────────────────────────────────────────────────────
def _hesapla_renk_kodu(sozlesmeler, bugun):
    """
    Sözleşme durumuna göre marker renk kodu belirler.

    Returns:
        'green' — Tüm sözleşmeler aktif
        'yellow' — En az bir sözleşme 30 gün içinde sona erecek
        'red' — En az bir sözleşme sona ermiş veya süresi dolmuş
        'gray' — Sözleşme yok
    """
    if not sozlesmeler:
        return 'gray'

    herhangi_suresi_dolmus = False
    herhangi_sona_eriyor = False
    herhangi_aktif = False

    for s in sozlesmeler:
        if s['durum'] == 'sona_erdi' or s['durum'] == 'iptal':
            herhangi_suresi_dolmus = True
        elif s['kalan_gun'] is not None and s['kalan_gun'] <= 0:
            herhangi_suresi_dolmus = True
        elif s['kalan_gun'] is not None and s['kalan_gun'] <= 30:
            herhangi_sona_eriyor = True
        elif s['durum'] == 'aktif':
            herhangi_aktif = True

    if herhangi_suresi_dolmus:
        return 'red'
    if herhangi_sona_eriyor:
        return 'yellow'
    if herhangi_aktif:
        return 'green'
    return 'gray'
