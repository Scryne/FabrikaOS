"""
FDYS — DYS (Doküman Yönetim Sistemi) Rotaları
Faz 6 — Merkezi Doküman Yönetimi

14 endpoint: Dashboard, liste, yükleme, detay, düzenleme,
yeni versiyon, indirme, önizleme, arama, onay, red,
silme, istatistik API, etiket API.
"""

import os
import logging
from datetime import datetime, timezone
from flask import (
    Blueprint, render_template, request, flash,
    redirect, url_for, send_file, jsonify, current_app
)
from flask_login import login_required, current_user
from sqlalchemy import func

from app.extensions import db
from app.utils.decorators import modul_erisim_gerekli, yazma_izni_gerekli, log_action
from app.models.dys import Dokuman
from app.forms.dys import (
    DokumanYukleForm, DokumanDuzenleForm,
    DokumanOnayForm, DokumanAramaForm
)
from app.services.dys_servisi import (
    dokuman_yukle, dokuman_yeni_versiyon,
    dokuman_ara, dokuman_istatistikler
)

logger = logging.getLogger(__name__)

dys_bp = Blueprint('dys', __name__, url_prefix='/dys')


# ══════════════════════════════════════════════════════════════════
# DYS ANA DASHBOARD
# ══════════════════════════════════════════════════════════════════

@dys_bp.route('/')
@login_required
@modul_erisim_gerekli('dys')
def index():
    """DYS ana panel — istatistikler ve son dokümanlar."""
    istatistikler = dokuman_istatistikler()

    return render_template('dys/index.html', **istatistikler)


# ══════════════════════════════════════════════════════════════════
# DOKÜMAN LİSTESİ
# ══════════════════════════════════════════════════════════════════

@dys_bp.route('/liste')
@login_required
@modul_erisim_gerekli('dys')
def liste():
    """Doküman listesi — filtreleme ve arama."""
    page = request.args.get('page', 1, type=int)
    kategori = request.args.get('kategori', '')
    departman = request.args.get('departman', '')
    onay_durumu = request.args.get('onay_durumu', '')
    arama = request.args.get('arama', '')

    dokumanlar = dokuman_ara(
        arama_metni=arama,
        kategori=kategori,
        departman=departman,
        onay_durumu=onay_durumu,
        kullanici=current_user,
        page=page,
        per_page=15
    )

    return render_template('dys/liste.html',
                           dokumanlar=dokumanlar,
                           kategori=kategori,
                           departman=departman,
                           onay_durumu=onay_durumu,
                           arama=arama)


# ══════════════════════════════════════════════════════════════════
# DOKÜMAN YÜKLEME
# ══════════════════════════════════════════════════════════════════

@dys_bp.route('/yukle', methods=['GET', 'POST'])
@login_required
@yazma_izni_gerekli('dys')
@log_action('Doküman Yükleme')
def yukle():
    """Yeni doküman yükleme."""
    form = DokumanYukleForm()

    if form.validate_on_submit():
        dosya = form.dosya.data
        if not dosya:
            flash('Lütfen bir dosya seçin.', 'warning')
            return render_template('dys/yukle.html', form=form, title='Yeni Doküman Yükle')

        dokuman, hata = dokuman_yukle(
            dosya=dosya,
            baslik=form.baslik.data,
            kategori=form.kategori.data,
            kullanici=current_user,
            alt_kategori=form.alt_kategori.data,
            etiketler_metin=form.etiketler_metin.data,
            departman=form.departman.data,
            erisim_seviyesi=form.erisim_seviyesi.data,
            aciklama=form.aciklama.data,
            onay_gonder=form.onay_gonder.data,
        )

        if hata:
            flash(f'Yükleme hatası: {hata}', 'danger')
        else:
            flash(f'Doküman başarıyla yüklendi: {dokuman.baslik}', 'success')
            return redirect(url_for('dys.detay', id=dokuman.id))

    return render_template('dys/yukle.html', form=form, title='Yeni Doküman Yükle')


# ══════════════════════════════════════════════════════════════════
# DOKÜMAN DETAY
# ══════════════════════════════════════════════════════════════════

@dys_bp.route('/detay/<int:id>')
@login_required
@modul_erisim_gerekli('dys')
def detay(id):
    """Doküman detay sayfası — versiyon geçmişi, onay bilgileri."""
    dokuman = Dokuman.query.get_or_404(id)

    # Erişim kontrolü
    if not dokuman.erisim_kontrol(current_user):
        flash('Bu dokümana erişim yetkiniz bulunmuyor.', 'danger')
        return redirect(url_for('dys.liste'))

    # Versiyon geçmişi
    versiyon_gecmisi = dokuman.versiyon_gecmisi()

    # Onay formu (yöneticiler için)
    onay_form = DokumanOnayForm() if current_user.yonetici_mi() else None

    return render_template('dys/detay.html',
                           dokuman=dokuman,
                           versiyon_gecmisi=versiyon_gecmisi,
                           onay_form=onay_form)


# ══════════════════════════════════════════════════════════════════
# DOKÜMAN DÜZENLEME
# ══════════════════════════════════════════════════════════════════

@dys_bp.route('/duzenle/<int:id>', methods=['GET', 'POST'])
@login_required
@yazma_izni_gerekli('dys')
@log_action('Doküman Düzenleme')
def duzenle(id):
    """Doküman bilgilerini düzenleme (dosya değiştirilmez)."""
    dokuman = Dokuman.query.get_or_404(id)

    # Sadece sahip veya yönetici düzenleyebilir
    if dokuman.sahip_id != current_user.id and not current_user.yonetici_mi():
        flash('Bu dokümanı düzenleme yetkiniz yok.', 'danger')
        return redirect(url_for('dys.detay', id=id))

    form = DokumanDuzenleForm(obj=dokuman)

    if request.method == 'GET':
        # Etiketleri virgülle ayrılmış stringe dönüştür
        form.etiketler_metin.data = ', '.join(dokuman.etiket_listesi)

    if form.validate_on_submit():
        dokuman.baslik = form.baslik.data
        dokuman.kategori = form.kategori.data
        dokuman.alt_kategori = form.alt_kategori.data
        dokuman.departman = form.departman.data
        dokuman.erisim_seviyesi = form.erisim_seviyesi.data
        dokuman.aciklama = form.aciklama.data

        # Etiketleri ayrıştır
        etiketler_metin = form.etiketler_metin.data or ''
        dokuman.etiketler = [e.strip() for e in etiketler_metin.split(',') if e.strip()]

        db.session.commit()
        flash('Doküman bilgileri güncellendi.', 'success')
        return redirect(url_for('dys.detay', id=id))

    return render_template('dys/yukle.html', form=form,
                           title='Doküman Düzenle', dokuman=dokuman, duzenleme=True)


# ══════════════════════════════════════════════════════════════════
# YENİ VERSİYON
# ══════════════════════════════════════════════════════════════════

@dys_bp.route('/yeni-versiyon/<int:id>', methods=['GET', 'POST'])
@login_required
@yazma_izni_gerekli('dys')
@log_action('Doküman Yeni Versiyon')
def yeni_versiyon(id):
    """Mevcut dokümanın yeni versiyonunu yükler."""
    mevcut = Dokuman.query.get_or_404(id)

    if request.method == 'POST':
        dosya = request.files.get('dosya')
        if not dosya or dosya.filename == '':
            flash('Lütfen yeni versiyon dosyasını seçin.', 'warning')
            return render_template('dys/yeni_versiyon.html', dokuman=mevcut)

        yeni, hata = dokuman_yeni_versiyon(mevcut.id, dosya, current_user)

        if hata:
            flash(f'Yükleme hatası: {hata}', 'danger')
        else:
            flash(f'Yeni versiyon başarıyla yüklendi (v{yeni.versiyon}).', 'success')
            return redirect(url_for('dys.detay', id=yeni.id))

    return render_template('dys/yeni_versiyon.html', dokuman=mevcut)


# ══════════════════════════════════════════════════════════════════
# İNDİRME
# ══════════════════════════════════════════════════════════════════

@dys_bp.route('/indir/<int:id>')
@login_required
@modul_erisim_gerekli('dys')
def indir(id):
    """Dokümanı indirir ve indirme sayısını artırır."""
    dokuman = Dokuman.query.get_or_404(id)

    # Erişim kontrolü
    if not dokuman.erisim_kontrol(current_user):
        flash('Bu dokümana erişim yetkiniz bulunmuyor.', 'danger')
        return redirect(url_for('dys.liste'))

    dosya_yolu = os.path.join(current_app.config['UPLOAD_FOLDER'], dokuman.dosya_adi)

    if not os.path.exists(dosya_yolu):
        flash('Dosya sunucuda bulunamadı.', 'danger')
        return redirect(url_for('dys.detay', id=id))

    # İndirme sayısını artır
    dokuman.indirme_artir()
    db.session.commit()

    return send_file(dosya_yolu, as_attachment=True, download_name=dokuman.orijinal_adi)


# ══════════════════════════════════════════════════════════════════
# ÖNİZLEME
# ══════════════════════════════════════════════════════════════════

@dys_bp.route('/onizle/<int:id>')
@login_required
@modul_erisim_gerekli('dys')
def onizle(id):
    """Doküman önizlemesi (resim ve PDF dosyaları için)."""
    dokuman = Dokuman.query.get_or_404(id)

    if not dokuman.erisim_kontrol(current_user):
        return jsonify({'error': 'Erişim yetkiniz yok'}), 403

    dosya_yolu = os.path.join(current_app.config['UPLOAD_FOLDER'], dokuman.dosya_adi)

    if not os.path.exists(dosya_yolu):
        return jsonify({'error': 'Dosya bulunamadı'}), 404

    return send_file(dosya_yolu, mimetype=dokuman.mime_type)


# ══════════════════════════════════════════════════════════════════
# ARAMA
# ══════════════════════════════════════════════════════════════════

@dys_bp.route('/arama')
@login_required
@modul_erisim_gerekli('dys')
def arama():
    """Doküman tam metin araması."""
    form = DokumanAramaForm(request.args)
    page = request.args.get('page', 1, type=int)

    arama_metni = request.args.get('arama_metni', '')
    kategori = request.args.get('kategori', '')
    departman = request.args.get('departman', '')
    onay_durumu = request.args.get('onay_durumu', '')

    sonuclar = None
    if arama_metni or kategori or departman or onay_durumu:
        sonuclar = dokuman_ara(
            arama_metni=arama_metni,
            kategori=kategori,
            departman=departman,
            onay_durumu=onay_durumu,
            kullanici=current_user,
            page=page,
        )

    return render_template('dys/arama.html',
                           form=form,
                           sonuclar=sonuclar,
                           arama_metni=arama_metni)


# ══════════════════════════════════════════════════════════════════
# ONAY İŞLEMLERİ
# ══════════════════════════════════════════════════════════════════

@dys_bp.route('/onayla/<int:id>', methods=['POST'])
@login_required
@yazma_izni_gerekli('dys')
@log_action('Doküman Onaylama')
def onayla(id):
    """Doküman onaylama."""
    dokuman = Dokuman.query.get_or_404(id)

    if dokuman.onay_durumu != 'onay_bekliyor':
        flash('Bu doküman onay bekleyen durumda değil.', 'warning')
        return redirect(url_for('dys.detay', id=id))

    if not current_user.yonetici_mi():
        flash('Onay yetkisi sadece yöneticilere aittir.', 'danger')
        return redirect(url_for('dys.detay', id=id))

    dokuman.onay_durumu = 'onaylandi'
    dokuman.onaylayan_id = current_user.id
    dokuman.onay_tarihi = datetime.now(timezone.utc)
    db.session.commit()

    flash(f'"{dokuman.baslik}" dokümanı onaylandı.', 'success')
    return redirect(url_for('dys.detay', id=id))


@dys_bp.route('/reddet/<int:id>', methods=['POST'])
@login_required
@yazma_izni_gerekli('dys')
@log_action('Doküman Reddetme')
def reddet(id):
    """Doküman reddetme."""
    dokuman = Dokuman.query.get_or_404(id)

    if dokuman.onay_durumu != 'onay_bekliyor':
        flash('Bu doküman onay bekleyen durumda değil.', 'warning')
        return redirect(url_for('dys.detay', id=id))

    if not current_user.yonetici_mi():
        flash('Red yetkisi sadece yöneticilere aittir.', 'danger')
        return redirect(url_for('dys.detay', id=id))

    red_nedeni = request.form.get('red_nedeni', '')

    dokuman.onay_durumu = 'reddedildi'
    dokuman.onaylayan_id = current_user.id
    dokuman.onay_tarihi = datetime.now(timezone.utc)
    dokuman.red_nedeni = red_nedeni
    db.session.commit()

    flash(f'"{dokuman.baslik}" dokümanı reddedildi.', 'warning')
    return redirect(url_for('dys.detay', id=id))


# ══════════════════════════════════════════════════════════════════
# SİLME
# ══════════════════════════════════════════════════════════════════

@dys_bp.route('/sil/<int:id>', methods=['POST'])
@login_required
@yazma_izni_gerekli('dys')
@log_action('Doküman Silme')
def sil(id):
    """Doküman silme (soft delete)."""
    dokuman = Dokuman.query.get_or_404(id)

    # Sadece sahip veya yönetici silebilir
    if dokuman.sahip_id != current_user.id and not current_user.yonetici_mi():
        flash('Bu dokümanı silme yetkiniz yok.', 'danger')
        return redirect(url_for('dys.detay', id=id))

    dokuman.aktif = False
    db.session.commit()

    flash(f'"{dokuman.baslik}" dokümanı silindi.', 'success')
    return redirect(url_for('dys.liste'))


# ══════════════════════════════════════════════════════════════════
# ONAY BEKLEYENLERİ LİSTELE
# ══════════════════════════════════════════════════════════════════

@dys_bp.route('/onay-bekleyen')
@login_required
@modul_erisim_gerekli('dys')
def onay_bekleyen():
    """Onay bekleyen dokümanları listeler."""
    page = request.args.get('page', 1, type=int)

    dokumanlar = Dokuman.query.filter_by(
        aktif=True, onay_durumu='onay_bekliyor'
    ).order_by(
        Dokuman.olusturma_tarihi.desc()
    ).paginate(page=page, per_page=15, error_out=False)

    return render_template('dys/liste.html',
                           dokumanlar=dokumanlar,
                           kategori='', departman='',
                           onay_durumu='onay_bekliyor', arama='',
                           title='Onay Bekleyen Dokümanlar')


# ══════════════════════════════════════════════════════════════════
# API: ETİKETLER (Autocomplete için)
# ══════════════════════════════════════════════════════════════════

@dys_bp.route('/api/etiketler')
@login_required
def api_etiketler():
    """Tüm benzersiz etiketleri JSON olarak döner (autocomplete için)."""
    dokumanlar = Dokuman.query.filter_by(aktif=True).with_entities(Dokuman.etiketler).all()

    tum_etiketler = set()
    for (etiketler,) in dokumanlar:
        if isinstance(etiketler, list):
            tum_etiketler.update(etiketler)

    return jsonify(sorted(list(tum_etiketler)))
