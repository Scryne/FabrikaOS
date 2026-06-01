"""
FDYS — Duyuru & İletişim Rotaları
Faz 6 — Duyuru Yönetimi

10 endpoint: Dashboard/liste, oluşturma, detay, düzenleme,
silme, okundu işaretle, sabitlenmiş duyurular API,
istatistik, okunma detayları.
"""

import logging
from datetime import datetime, timezone
from flask import (
    Blueprint, render_template, request, flash,
    redirect, url_for, jsonify
)
from flask_login import login_required, current_user
from sqlalchemy import or_

from app.extensions import db
from app.utils.decorators import modul_erisim_gerekli, yazma_izni_gerekli, log_action
from app.models.duyuru import Duyuru, DuyuruOkunma
from app.forms.duyuru import DuyuruForm
from app.services.duyuru_servisi import (
    duyuru_olustur, duyurulari_getir, sabitlenmis_duyurular,
    duyuru_okunma_kaydet, duyuru_istatistikler, okunma_detay
)

logger = logging.getLogger(__name__)

duyuru_bp = Blueprint('duyuru', __name__, url_prefix='/duyuru')


# ══════════════════════════════════════════════════════════════════
# DUYURU LİSTESİ (ANA SAYFA)
# ══════════════════════════════════════════════════════════════════

@duyuru_bp.route('/')
@login_required
@modul_erisim_gerekli('duyuru')
def index():
    """Duyuru listesi — kullanıcının görebileceği duyurular."""
    page = request.args.get('page', 1, type=int)
    tur = request.args.get('tur', '')

    # Tüm duyuruları (yönetici) veya hedef kitleye uygunları getir
    if current_user.yonetici_mi():
        query = Duyuru.query.filter_by(aktif=True)
    else:
        duyurular_paginated = duyurulari_getir(current_user, page=page, per_page=15)
        istatistikler = duyuru_istatistikler()
        return render_template('duyuru/index.html',
                               duyurular=duyurular_paginated,
                               tur=tur,
                               **istatistikler)

    if tur:
        query = query.filter(Duyuru.tur == tur)

    duyurular_paginated = query.order_by(
        Duyuru.sabitle.desc(),
        Duyuru.yayin_tarihi.desc()
    ).paginate(page=page, per_page=15, error_out=False)

    istatistikler = duyuru_istatistikler()

    return render_template('duyuru/index.html',
                           duyurular=duyurular_paginated,
                           tur=tur,
                           **istatistikler)


# ══════════════════════════════════════════════════════════════════
# DUYURU OLUŞTURMA
# ══════════════════════════════════════════════════════════════════

@duyuru_bp.route('/ekle', methods=['GET', 'POST'])
@login_required
@yazma_izni_gerekli('duyuru')
@log_action('Duyuru Oluşturma')
def ekle():
    """Yeni duyuru oluşturma."""
    form = DuyuruForm()

    if form.validate_on_submit():
        duyuru = duyuru_olustur(
            baslik=form.baslik.data,
            icerik=form.icerik.data,
            kullanici=current_user,
            tur=form.tur.data,
            oncelik=form.oncelik.data,
            hedef_kitle=form.hedef_kitle.data,
            hedef_deger=form.hedef_deger.data,
            bitis_tarihi=form.bitis_tarihi.data,
            sabitle=form.sabitle.data,
        )

        flash(f'Duyuru başarıyla yayınlandı: "{duyuru.baslik}"', 'success')
        return redirect(url_for('duyuru.detay', id=duyuru.id))

    return render_template('duyuru/form.html', form=form, title='Yeni Duyuru')


# ══════════════════════════════════════════════════════════════════
# DUYURU DETAY
# ══════════════════════════════════════════════════════════════════

@duyuru_bp.route('/<int:id>')
@login_required
@modul_erisim_gerekli('duyuru')
def detay(id):
    """Duyuru detay sayfası — okunma istatistikleri."""
    duyuru = Duyuru.query.get_or_404(id)

    # Okundu olarak kaydet
    duyuru.okunma_kaydet(current_user.id)
    db.session.commit()

    # Okunma detayları (yöneticiler için)
    okunma_kayitlari = []
    if current_user.yonetici_mi():
        okunma_kayitlari = okunma_detay(id)

    return render_template('duyuru/detay.html',
                           duyuru=duyuru,
                           okunma_kayitlari=okunma_kayitlari)


# ══════════════════════════════════════════════════════════════════
# DUYURU DÜZENLEME
# ══════════════════════════════════════════════════════════════════

@duyuru_bp.route('/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
@yazma_izni_gerekli('duyuru')
@log_action('Duyuru Düzenleme')
def duzenle(id):
    """Duyuru düzenleme."""
    duyuru = Duyuru.query.get_or_404(id)

    # Sadece yayınlayan veya yönetici düzenleyebilir
    if duyuru.yayinlayan_id != current_user.id and not current_user.yonetici_mi():
        flash('Bu duyuruyu düzenleme yetkiniz yok.', 'danger')
        return redirect(url_for('duyuru.detay', id=id))

    form = DuyuruForm(obj=duyuru)

    if form.validate_on_submit():
        duyuru.baslik = form.baslik.data
        duyuru.icerik = form.icerik.data
        duyuru.tur = form.tur.data
        duyuru.oncelik = form.oncelik.data
        duyuru.hedef_kitle = form.hedef_kitle.data
        duyuru.hedef_deger = form.hedef_deger.data
        duyuru.bitis_tarihi = form.bitis_tarihi.data
        duyuru.sabitle = form.sabitle.data

        db.session.commit()
        flash('Duyuru güncellendi.', 'success')
        return redirect(url_for('duyuru.detay', id=id))

    return render_template('duyuru/form.html', form=form, duyuru=duyuru,
                           title='Duyuru Düzenle')


# ══════════════════════════════════════════════════════════════════
# DUYURU SİLME
# ══════════════════════════════════════════════════════════════════

@duyuru_bp.route('/<int:id>/sil', methods=['POST'])
@login_required
@yazma_izni_gerekli('duyuru')
@log_action('Duyuru Silme')
def sil(id):
    """Duyuru silme (soft delete)."""
    duyuru = Duyuru.query.get_or_404(id)

    if duyuru.yayinlayan_id != current_user.id and not current_user.yonetici_mi():
        flash('Bu duyuruyu silme yetkiniz yok.', 'danger')
        return redirect(url_for('duyuru.detay', id=id))

    duyuru.aktif = False
    db.session.commit()

    flash(f'Duyuru silindi: "{duyuru.baslik}"', 'success')
    return redirect(url_for('duyuru.index'))


# ══════════════════════════════════════════════════════════════════
# OKUNDU İŞARETLE (AJAX)
# ══════════════════════════════════════════════════════════════════

@duyuru_bp.route('/<int:id>/okundu', methods=['POST'])
@login_required
def okundu_isaretle(id):
    """Duyuruyu okundu olarak işaretler (AJAX)."""
    duyuru = Duyuru.query.get_or_404(id)
    yeni_kayit = duyuru.okunma_kaydet(current_user.id)
    db.session.commit()

    return jsonify({
        'success': True,
        'yeni_kayit': yeni_kayit,
        'okunma_sayisi': duyuru.okunma_sayisi
    })


# ══════════════════════════════════════════════════════════════════
# SABİTLENMİŞ DUYURULAR API (Banner için)
# ══════════════════════════════════════════════════════════════════

@duyuru_bp.route('/api/sabitlenmis')
@login_required
def api_sabitlenmis():
    """Sabitlenmiş duyuruları JSON olarak döner (banner widget için)."""
    duyurular = sabitlenmis_duyurular(current_user)

    data = []
    for d in duyurular:
        data.append({
            'id': d.id,
            'baslik': d.baslik,
            'tur': d.tur,
            'oncelik': d.oncelik,
            'tur_ikonu': d.tur_ikonu,
            'tur_rengi': d.tur_rengi,
            'oncelik_adi': d.oncelik_adi,
            'url': url_for('duyuru.detay', id=d.id),
        })

    return jsonify({'duyurular': data, 'toplam': len(data)})


# ══════════════════════════════════════════════════════════════════
# SABİTLE / SABİTLEMEYİ KALDIR
# ══════════════════════════════════════════════════════════════════

@duyuru_bp.route('/<int:id>/sabitle', methods=['POST'])
@login_required
@yazma_izni_gerekli('duyuru')
@log_action('Duyuru Sabitleme')
def sabitle(id):
    """Duyuruyu üst çubuğa sabitler/sabitlemeyi kaldırır."""
    duyuru = Duyuru.query.get_or_404(id)

    if not current_user.yonetici_mi():
        flash('Sabitleme yetkisi sadece yöneticilere aittir.', 'danger')
        return redirect(url_for('duyuru.detay', id=id))

    duyuru.sabitle = not duyuru.sabitle
    db.session.commit()

    durum = 'sabitlendi' if duyuru.sabitle else 'sabitleme kaldırıldı'
    flash(f'Duyuru {durum}.', 'success')
    return redirect(url_for('duyuru.detay', id=id))
