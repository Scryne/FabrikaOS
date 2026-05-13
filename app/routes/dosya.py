"""
FDYS — Dosya Yönetimi Rotaları
Faz 5 — Dosya Eki Sistemi

Her kayda dosya/fotoğraf ekleme, listeleme, indirme, silme.
AJAX destekli çoklu dosya yükleme.
"""

import os
import uuid
import logging
from flask import Blueprint, request, jsonify, send_file, current_app, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db, csrf
from app.models.dosya import DosyaEki
from app.utils.security import is_secure_image

logger = logging.getLogger(__name__)

dosya_bp = Blueprint('dosya', __name__, url_prefix='/dosya')

# Desteklenen uzantılar
IZIN_VERILEN_UZANTILAR = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv'}


def _uzanti_gecerli_mi(dosya_adi):
    """Dosya uzantısının geçerli olup olmadığını kontrol eder."""
    return '.' in dosya_adi and dosya_adi.rsplit('.', 1)[1].lower() in IZIN_VERILEN_UZANTILAR


def _guvenli_dosya_adi(dosya_adi):
    """UUID prefix ile benzersiz dosya adı oluşturur."""
    uzanti = dosya_adi.rsplit('.', 1)[1].lower() if '.' in dosya_adi else 'bin'
    return f"{uuid.uuid4().hex[:12]}_{secure_filename(dosya_adi)}"


@dosya_bp.route('/yukle', methods=['POST'])
@login_required
def yukle():
    """Dosya yükleme endpoint'i (AJAX, çoklu dosya desteği)."""
    kaynak_tablo = request.form.get('kaynak_tablo')
    kaynak_id = request.form.get('kaynak_id', type=int)
    aciklama = request.form.get('aciklama', '')

    if not kaynak_tablo or not kaynak_id:
        return jsonify({'success': False, 'error': 'Kaynak bilgisi eksik.'}), 400

    dosyalar = request.files.getlist('dosyalar')
    if not dosyalar or all(f.filename == '' for f in dosyalar):
        return jsonify({'success': False, 'error': 'Dosya seçilmedi.'}), 400

    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    if not upload_folder:
        return jsonify({'success': False, 'error': 'Yükleme klasörü yapılandırılmamış.'}), 500

    # Kaynak tablo alt klasörü
    hedef_klasor = os.path.join(upload_folder, kaynak_tablo)
    os.makedirs(hedef_klasor, exist_ok=True)

    yuklenen = []
    hatalar = []

    for dosya in dosyalar:
        if dosya.filename == '':
            continue

        if not _uzanti_gecerli_mi(dosya.filename):
            hatalar.append(f'{dosya.filename}: Desteklenmeyen dosya formatı.')
            continue

        # Resim dosyaları için güvenlik kontrolü
        uzanti = dosya.filename.rsplit('.', 1)[1].lower()
        if uzanti in {'jpg', 'jpeg', 'png', 'gif', 'webp'}:
            dosya.seek(0)
            if not is_secure_image(dosya, dosya.filename):
                hatalar.append(f'{dosya.filename}: Geçersiz resim dosyası.')
                continue
            dosya.seek(0)

        # Dosyayı kaydet
        guvenli_ad = _guvenli_dosya_adi(dosya.filename)
        dosya_yolu = os.path.join(hedef_klasor, guvenli_ad)

        try:
            dosya.save(dosya_yolu)
            dosya_boyutu = os.path.getsize(dosya_yolu)

            ek = DosyaEki(
                dosya_adi=f"{kaynak_tablo}/{guvenli_ad}",
                orijinal_adi=dosya.filename,
                dosya_tipi=DosyaEki.dosya_tipi_bul(dosya.filename),
                mime_type=dosya.content_type,
                dosya_boyutu=dosya_boyutu,
                kaynak_tablo=kaynak_tablo,
                kaynak_id=kaynak_id,
                yukleyen_id=current_user.id,
                aciklama=aciklama
            )
            db.session.add(ek)
            yuklenen.append({
                'orijinal_adi': dosya.filename,
                'boyut': ek.boyut_formatli,
                'tip': ek.dosya_tipi
            })
        except Exception as e:
            logger.error(f"Dosya yükleme hatası: {e}")
            hatalar.append(f'{dosya.filename}: Yükleme sırasında hata oluştu.')

    if yuklenen:
        db.session.commit()

    return jsonify({
        'success': len(yuklenen) > 0,
        'yuklenen': yuklenen,
        'yuklenen_sayisi': len(yuklenen),
        'hatalar': hatalar
    })


@dosya_bp.route('/listele/<kaynak_tablo>/<int:kaynak_id>')
@login_required
def listele(kaynak_tablo, kaynak_id):
    """Kayda bağlı dosyaları JSON olarak döner."""
    dosyalar = DosyaEki.query.filter_by(
        kaynak_tablo=kaynak_tablo,
        kaynak_id=kaynak_id,
        aktif=True
    ).order_by(DosyaEki.olusturma_tarihi.desc()).all()

    data = []
    for d in dosyalar:
        data.append({
            'id': d.id,
            'orijinal_adi': d.orijinal_adi,
            'dosya_tipi': d.dosya_tipi,
            'ikon': d.ikon_sinifi,
            'boyut': d.boyut_formatli,
            'resim_mi': d.resim_mi,
            'onizleme_url': url_for('dosya.onizle', id=d.id) if d.resim_mi else None,
            'indirme_url': url_for('dosya.indir', id=d.id),
            'yukleyen': d.yukleyen.ad_soyad if d.yukleyen else '—',
            'tarih': d.olusturma_tarihi.strftime('%d.%m.%Y %H:%M'),
            'aciklama': d.aciklama or ''
        })

    return jsonify({'dosyalar': data, 'toplam': len(data)})


@dosya_bp.route('/indir/<int:id>')
@login_required
def indir(id):
    """Dosyayı indirir."""
    dosya = DosyaEki.query.get_or_404(id)
    dosya_yolu = os.path.join(current_app.config['UPLOAD_FOLDER'], dosya.dosya_adi)

    if not os.path.exists(dosya_yolu):
        return jsonify({'success': False, 'error': 'Dosya bulunamadı.'}), 404

    return send_file(dosya_yolu, as_attachment=True, download_name=dosya.orijinal_adi)


@dosya_bp.route('/onizle/<int:id>')
@login_required
def onizle(id):
    """Dosya önizlemesi (resimler için)."""
    dosya = DosyaEki.query.get_or_404(id)
    dosya_yolu = os.path.join(current_app.config['UPLOAD_FOLDER'], dosya.dosya_adi)

    if not os.path.exists(dosya_yolu):
        return jsonify({'success': False, 'error': 'Dosya bulunamadı.'}), 404

    return send_file(dosya_yolu, mimetype=dosya.mime_type)


@dosya_bp.route('/sil/<int:id>', methods=['POST'])
@login_required
def sil(id):
    """Dosyayı siler (soft delete + fiziksel silme)."""
    dosya = DosyaEki.query.get_or_404(id)

    # Yetki kontrolü: Yükleyen veya yönetici silebilir
    if dosya.yukleyen_id != current_user.id and not current_user.yonetici_mi():
        return jsonify({'success': False, 'error': 'Bu dosyayı silme yetkiniz yok.'}), 403

    # Fiziksel dosyayı sil
    dosya_yolu = os.path.join(current_app.config['UPLOAD_FOLDER'], dosya.dosya_adi)
    if os.path.exists(dosya_yolu):
        try:
            os.remove(dosya_yolu)
        except Exception as e:
            logger.warning(f"Fiziksel dosya silme hatası: {e}")

    # DB'den sil
    db.session.delete(dosya)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Dosya başarıyla silindi.'})
