"""
FDYS — REST API v1 Katmanı
Faz 8 — JWT Kimlik Doğrulama + CRUD Endpoint'ler

Özellikler:
    - JWT (JSON Web Token) kimlik doğrulama
    - Tüm modüller için CRUD endpoint'ler
    - Sayfalama, filtreleme, sıralama (query params)
    - Rate limiting
    - Tutarlı JSON yanıt formatı
    - Swagger/OpenAPI uyumlu endpoint yapısı

Kullanım:
    1. Token alma:
       POST /api/v1/auth/login
       Body: {"kullanici_adi": "admin", "sifre": "..."}
       → {"access_token": "eyJ...", "refresh_token": "eyJ..."}

    2. Korumalı endpoint'e erişim:
       GET /api/v1/ortaklar
       Header: Authorization: Bearer <access_token>

    3. Token yenileme:
       POST /api/v1/auth/refresh
       Header: Authorization: Bearer <refresh_token>
"""

import logging
from datetime import datetime, timezone, date
from functools import wraps

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)

from app.extensions import db, csrf, limiter
from app.models.kullanici import Kullanici
from app.models.crm import Ortak, Firma, FirmaYetkilisi
from app.models.sozlesme import Sozlesme
from app.models.talep import Talep, TalepGecmisi
from app.models.personel import Calisan
from app.models.makine import Makine
from app.models.stok import Malzeme
from app.models.is_emri import IsEmri
from app.models.duyuru import Duyuru

logger = logging.getLogger(__name__)

api_v1_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# CSRF muafiyeti — REST API token tabanlı koruma kullanır
csrf.exempt(api_v1_bp)


# ══════════════════════════════════════════════════════════════
# Yardımcı Fonksiyonlar
# ══════════════════════════════════════════════════════════════

def api_yanit(data=None, mesaj=None, durum=200, meta=None):
    """
    Tutarlı API yanıt formatı.

    {
        "success": true,
        "message": "...",
        "data": {...},
        "meta": {"sayfa": 1, "toplam": 100, ...}
    }
    """
    yanit = {
        'success': durum < 400,
        'message': mesaj,
        'data': data,
    }
    if meta:
        yanit['meta'] = meta
    return jsonify(yanit), durum


def sayfalama_parametreleri():
    """
    Query string'den sayfalama, sıralama, arama parametrelerini okur.

    Query Params:
        sayfa (int): Sayfa numarası (default: 1)
        adet (int): Sayfa başına kayıt (default: 20, max: 100)
        siralama (str): Sıralama alanı (default: 'id')
        yon (str): Sıralama yönü ('asc' | 'desc', default: 'desc')
        arama (str): Arama metni (opsiyonel)
    """
    sayfa = max(1, request.args.get('sayfa', 1, type=int))
    adet = min(100, max(1, request.args.get('adet', 20, type=int)))
    siralama = request.args.get('siralama', 'id')
    yon = request.args.get('yon', 'desc').lower()
    arama = request.args.get('arama', '').strip()

    if yon not in ('asc', 'desc'):
        yon = 'desc'

    return sayfa, adet, siralama, yon, arama


def uygula_sayfalama(query, model, sayfa, adet, siralama, yon):
    """
    Sorguya sayfalama ve sıralama uygular.

    Returns:
        (sonuclar, meta_bilgi)
    """
    # Sıralama alanını doğrula
    if hasattr(model, siralama):
        siralama_kolonu = getattr(model, siralama)
    else:
        siralama_kolonu = model.id

    if yon == 'asc':
        query = query.order_by(siralama_kolonu.asc())
    else:
        query = query.order_by(siralama_kolonu.desc())

    # Toplam kayıt
    toplam = query.count()

    # Sayfalama
    sonuclar = query.offset((sayfa - 1) * adet).limit(adet).all()

    meta = {
        'sayfa': sayfa,
        'adet': adet,
        'toplam': toplam,
        'toplam_sayfa': (toplam + adet - 1) // adet if toplam > 0 else 0,
        'siralama': siralama,
        'yon': yon,
    }

    return sonuclar, meta


def api_yetki_kontrol(modul_adi, izin_turu=None):
    """JWT kimliğindeki kullanıcının modül erişimini kontrol eder."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            kullanici_id = get_jwt_identity()
            kullanici = db.session.get(Kullanici, kullanici_id)
            if not kullanici:
                return api_yanit(mesaj='Kullanıcı bulunamadı', durum=401)
            if not kullanici.aktif:
                return api_yanit(mesaj='Hesap deaktif edilmiş', durum=403)
            if not kullanici.modul_erisim_var_mi(modul_adi, izin_turu):
                return api_yanit(mesaj='Bu modüle erişim yetkiniz yok', durum=403)
            return f(*args, **kwargs)
        return wrapper
    return decorator


# ══════════════════════════════════════════════════════════════
# AUTH — Kimlik Doğrulama
# ══════════════════════════════════════════════════════════════

@api_v1_bp.route('/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def auth_login():
    """
    JWT access + refresh token döner.

    Body:
        {"kullanici_adi": "admin", "sifre": "Admin123!"}

    Response:
        {
            "success": true,
            "data": {
                "access_token": "eyJ...",
                "refresh_token": "eyJ...",
                "kullanici": {
                    "id": 1,
                    "ad_soyad": "Admin",
                    "rol": "yonetici"
                }
            }
        }
    """
    data = request.get_json()
    if not data:
        return api_yanit(mesaj='JSON body gerekli', durum=400)

    kullanici_adi = data.get('kullanici_adi', '').strip()
    sifre = data.get('sifre', '')

    if not kullanici_adi or not sifre:
        return api_yanit(mesaj='Kullanıcı adı ve şifre gerekli', durum=400)

    kullanici = Kullanici.query.filter_by(kullanici_adi=kullanici_adi).first()

    if not kullanici or not kullanici.sifre_dogrula(sifre):
        return api_yanit(mesaj='Geçersiz kullanıcı adı veya şifre', durum=401)

    if not kullanici.aktif:
        return api_yanit(mesaj='Hesap deaktif edilmiş', durum=403)

    if kullanici.hesap_kilitli:
        return api_yanit(mesaj='Hesap kilitlenmiş. Yöneticiye başvurun.', durum=403)

    # Token oluştur
    access_token = create_access_token(
        identity=kullanici.id,
        additional_claims={
            'rol': kullanici.rol,
            'ad_soyad': kullanici.ad_soyad,
        }
    )
    refresh_token = create_refresh_token(identity=kullanici.id)

    # Giriş kaydı
    kullanici.giris_basarili()
    db.session.commit()

    logger.info(f"API login başarılı: {kullanici.kullanici_adi}")

    return api_yanit(
        data={
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'kullanici': {
                'id': kullanici.id,
                'ad_soyad': kullanici.ad_soyad,
                'kullanici_adi': kullanici.kullanici_adi,
                'rol': kullanici.rol,
                'rol_adi': kullanici.rol_adi,
            }
        },
        mesaj='Giriş başarılı'
    )


@api_v1_bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def auth_refresh():
    """Refresh token ile yeni access token alır."""
    kullanici_id = get_jwt_identity()
    kullanici = db.session.get(Kullanici, kullanici_id)

    if not kullanici or not kullanici.aktif:
        return api_yanit(mesaj='Geçersiz kullanıcı', durum=401)

    access_token = create_access_token(
        identity=kullanici.id,
        additional_claims={
            'rol': kullanici.rol,
            'ad_soyad': kullanici.ad_soyad,
        }
    )

    return api_yanit(
        data={'access_token': access_token, 'token_type': 'Bearer'},
        mesaj='Token yenilendi'
    )


@api_v1_bp.route('/auth/me', methods=['GET'])
@jwt_required()
def auth_me():
    """Mevcut kullanıcı bilgilerini döner."""
    kullanici_id = get_jwt_identity()
    kullanici = db.session.get(Kullanici, kullanici_id)

    if not kullanici:
        return api_yanit(mesaj='Kullanıcı bulunamadı', durum=404)

    return api_yanit(data={
        'id': kullanici.id,
        'ad_soyad': kullanici.ad_soyad,
        'kullanici_adi': kullanici.kullanici_adi,
        'rol': kullanici.rol,
        'rol_adi': kullanici.rol_adi,
        'departman': kullanici.departman,
        'modul_erisim': kullanici.modul_erisim,
        'aktif': kullanici.aktif,
        'son_giris': kullanici.son_giris.isoformat() if kullanici.son_giris else None,
    })


# ══════════════════════════════════════════════════════════════
# ORTAKLAR — CRM Ortak CRUD
# ══════════════════════════════════════════════════════════════

@api_v1_bp.route('/ortaklar', methods=['GET'])
@jwt_required()
@api_yetki_kontrol('crm')
@limiter.limit("60 per minute")
def ortaklar_listele():
    """
    Ortak listesi (sayfalama + filtreleme + arama).

    Query Params:
        sayfa, adet, siralama, yon, arama
        durum: aktif | pasif | cikis_yapti
        blok: Blok filtresi
        ortak_tipi: malik | kiraci | yetkili | vekil
    """
    sayfa, adet, siralama, yon, arama = sayfalama_parametreleri()

    query = Ortak.query.filter_by(aktif=True)

    # Filtreler
    durum = request.args.get('durum')
    if durum:
        query = query.filter_by(durum=durum)

    blok = request.args.get('blok')
    if blok:
        query = query.filter_by(blok=blok)

    ortak_tipi = request.args.get('ortak_tipi')
    if ortak_tipi:
        query = query.filter_by(ortak_tipi=ortak_tipi)

    # Arama
    if arama:
        query = query.filter(
            db.or_(
                Ortak.ad_soyad.ilike(f'%{arama}%'),
                Ortak.ortak_no.ilike(f'%{arama}%'),
                Ortak.tc_kimlik.ilike(f'%{arama}%'),
                Ortak.telefon.ilike(f'%{arama}%'),
                Ortak.blok.ilike(f'%{arama}%'),
            )
        )

    sonuclar, meta = uygula_sayfalama(query, Ortak, sayfa, adet, siralama, yon)

    return api_yanit(
        data=[_ortak_to_dict(o) for o in sonuclar],
        meta=meta
    )


@api_v1_bp.route('/ortaklar/<int:ortak_id>', methods=['GET'])
@jwt_required()
@api_yetki_kontrol('crm')
def ortak_detay(ortak_id):
    """Ortak detay bilgisi."""
    ortak = db.session.get(Ortak, ortak_id)
    if not ortak or not ortak.aktif:
        return api_yanit(mesaj='Ortak bulunamadı', durum=404)

    return api_yanit(data=_ortak_to_dict(ortak, detayli=True))


@api_v1_bp.route('/ortaklar', methods=['POST'])
@jwt_required()
@api_yetki_kontrol('crm', 'yazma')
def ortak_ekle():
    """Yeni ortak oluşturma."""
    data = request.get_json()
    if not data:
        return api_yanit(mesaj='JSON body gerekli', durum=400)

    # Zorunlu alanlar
    ad_soyad = data.get('ad_soyad', '').strip()
    ortak_no = data.get('ortak_no', '').strip()

    if not ad_soyad or not ortak_no:
        return api_yanit(mesaj='ad_soyad ve ortak_no zorunludur', durum=400)

    # Unique kontrol
    if Ortak.query.filter_by(ortak_no=ortak_no).first():
        return api_yanit(mesaj='Bu ortak numarası zaten kullanımda', durum=409)

    try:
        ortak = Ortak(
            ortak_no=ortak_no,
            ad_soyad=ad_soyad,
            tc_kimlik=data.get('tc_kimlik'),
            telefon=data.get('telefon'),
            telefon2=data.get('telefon2'),
            eposta=data.get('eposta'),
            adres=data.get('adres'),
            blok=data.get('blok'),
            daire_no=data.get('daire_no'),
            ortak_tipi=data.get('ortak_tipi', 'malik'),
            hisse_orani=data.get('hisse_orani'),
            m2=data.get('m2'),
            milliyet=data.get('milliyet', 'T.C.'),
            durum=data.get('durum', 'aktif'),
            harita_enlem=data.get('harita_enlem'),
            harita_boylam=data.get('harita_boylam'),
            notlar=data.get('notlar'),
        )
        db.session.add(ortak)
        db.session.commit()

        return api_yanit(data=_ortak_to_dict(ortak), mesaj='Ortak oluşturuldu', durum=201)

    except Exception as e:
        db.session.rollback()
        logger.error(f"Ortak ekleme hatası: {e}", exc_info=True)
        return api_yanit(mesaj='Ortak oluşturulurken hata oluştu', durum=500)


@api_v1_bp.route('/ortaklar/<int:ortak_id>', methods=['PUT'])
@jwt_required()
@api_yetki_kontrol('crm', 'yazma')
def ortak_guncelle(ortak_id):
    """Ortak bilgilerini güncelleme."""
    ortak = db.session.get(Ortak, ortak_id)
    if not ortak or not ortak.aktif:
        return api_yanit(mesaj='Ortak bulunamadı', durum=404)

    data = request.get_json()
    if not data:
        return api_yanit(mesaj='JSON body gerekli', durum=400)

    try:
        guncellenebilir = [
            'ad_soyad', 'tc_kimlik', 'telefon', 'telefon2', 'eposta', 'adres',
            'blok', 'daire_no', 'ortak_tipi', 'hisse_orani', 'm2', 'milliyet',
            'durum', 'harita_enlem', 'harita_boylam', 'notlar'
        ]
        for alan in guncellenebilir:
            if alan in data:
                setattr(ortak, alan, data[alan])

        db.session.commit()
        return api_yanit(data=_ortak_to_dict(ortak), mesaj='Ortak güncellendi')

    except Exception as e:
        db.session.rollback()
        logger.error(f"Ortak güncelleme hatası: {e}", exc_info=True)
        return api_yanit(mesaj='Güncelleme sırasında hata oluştu', durum=500)


@api_v1_bp.route('/ortaklar/<int:ortak_id>', methods=['DELETE'])
@jwt_required()
@api_yetki_kontrol('crm', 'silme')
def ortak_sil(ortak_id):
    """Ortak soft-delete."""
    ortak = db.session.get(Ortak, ortak_id)
    if not ortak:
        return api_yanit(mesaj='Ortak bulunamadı', durum=404)

    try:
        ortak.aktif = False
        db.session.commit()
        return api_yanit(mesaj='Ortak silindi (soft-delete)')
    except Exception as e:
        db.session.rollback()
        return api_yanit(mesaj='Silme hatası', durum=500)


# ══════════════════════════════════════════════════════════════
# FİRMALAR — CRM Firma CRUD
# ══════════════════════════════════════════════════════════════

@api_v1_bp.route('/firmalar', methods=['GET'])
@jwt_required()
@api_yetki_kontrol('crm')
@limiter.limit("60 per minute")
def firmalar_listele():
    """Firma listesi (sayfalama + filtreleme + arama)."""
    sayfa, adet, siralama, yon, arama = sayfalama_parametreleri()

    query = Firma.query.filter_by(aktif=True)

    durum = request.args.get('durum')
    if durum:
        query = query.filter_by(durum=durum)

    blok = request.args.get('blok')
    if blok:
        query = query.filter_by(blok=blok)

    sektor = request.args.get('sektor')
    if sektor:
        query = query.filter_by(sektor=sektor)

    if arama:
        query = query.filter(
            db.or_(
                Firma.unvan.ilike(f'%{arama}%'),
                Firma.firma_no.ilike(f'%{arama}%'),
                Firma.vergi_no.ilike(f'%{arama}%'),
                Firma.yetkili_kisi.ilike(f'%{arama}%'),
                Firma.telefon.ilike(f'%{arama}%'),
            )
        )

    sonuclar, meta = uygula_sayfalama(query, Firma, sayfa, adet, siralama, yon)

    return api_yanit(
        data=[_firma_to_dict(f) for f in sonuclar],
        meta=meta
    )


@api_v1_bp.route('/firmalar/<int:firma_id>', methods=['GET'])
@jwt_required()
@api_yetki_kontrol('crm')
def firma_detay(firma_id):
    """Firma detay bilgisi (yetkilileri dahil)."""
    firma = db.session.get(Firma, firma_id)
    if not firma or not firma.aktif:
        return api_yanit(mesaj='Firma bulunamadı', durum=404)

    return api_yanit(data=_firma_to_dict(firma, detayli=True))


@api_v1_bp.route('/firmalar', methods=['POST'])
@jwt_required()
@api_yetki_kontrol('crm', 'yazma')
def firma_ekle():
    """Yeni firma oluşturma."""
    data = request.get_json()
    if not data:
        return api_yanit(mesaj='JSON body gerekli', durum=400)

    unvan = data.get('unvan', '').strip()
    firma_no = data.get('firma_no', '').strip()

    if not unvan or not firma_no:
        return api_yanit(mesaj='unvan ve firma_no zorunludur', durum=400)

    if Firma.query.filter_by(firma_no=firma_no).first():
        return api_yanit(mesaj='Bu firma numarası zaten kullanımda', durum=409)

    try:
        firma = Firma(
            firma_no=firma_no,
            unvan=unvan,
            vergi_no=data.get('vergi_no'),
            vergi_dairesi=data.get('vergi_dairesi'),
            sektor=data.get('sektor', 'diger'),
            faaliyet_alani=data.get('faaliyet_alani'),
            yetkili_kisi=data.get('yetkili_kisi'),
            telefon=data.get('telefon'),
            eposta=data.get('eposta'),
            web_sitesi=data.get('web_sitesi'),
            adres=data.get('adres'),
            blok=data.get('blok'),
            daire_no=data.get('daire_no'),
            m2=data.get('m2'),
            calisan_sayisi=data.get('calisan_sayisi'),
            durum=data.get('durum', 'aktif'),
            harita_enlem=data.get('harita_enlem'),
            harita_boylam=data.get('harita_boylam'),
            notlar=data.get('notlar'),
        )
        db.session.add(firma)
        db.session.commit()

        return api_yanit(data=_firma_to_dict(firma), mesaj='Firma oluşturuldu', durum=201)

    except Exception as e:
        db.session.rollback()
        logger.error(f"Firma ekleme hatası: {e}", exc_info=True)
        return api_yanit(mesaj='Firma oluşturulurken hata oluştu', durum=500)


@api_v1_bp.route('/firmalar/<int:firma_id>', methods=['PUT'])
@jwt_required()
@api_yetki_kontrol('crm', 'yazma')
def firma_guncelle(firma_id):
    """Firma bilgilerini güncelleme."""
    firma = db.session.get(Firma, firma_id)
    if not firma or not firma.aktif:
        return api_yanit(mesaj='Firma bulunamadı', durum=404)

    data = request.get_json()
    if not data:
        return api_yanit(mesaj='JSON body gerekli', durum=400)

    try:
        guncellenebilir = [
            'unvan', 'vergi_no', 'vergi_dairesi', 'sektor', 'faaliyet_alani',
            'yetkili_kisi', 'telefon', 'eposta', 'web_sitesi', 'adres',
            'blok', 'daire_no', 'm2', 'calisan_sayisi', 'durum',
            'harita_enlem', 'harita_boylam', 'notlar'
        ]
        for alan in guncellenebilir:
            if alan in data:
                setattr(firma, alan, data[alan])

        db.session.commit()
        return api_yanit(data=_firma_to_dict(firma), mesaj='Firma güncellendi')

    except Exception as e:
        db.session.rollback()
        logger.error(f"Firma güncelleme hatası: {e}", exc_info=True)
        return api_yanit(mesaj='Güncelleme hatası', durum=500)


@api_v1_bp.route('/firmalar/<int:firma_id>', methods=['DELETE'])
@jwt_required()
@api_yetki_kontrol('crm', 'silme')
def firma_sil(firma_id):
    """Firma soft-delete."""
    firma = db.session.get(Firma, firma_id)
    if not firma:
        return api_yanit(mesaj='Firma bulunamadı', durum=404)

    try:
        firma.aktif = False
        db.session.commit()
        return api_yanit(mesaj='Firma silindi (soft-delete)')
    except Exception as e:
        db.session.rollback()
        return api_yanit(mesaj='Silme hatası', durum=500)


# ══════════════════════════════════════════════════════════════
# SÖZLEŞMELER — Sözleşme CRUD
# ══════════════════════════════════════════════════════════════

@api_v1_bp.route('/sozlesmeler', methods=['GET'])
@jwt_required()
@api_yetki_kontrol('sozlesme')
@limiter.limit("60 per minute")
def sozlesmeler_listele():
    """Sözleşme listesi."""
    sayfa, adet, siralama, yon, arama = sayfalama_parametreleri()

    query = Sozlesme.query.filter_by(aktif=True)

    durum = request.args.get('durum')
    if durum:
        query = query.filter_by(durum=durum)

    tur = request.args.get('tur')
    if tur:
        query = query.filter_by(tur=tur)

    taraf_tip = request.args.get('taraf_tip')
    if taraf_tip:
        query = query.filter_by(taraf_tip=taraf_tip)

    if arama:
        query = query.filter(
            db.or_(
                Sozlesme.baslik.ilike(f'%{arama}%'),
                Sozlesme.sozlesme_no.ilike(f'%{arama}%'),
            )
        )

    sonuclar, meta = uygula_sayfalama(query, Sozlesme, sayfa, adet, siralama, yon)

    return api_yanit(
        data=[_sozlesme_to_dict(s) for s in sonuclar],
        meta=meta
    )


@api_v1_bp.route('/sozlesmeler/<int:sozlesme_id>', methods=['GET'])
@jwt_required()
@api_yetki_kontrol('sozlesme')
def sozlesme_detay(sozlesme_id):
    """Sözleşme detay bilgisi."""
    sozlesme = db.session.get(Sozlesme, sozlesme_id)
    if not sozlesme or not sozlesme.aktif:
        return api_yanit(mesaj='Sözleşme bulunamadı', durum=404)

    return api_yanit(data=_sozlesme_to_dict(sozlesme, detayli=True))


# ══════════════════════════════════════════════════════════════
# TALEPLER — Talep CRUD
# ══════════════════════════════════════════════════════════════

@api_v1_bp.route('/talepler', methods=['GET'])
@jwt_required()
@api_yetki_kontrol('talep')
@limiter.limit("60 per minute")
def talepler_listele():
    """Talep listesi."""
    sayfa, adet, siralama, yon, arama = sayfalama_parametreleri()

    query = Talep.query.filter_by(aktif=True)

    durum = request.args.get('durum')
    if durum:
        query = query.filter_by(durum=durum)

    kategori = request.args.get('kategori')
    if kategori:
        query = query.filter_by(kategori=kategori)

    oncelik = request.args.get('oncelik')
    if oncelik:
        query = query.filter_by(oncelik=oncelik)

    if arama:
        query = query.filter(
            db.or_(
                Talep.baslik.ilike(f'%{arama}%'),
                Talep.talep_no.ilike(f'%{arama}%'),
                Talep.talep_eden_adi.ilike(f'%{arama}%'),
            )
        )

    sonuclar, meta = uygula_sayfalama(query, Talep, sayfa, adet, siralama, yon)

    return api_yanit(
        data=[_talep_to_dict(t) for t in sonuclar],
        meta=meta
    )


@api_v1_bp.route('/talepler/<int:talep_id>', methods=['GET'])
@jwt_required()
@api_yetki_kontrol('talep')
def talep_detay(talep_id):
    """Talep detay bilgisi (geçmiş dahil)."""
    talep = db.session.get(Talep, talep_id)
    if not talep or not talep.aktif:
        return api_yanit(mesaj='Talep bulunamadı', durum=404)

    return api_yanit(data=_talep_to_dict(talep, detayli=True))


@api_v1_bp.route('/talepler', methods=['POST'])
@jwt_required()
@api_yetki_kontrol('talep', 'yazma')
def talep_ekle():
    """Yeni talep oluşturma."""
    data = request.get_json()
    if not data:
        return api_yanit(mesaj='JSON body gerekli', durum=400)

    baslik = data.get('baslik', '').strip()
    if not baslik:
        return api_yanit(mesaj='baslik zorunludur', durum=400)

    try:
        kullanici_id = get_jwt_identity()
        kullanici = db.session.get(Kullanici, kullanici_id)

        # Otomatik talep no
        son_talep = Talep.query.order_by(Talep.id.desc()).first()
        yil = datetime.now().year
        sira = (son_talep.id + 1) if son_talep else 1
        talep_no = f'TLP-{yil}-{sira:05d}'

        talep = Talep(
            talep_no=talep_no,
            talep_eden_tip='dahili',
            talep_eden_id=kullanici_id,
            talep_eden_adi=kullanici.ad_soyad if kullanici else 'API Kullanıcı',
            kategori=data.get('kategori', 'diger'),
            alt_kategori=data.get('alt_kategori'),
            baslik=baslik,
            aciklama=data.get('aciklama'),
            oncelik=data.get('oncelik', 'normal'),
            konum_bilgi=data.get('konum_bilgi'),
            sms_bildirim=data.get('sms_bildirim', False),
            eposta_bildirim=data.get('eposta_bildirim', True),
        )
        db.session.add(talep)

        # Geçmiş kaydı
        gecmis = TalepGecmisi(
            talep=talep,
            islem_turu='olusturma',
            yapan_id=kullanici_id,
            yapan_adi=kullanici.ad_soyad if kullanici else 'API',
            aciklama='API üzerinden talep oluşturuldu',
            yeni_durum='acik',
        )
        db.session.add(gecmis)
        db.session.commit()

        return api_yanit(data=_talep_to_dict(talep), mesaj='Talep oluşturuldu', durum=201)

    except Exception as e:
        db.session.rollback()
        logger.error(f"Talep ekleme hatası: {e}", exc_info=True)
        return api_yanit(mesaj='Talep oluşturulurken hata oluştu', durum=500)


# ══════════════════════════════════════════════════════════════
# PERSONEL — Personel (Salt Okunur)
# ══════════════════════════════════════════════════════════════

@api_v1_bp.route('/personel', methods=['GET'])
@jwt_required()
@api_yetki_kontrol('personel')
@limiter.limit("60 per minute")
def personel_listele():
    """Çalışan listesi."""
    sayfa, adet, siralama, yon, arama = sayfalama_parametreleri()

    query = Calisan.query.filter_by(aktif=True)

    if arama:
        query = query.filter(
            db.or_(
                Calisan.ad_soyad.ilike(f'%{arama}%'),
                Calisan.sicil_no.ilike(f'%{arama}%'),
                Calisan.departman.ilike(f'%{arama}%'),
            )
        )

    sonuclar, meta = uygula_sayfalama(query, Calisan, sayfa, adet, siralama, yon)

    return api_yanit(
        data=[{
            'id': c.id,
            'sicil_no': c.sicil_no,
            'ad_soyad': c.ad_soyad,
            'departman': c.departman,
            'pozisyon': c.pozisyon,
            'ise_baslama': c.ise_baslama_tarihi.isoformat() if c.ise_baslama_tarihi else None,
            'durum': c.durum if hasattr(c, 'durum') else 'aktif',
        } for c in sonuclar],
        meta=meta
    )


# ══════════════════════════════════════════════════════════════
# MAKİNELER — Makine (Salt Okunur)
# ══════════════════════════════════════════════════════════════

@api_v1_bp.route('/makineler', methods=['GET'])
@jwt_required()
@api_yetki_kontrol('makine')
@limiter.limit("60 per minute")
def makineler_listele():
    """Makine listesi."""
    sayfa, adet, siralama, yon, arama = sayfalama_parametreleri()

    query = Makine.query.filter_by(aktif=True)

    durum = request.args.get('durum')
    if durum:
        query = query.filter_by(durum=durum)

    if arama:
        query = query.filter(
            db.or_(
                Makine.ad.ilike(f'%{arama}%'),
                Makine.kod.ilike(f'%{arama}%'),
                Makine.lokasyon.ilike(f'%{arama}%'),
            )
        )

    sonuclar, meta = uygula_sayfalama(query, Makine, sayfa, adet, siralama, yon)

    return api_yanit(
        data=[{
            'id': m.id,
            'ad': m.ad,
            'kod': m.kod,
            'durum': m.durum,
            'lokasyon': m.lokasyon,
            'marka': m.marka if hasattr(m, 'marka') else None,
            'model': m.model if hasattr(m, 'model') else None,
        } for m in sonuclar],
        meta=meta
    )


# ══════════════════════════════════════════════════════════════
# STOK — Malzeme (Salt Okunur)
# ══════════════════════════════════════════════════════════════

@api_v1_bp.route('/malzemeler', methods=['GET'])
@jwt_required()
@api_yetki_kontrol('stok')
@limiter.limit("60 per minute")
def malzemeler_listele():
    """Malzeme/stok listesi."""
    sayfa, adet, siralama, yon, arama = sayfalama_parametreleri()

    query = Malzeme.query.filter_by(aktif=True)

    if arama:
        query = query.filter(
            db.or_(
                Malzeme.ad.ilike(f'%{arama}%'),
                Malzeme.kod.ilike(f'%{arama}%'),
            )
        )

    sonuclar, meta = uygula_sayfalama(query, Malzeme, sayfa, adet, siralama, yon)

    return api_yanit(
        data=[{
            'id': m.id,
            'ad': m.ad,
            'kod': m.kod,
            'miktar': float(m.miktar) if m.miktar else 0,
            'birim': m.birim,
            'kategori': m.kategori,
            'min_stok': float(m.min_stok) if m.min_stok else 0,
        } for m in sonuclar],
        meta=meta
    )


# ══════════════════════════════════════════════════════════════
# İŞ EMİRLERİ — İş Emri (Salt Okunur)
# ══════════════════════════════════════════════════════════════

@api_v1_bp.route('/is-emirleri', methods=['GET'])
@jwt_required()
@api_yetki_kontrol('makine')
@limiter.limit("60 per minute")
def is_emirleri_listele():
    """İş emri listesi."""
    sayfa, adet, siralama, yon, arama = sayfalama_parametreleri()

    query = IsEmri.query.filter_by(aktif=True)

    durum = request.args.get('durum')
    if durum:
        query = query.filter_by(durum=durum)

    if arama:
        query = query.filter(
            db.or_(
                IsEmri.baslik.ilike(f'%{arama}%'),
                IsEmri.is_emri_no.ilike(f'%{arama}%'),
            )
        )

    sonuclar, meta = uygula_sayfalama(query, IsEmri, sayfa, adet, siralama, yon)

    return api_yanit(
        data=[{
            'id': ie.id,
            'is_emri_no': ie.is_emri_no,
            'baslik': ie.baslik,
            'durum': ie.durum,
            'oncelik': ie.oncelik,
            'olusturma_tarihi': ie.olusturma_tarihi.isoformat() if ie.olusturma_tarihi else None,
        } for ie in sonuclar],
        meta=meta
    )


# ══════════════════════════════════════════════════════════════
# DUYURULAR — Duyuru (Salt Okunur)
# ══════════════════════════════════════════════════════════════

@api_v1_bp.route('/duyurular', methods=['GET'])
@jwt_required()
@api_yetki_kontrol('duyuru')
@limiter.limit("60 per minute")
def duyurular_listele():
    """Aktif duyuru listesi."""
    sayfa, adet, siralama, yon, arama = sayfalama_parametreleri()

    query = Duyuru.query.filter_by(aktif=True)

    if arama:
        query = query.filter(
            db.or_(
                Duyuru.baslik.ilike(f'%{arama}%'),
            )
        )

    sonuclar, meta = uygula_sayfalama(query, Duyuru, sayfa, adet, siralama, yon)

    return api_yanit(
        data=[{
            'id': d.id,
            'baslik': d.baslik,
            'icerik': d.icerik[:200] if d.icerik else None,
            'tur': d.tur,
            'oncelik': d.oncelik,
            'yayin_tarihi': d.yayin_tarihi.isoformat() if d.yayin_tarihi else None,
        } for d in sonuclar],
        meta=meta
    )


# ══════════════════════════════════════════════════════════════
# İSTATİSTİK — Dashboard Özet
# ══════════════════════════════════════════════════════════════

@api_v1_bp.route('/istatistik/ozet', methods=['GET'])
@jwt_required()
@limiter.limit("30 per minute")
def istatistik_ozet():
    """Genel sistem istatistik özeti."""
    try:
        bugun = date.today()

        data = {
            'ortaklar': {
                'toplam': Ortak.query.filter_by(aktif=True).count(),
                'aktif': Ortak.query.filter_by(aktif=True, durum='aktif').count(),
            },
            'firmalar': {
                'toplam': Firma.query.filter_by(aktif=True).count(),
                'aktif': Firma.query.filter_by(aktif=True, durum='aktif').count(),
            },
            'sozlesmeler': {
                'toplam': Sozlesme.query.filter_by(aktif=True).count(),
                'aktif': Sozlesme.query.filter_by(aktif=True, durum='aktif').count(),
            },
            'talepler': {
                'toplam': Talep.query.filter_by(aktif=True).count(),
                'acik': Talep.query.filter(Talep.aktif == True, Talep.durum.in_(['acik', 'yonlendirildi', 'devam'])).count(),
            },
            'personel': {
                'toplam': Calisan.query.filter_by(aktif=True).count(),
            },
            'makineler': {
                'toplam': Makine.query.filter_by(aktif=True).count(),
                'calisir': Makine.query.filter_by(aktif=True, durum='aktif').count(),
                'arizali': Makine.query.filter_by(aktif=True, durum='arizali').count(),
            },
        }

        return api_yanit(data=data, mesaj='Sistem özeti')

    except Exception as e:
        logger.error(f"İstatistik hatası: {e}", exc_info=True)
        return api_yanit(mesaj='İstatistik alınamadı', durum=500)


# ══════════════════════════════════════════════════════════════
# API BİLGİ — Sürüm ve Endpoint Listesi
# ══════════════════════════════════════════════════════════════

@api_v1_bp.route('/', methods=['GET'])
def api_bilgi():
    """API sürüm ve endpoint bilgisi (herkese açık)."""
    return api_yanit(data={
        'api': 'FDYS REST API',
        'versiyon': 'v1.0.0',
        'dokumantasyon': '/api/v1/endpoints',
        'auth': {
            'login': 'POST /api/v1/auth/login',
            'refresh': 'POST /api/v1/auth/refresh',
            'me': 'GET /api/v1/auth/me',
        },
        'endpoints': {
            'ortaklar': '/api/v1/ortaklar',
            'firmalar': '/api/v1/firmalar',
            'sozlesmeler': '/api/v1/sozlesmeler',
            'talepler': '/api/v1/talepler',
            'personel': '/api/v1/personel',
            'makineler': '/api/v1/makineler',
            'malzemeler': '/api/v1/malzemeler',
            'is_emirleri': '/api/v1/is-emirleri',
            'duyurular': '/api/v1/duyurular',
            'istatistik': '/api/v1/istatistik/ozet',
        },
        'sayfalama': {
            'parametreler': 'sayfa, adet, siralama, yon, arama',
            'varsayilan': {'sayfa': 1, 'adet': 20, 'max_adet': 100},
        },
    })


@api_v1_bp.route('/endpoints', methods=['GET'])
def api_endpoints():
    """Tüm endpoint'lerin detaylı listesi (Swagger benzeri)."""
    endpoints = [
        # Auth
        {'metod': 'POST', 'url': '/api/v1/auth/login', 'aciklama': 'JWT token alır', 'yetki': 'Herkese açık'},
        {'metod': 'POST', 'url': '/api/v1/auth/refresh', 'aciklama': 'Access token yeniler', 'yetki': 'Refresh token'},
        {'metod': 'GET', 'url': '/api/v1/auth/me', 'aciklama': 'Mevcut kullanıcı bilgisi', 'yetki': 'JWT'},

        # Ortaklar
        {'metod': 'GET', 'url': '/api/v1/ortaklar', 'aciklama': 'Ortak listesi', 'yetki': 'CRM okuma'},
        {'metod': 'GET', 'url': '/api/v1/ortaklar/{id}', 'aciklama': 'Ortak detay', 'yetki': 'CRM okuma'},
        {'metod': 'POST', 'url': '/api/v1/ortaklar', 'aciklama': 'Yeni ortak oluştur', 'yetki': 'CRM yazma'},
        {'metod': 'PUT', 'url': '/api/v1/ortaklar/{id}', 'aciklama': 'Ortak güncelle', 'yetki': 'CRM yazma'},
        {'metod': 'DELETE', 'url': '/api/v1/ortaklar/{id}', 'aciklama': 'Ortak sil', 'yetki': 'CRM silme'},

        # Firmalar
        {'metod': 'GET', 'url': '/api/v1/firmalar', 'aciklama': 'Firma listesi', 'yetki': 'CRM okuma'},
        {'metod': 'GET', 'url': '/api/v1/firmalar/{id}', 'aciklama': 'Firma detay', 'yetki': 'CRM okuma'},
        {'metod': 'POST', 'url': '/api/v1/firmalar', 'aciklama': 'Yeni firma oluştur', 'yetki': 'CRM yazma'},
        {'metod': 'PUT', 'url': '/api/v1/firmalar/{id}', 'aciklama': 'Firma güncelle', 'yetki': 'CRM yazma'},
        {'metod': 'DELETE', 'url': '/api/v1/firmalar/{id}', 'aciklama': 'Firma sil', 'yetki': 'CRM silme'},

        # Sözleşmeler
        {'metod': 'GET', 'url': '/api/v1/sozlesmeler', 'aciklama': 'Sözleşme listesi', 'yetki': 'Sözleşme okuma'},
        {'metod': 'GET', 'url': '/api/v1/sozlesmeler/{id}', 'aciklama': 'Sözleşme detay', 'yetki': 'Sözleşme okuma'},

        # Talepler
        {'metod': 'GET', 'url': '/api/v1/talepler', 'aciklama': 'Talep listesi', 'yetki': 'Talep okuma'},
        {'metod': 'GET', 'url': '/api/v1/talepler/{id}', 'aciklama': 'Talep detay', 'yetki': 'Talep okuma'},
        {'metod': 'POST', 'url': '/api/v1/talepler', 'aciklama': 'Yeni talep oluştur', 'yetki': 'Talep yazma'},

        # Diğer
        {'metod': 'GET', 'url': '/api/v1/personel', 'aciklama': 'Personel listesi', 'yetki': 'Personel okuma'},
        {'metod': 'GET', 'url': '/api/v1/makineler', 'aciklama': 'Makine listesi', 'yetki': 'Makine okuma'},
        {'metod': 'GET', 'url': '/api/v1/malzemeler', 'aciklama': 'Malzeme/stok listesi', 'yetki': 'Stok okuma'},
        {'metod': 'GET', 'url': '/api/v1/is-emirleri', 'aciklama': 'İş emri listesi', 'yetki': 'Makine okuma'},
        {'metod': 'GET', 'url': '/api/v1/duyurular', 'aciklama': 'Duyuru listesi', 'yetki': 'Duyuru okuma'},
        {'metod': 'GET', 'url': '/api/v1/istatistik/ozet', 'aciklama': 'Sistem özeti', 'yetki': 'JWT'},
    ]

    return api_yanit(data=endpoints, mesaj=f'Toplam {len(endpoints)} endpoint')


# ══════════════════════════════════════════════════════════════
# Serializer Yardımcıları
# ══════════════════════════════════════════════════════════════

def _ortak_to_dict(o, detayli=False):
    """Ortak nesnesini dict'e çevirir."""
    d = {
        'id': o.id,
        'ortak_no': o.ortak_no,
        'ad_soyad': o.ad_soyad,
        'telefon': o.telefon,
        'eposta': o.eposta,
        'blok': o.blok,
        'daire_no': o.daire_no,
        'ortak_tipi': o.ortak_tipi,
        'ortak_tipi_adi': o.ortak_tipi_adi,
        'durum': o.durum,
        'durum_adi': o.durum_adi,
        'konum': o.konum_bilgi,
        'harita_enlem': o.harita_enlem,
        'harita_boylam': o.harita_boylam,
    }
    if detayli:
        d.update({
            'tc_kimlik': o.tc_kimlik,
            'telefon2': o.telefon2,
            'adres': o.adres,
            'hisse_orani': float(o.hisse_orani) if o.hisse_orani else None,
            'm2': float(o.m2) if o.m2 else None,
            'milliyet': o.milliyet,
            'notlar': o.notlar,
            'olusturma_tarihi': o.olusturma_tarihi.isoformat() if o.olusturma_tarihi else None,
            'guncelleme_tarihi': o.guncelleme_tarihi.isoformat() if o.guncelleme_tarihi else None,
        })
    return d


def _firma_to_dict(f, detayli=False):
    """Firma nesnesini dict'e çevirir."""
    d = {
        'id': f.id,
        'firma_no': f.firma_no,
        'unvan': f.unvan,
        'telefon': f.telefon,
        'eposta': f.eposta,
        'sektor': f.sektor,
        'sektor_adi': f.sektor_adi,
        'blok': f.blok,
        'daire_no': f.daire_no,
        'durum': f.durum,
        'durum_adi': f.durum_adi,
        'konum': f.konum_bilgi,
        'harita_enlem': f.harita_enlem,
        'harita_boylam': f.harita_boylam,
    }
    if detayli:
        d.update({
            'vergi_no': f.vergi_no,
            'vergi_dairesi': f.vergi_dairesi,
            'faaliyet_alani': f.faaliyet_alani,
            'yetkili_kisi': f.yetkili_kisi,
            'web_sitesi': f.web_sitesi,
            'adres': f.adres,
            'm2': float(f.m2) if f.m2 else None,
            'calisan_sayisi': f.calisan_sayisi,
            'notlar': f.notlar,
            'olusturma_tarihi': f.olusturma_tarihi.isoformat() if f.olusturma_tarihi else None,
            'guncelleme_tarihi': f.guncelleme_tarihi.isoformat() if f.guncelleme_tarihi else None,
            'yetkililer': [{
                'id': y.id,
                'ad_soyad': y.ad_soyad,
                'gorev': y.gorev,
                'telefon': y.telefon,
                'eposta': y.eposta,
            } for y in f.yetkililer.filter_by(aktif=True).all()],
        })
    return d


def _sozlesme_to_dict(s, detayli=False):
    """Sözleşme nesnesini dict'e çevirir."""
    d = {
        'id': s.id,
        'sozlesme_no': s.sozlesme_no,
        'tur': s.tur,
        'tur_adi': s.tur_adi,
        'taraf_tip': s.taraf_tip,
        'taraf_bilgi': s.taraf_bilgi,
        'baslik': s.baslik,
        'baslangic_tarihi': s.baslangic_tarihi.isoformat() if s.baslangic_tarihi else None,
        'bitis_tarihi': s.bitis_tarihi.isoformat() if s.bitis_tarihi else None,
        'tutar': float(s.tutar) if s.tutar else None,
        'para_birimi': s.para_birimi,
        'durum': s.durum,
        'durum_adi': s.durum_adi,
        'kalan_gun': s.kalan_gun,
    }
    if detayli:
        d.update({
            'aciklama': s.aciklama,
            'odeme_periyodu': s.odeme_periyodu,
            'odeme_periyodu_adi': s.odeme_periyodu_adi,
            'otomatik_yenileme': s.otomatik_yenileme,
            'hatirlatma_gun': s.hatirlatma_gun,
            'notlar': s.notlar,
            'olusturma_tarihi': s.olusturma_tarihi.isoformat() if s.olusturma_tarihi else None,
        })
    return d


def _talep_to_dict(t, detayli=False):
    """Talep nesnesini dict'e çevirir."""
    d = {
        'id': t.id,
        'talep_no': t.talep_no,
        'baslik': t.baslik,
        'kategori': t.kategori,
        'kategori_adi': t.kategori_adi,
        'oncelik': t.oncelik,
        'oncelik_adi': t.oncelik_adi,
        'durum': t.durum,
        'durum_adi': t.durum_adi,
        'talep_eden_adi': t.talep_eden_adi,
        'konum_bilgi': t.konum_bilgi,
        'olusturma_tarihi': t.olusturma_tarihi.isoformat() if t.olusturma_tarihi else None,
        'gecen_sure': t.gecen_sure_str,
    }
    if detayli:
        d.update({
            'aciklama': t.aciklama,
            'talep_eden_tip': t.talep_eden_tip,
            'atanan_departman': t.atanan_departman,
            'cozum_notu': t.cozum_notu,
            'memnuniyet_puani': t.memnuniyet_puani,
            'kapanma_tarihi': t.kapanma_tarihi.isoformat() if t.kapanma_tarihi else None,
            'gecmis': [{
                'islem_turu': g.islem_turu,
                'islem_turu_adi': g.islem_turu_adi,
                'yapan_adi': g.yapan_adi,
                'aciklama': g.aciklama,
                'eski_durum': g.eski_durum,
                'yeni_durum': g.yeni_durum,
                'tarih': g.tarih.isoformat() if g.tarih else None,
            } for g in t.gecmis.limit(50).all()],
        })
    return d
