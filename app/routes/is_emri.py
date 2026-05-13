"""FDYS — İş Emri ve Görev Yönetimi Rotaları (Kategori 6 — İş Akışı Otomasyonu)"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.is_emri import IsEmri, IsEmriYorum
from app.models.kullanici import Kullanici
from app.forms.is_emri import IsEmriForm, IsEmriGuncellemeForm, IsEmriYorumForm
from app.services.is_emri_servisi import is_emri_servisi
from app.utils.decorators import log_action
from sqlalchemy import desc

is_emri_bp = Blueprint('is_emri', __name__, url_prefix='/is-emri')


@is_emri_bp.route('/')
@login_required
def index():
    """İş emri listesi — filtreli, sayfalı."""
    # Filtreler
    durum_filtre = request.args.get('durum', '')
    oncelik_filtre = request.args.get('oncelik', '')
    kategori_filtre = request.args.get('kategori', '')
    arama = request.args.get('q', '')

    query = IsEmri.query

    if durum_filtre:
        query = query.filter(IsEmri.durum == durum_filtre)
    if oncelik_filtre:
        query = query.filter(IsEmri.oncelik == oncelik_filtre)
    if kategori_filtre:
        query = query.filter(IsEmri.kategori == kategori_filtre)
    if arama:
        query = query.filter(
            db.or_(
                IsEmri.baslik.ilike(f'%{arama}%'),
                IsEmri.is_emri_no.ilike(f'%{arama}%'),
            )
        )

    # Sıralama: SLA aşılanlar önce, sonra önceliğe göre
    oncelik_sirasi = db.case(
        (IsEmri.oncelik == 'kritik', 1),
        (IsEmri.oncelik == 'yuksek', 2),
        (IsEmri.oncelik == 'normal', 3),
        (IsEmri.oncelik == 'dusuk', 4),
        else_=5
    )
    query = query.order_by(
        IsEmri.sla_asildi_mi.desc(),
        oncelik_sirasi,
        IsEmri.olusturma_tarihi.desc()
    )

    page = request.args.get('page', 1, type=int)
    is_emirleri_pagination = query.paginate(page=page, per_page=20, error_out=False)
    istatistikler = is_emri_servisi.istatistikler()

    # SLA kontrolü
    is_emri_servisi.sla_toplu_kontrol()

    return render_template('is_emri/index.html',
                           is_emirleri=is_emirleri_pagination.items,
                           pagination=is_emirleri_pagination,
                           stats=istatistikler,
                           filtreler={
                               'durum': durum_filtre,
                               'oncelik': oncelik_filtre,
                               'kategori': kategori_filtre,
                               'q': arama,
                           })


@is_emri_bp.route('/olustur', methods=['GET', 'POST'])
@login_required
@log_action('İş Emri Oluşturma')
def olustur():
    """Manuel iş emri oluşturma."""
    form = IsEmriForm()
    # Atanabilecek kullanıcı listesi
    kullanicilar = Kullanici.query.filter_by(aktif=True).all()
    form.atanan_id.choices = [(0, '— Atanmadı —')] + [(k.id, f"{k.ad_soyad} ({k.rol})") for k in kullanicilar]

    if form.validate_on_submit():
        atanan = form.atanan_id.data if form.atanan_id.data != 0 else None

        is_emri = is_emri_servisi.is_emri_olustur(
            baslik=form.baslik.data,
            aciklama=form.aciklama.data,
            kategori=form.kategori.data,
            oncelik=form.oncelik.data,
            olusturan_id=current_user.id,
            atanan_id=atanan,
            sla_saat=form.sla_saat.data,
        )

        flash(f'İş emri {is_emri.is_emri_no} başarıyla oluşturuldu.', 'success')
        return redirect(url_for('is_emri.detay', id=is_emri.id))

    return render_template('is_emri/form.html', form=form)


@is_emri_bp.route('/detay/<int:id>')
@login_required
def detay(id):
    """İş emri detay sayfası."""
    is_emri = IsEmri.query.get_or_404(id)
    guncelleme_form = IsEmriGuncellemeForm()
    yorum_form = IsEmriYorumForm()
    yorumlar = is_emri.yorumlar.all()

    # SLA kontrolü
    is_emri.sla_kontrol()
    db.session.commit()

    return render_template('is_emri/detay.html',
                           ie=is_emri,
                           guncelleme_form=guncelleme_form,
                           yorum_form=yorum_form,
                           yorumlar=yorumlar)


@is_emri_bp.route('/guncelle/<int:id>', methods=['POST'])
@login_required
@log_action('İş Emri Güncelleme')
def guncelle(id):
    """İş emri durum güncelleme."""
    form = IsEmriGuncellemeForm()
    if form.validate_on_submit():
        basarili, mesaj = is_emri_servisi.durum_guncelle(
            is_emri_id=id,
            yeni_durum=form.durum.data,
            kullanici_id=current_user.id,
            cozum_notu=form.cozum_notu.data
        )
        if basarili:
            flash(mesaj, 'success')
        else:
            flash(mesaj, 'danger')
    return redirect(url_for('is_emri.detay', id=id))


@is_emri_bp.route('/yorum/<int:id>', methods=['POST'])
@login_required
def yorum_ekle(id):
    """İş emrine yorum ekleme."""
    form = IsEmriYorumForm()
    if form.validate_on_submit():
        is_emri_servisi.yorum_ekle(
            is_emri_id=id,
            kullanici_id=current_user.id,
            icerik=form.icerik.data
        )
        flash('Yorum eklendi.', 'success')
    return redirect(url_for('is_emri.detay', id=id))


@is_emri_bp.route('/sil/<int:id>', methods=['POST'])
@login_required
@log_action('İş Emri Silme')
def sil(id):
    """İş emrini iptal eder (yönetici)."""
    if not current_user.yonetici_mi():
        flash('Bu işlem için yetkiniz yok.', 'danger')
        return redirect(url_for('is_emri.index'))

    is_emri = IsEmri.query.get_or_404(id)
    is_emri_servisi.durum_guncelle(id, 'iptal', current_user.id)
    flash(f'{is_emri.is_emri_no} iptal edildi.', 'warning')
    return redirect(url_for('is_emri.index'))


@is_emri_bp.route('/kanban')
@login_required
def kanban():
    """Kanban board görünümü."""
    is_emirleri = IsEmri.query.filter(
        IsEmri.durum != IsEmri.DURUM_IPTAL
    ).order_by(
        db.case(
            (IsEmri.oncelik == 'kritik', 1),
            (IsEmri.oncelik == 'yuksek', 2),
            (IsEmri.oncelik == 'normal', 3),
            (IsEmri.oncelik == 'dusuk', 4),
            else_=5
        ),
        IsEmri.olusturma_tarihi.desc()
    ).all()

    kolonlar = {
        'acik': [ie for ie in is_emirleri if ie.durum in ('acik', 'atandi')],
        'devam': [ie for ie in is_emirleri if ie.durum == 'devam'],
        'tamamlandi': [ie for ie in is_emirleri if ie.durum == 'tamamlandi'],
        'onaylandi': [ie for ie in is_emirleri if ie.durum == 'onaylandi'],
    }

    return render_template('is_emri/kanban.html', kolonlar=kolonlar)


@is_emri_bp.route('/api/durum-guncelle', methods=['POST'])
@login_required
def api_durum_guncelle():
    """Kanban sürükle-bırak için AJAX endpoint."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Geçersiz istek.'}), 400

    is_emri_id = data.get('is_emri_id')
    yeni_durum = data.get('durum')

    if not is_emri_id or not yeni_durum:
        return jsonify({'success': False, 'message': 'Eksik parametreler.'}), 400

    basarili, mesaj = is_emri_servisi.durum_guncelle(
        is_emri_id=int(is_emri_id),
        yeni_durum=yeni_durum,
        kullanici_id=current_user.id
    )

    return jsonify({'success': basarili, 'message': mesaj})


@is_emri_bp.route('/api/istatistikler')
@login_required
def api_istatistikler():
    """Dashboard widget için JSON istatistikler."""
    return jsonify(is_emri_servisi.istatistikler())
