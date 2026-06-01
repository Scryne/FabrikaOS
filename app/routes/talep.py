"""
FDYS — Dahili Talep ve İş Takip Route'ları
Faz 4 — Talep Yönetimi
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user

from app.extensions import db
from app.utils.decorators import modul_erisim_gerekli, log_action
from app.models.talep import Talep, TalepGecmisi
from app.forms.talep import (
    TalepForm, TalepYonlendirmeForm, TalepDurumForm, TalepYorumForm
)
from app.services import talep_servisi, sms_servisi

talep_bp = Blueprint('talep', __name__, url_prefix='/talep')


@talep_bp.route('/')
@login_required
@modul_erisim_gerekli('talep')
def index():
    """Talep dashboard'u."""
    stats = talep_servisi.talep_dashboard_istatistik()
    return render_template('talep/index.html', stats=stats)


@talep_bp.route('/liste')
@login_required
@modul_erisim_gerekli('talep')
def liste():
    """Talepler listesi."""
    page = request.args.get('page', 1, type=int)
    durum = request.args.get('durum', '')
    kategori = request.args.get('kategori', '')
    oncelik = request.args.get('oncelik', '')
    arama = request.args.get('q', '').strip()

    sorgu = Talep.query.filter_by(aktif=True)

    if durum:
        sorgu = sorgu.filter(Talep.durum == durum)
    if kategori:
        sorgu = sorgu.filter(Talep.kategori == kategori)
    if oncelik:
        sorgu = sorgu.filter(Talep.oncelik == oncelik)
    if arama:
        terim = f"%{arama}%"
        sorgu = sorgu.filter(
            db.or_(
                Talep.talep_no.ilike(terim),
                Talep.baslik.ilike(terim),
                Talep.talep_eden_adi.ilike(terim)
            )
        )

    talepler = sorgu.order_by(Talep.olusturma_tarihi.desc()).paginate(page=page, per_page=15, error_out=False)

    return render_template('talep/liste.html',
                           talepler=talepler,
                           durum=durum,
                           kategori=kategori,
                           oncelik=oncelik,
                           arama=arama,
                           durumlar=Talep.DURUMLAR,
                           kategoriler=Talep.KATEGORILER,
                           oncelikler=Talep.ONCELIKLER)


@talep_bp.route('/ekle', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('talep', 'yazma')
@log_action('Dahili Talep Oluşturma')
def ekle():
    """Dahili kullanıcılar için manuel talep oluşturma formu."""
    form = TalepForm()

    if form.validate_on_submit():
        talep = Talep(
            talep_eden_tip=Talep.TIP_DAHILI,
            talep_eden_id=current_user.id,
            talep_eden_adi=current_user.ad_soyad,
            baslik=form.baslik.data,
            aciklama=form.aciklama.data,
            kategori=form.kategori.data,
            alt_kategori=form.alt_kategori.data,
            oncelik=form.oncelik.data,
            konum_bilgi=form.konum_bilgi.data,
            sms_bildirim=form.sms_bildirim.data,
            eposta_bildirim=form.eposta_bildirim.data,
        )

        talep = talep_servisi.talep_olustur(talep, yapan_id=current_user.id, yapan_adi=current_user.ad_soyad)
        flash(f'Talep başarıyla oluşturuldu: {talep.talep_no}', 'success')
        return redirect(url_for('talep.detay', id=talep.id))

    return render_template('talep/form.html', form=form, is_edit=False)


@talep_bp.route('/<int:id>')
@login_required
@modul_erisim_gerekli('talep')
def detay(id):
    """Talep detay sayfası ve zaman çizelgesi (timeline)."""
    talep = db.session.get(Talep, id)
    if not talep or not talep.aktif:
        flash('Talep bulunamadı.', 'danger')
        return redirect(url_for('talep.liste'))

    yonlendirme_form = TalepYonlendirmeForm()
    yonlendirme_form.talep_id.data = talep.id
    # Kullanıcı listesi (sorumlu seçimi için)
    from app.models.kullanici import Kullanici
    kullanicilar = [(k.id, k.ad_soyad) for k in Kullanici.query.filter_by(aktif=True).all()]
    yonlendirme_form.atanan_id.choices = [(0, '— Seçiniz —')] + kullanicilar

    durum_form = TalepDurumForm()
    durum_form.talep_id.data = talep.id
    durum_form.yeni_durum.data = talep.durum

    yorum_form = TalepYorumForm()
    yorum_form.talep_id.data = talep.id

    return render_template('talep/detay.html',
                           talep=talep,
                           yonlendirme_form=yonlendirme_form,
                           durum_form=durum_form,
                           yorum_form=yorum_form)


@talep_bp.route('/yonlendir', methods=['POST'])
@login_required
@modul_erisim_gerekli('talep', 'yazma')
@log_action('Talep Yönlendirme')
def yonlendir():
    """Talebi ilgili departman veya kişiye yönlendirir."""
    form = TalepYonlendirmeForm()
    # Atanan ID choices dynamic assignment needed to bypass validation error on POST
    from app.models.kullanici import Kullanici
    kullanicilar = [(k.id, k.ad_soyad) for k in Kullanici.query.filter_by(aktif=True).all()]
    form.atanan_id.choices = [(0, '— Seçiniz —')] + kullanicilar

    if form.validate_on_submit():
        talep_id = form.talep_id.data
        atanan_id = form.atanan_id.data if form.atanan_id.data != 0 else None

        talep, hata = talep_servisi.talep_yonlendir(
            talep_id,
            departman=form.atanan_departman.data,
            atanan_id=atanan_id,
            yapan_id=current_user.id,
            yapan_adi=current_user.ad_soyad,
            aciklama=form.aciklama.data
        )

        if hata:
            flash(hata, 'danger')
        else:
            flash('Talep başarıyla yönlendirildi.', 'success')

        return redirect(url_for('talep.detay', id=talep_id))

    flash('Yönlendirme sırasında bir hata oluştu.', 'danger')
    return redirect(request.referrer or url_for('talep.liste'))


@talep_bp.route('/durum_guncelle', methods=['POST'])
@login_required
@modul_erisim_gerekli('talep', 'yazma')
@log_action('Talep Durum Güncelleme')
def durum_guncelle():
    """Talebin durumunu günceller."""
    form = TalepDurumForm()
    if form.validate_on_submit():
        talep_id = form.talep_id.data
        talep, hata = talep_servisi.durum_guncelle(
            talep_id,
            yeni_durum=form.yeni_durum.data,
            yapan_id=current_user.id,
            yapan_adi=current_user.ad_soyad,
            aciklama=form.aciklama.data
        )

        if hata:
            flash(hata, 'danger')
        else:
            if form.cozum_notu.data:
                talep.cozum_notu = form.cozum_notu.data
                db.session.commit()

            # Bildirim gönder (SMS seçilmişse)
            if talep.sms_bildirim and talep.talep_eden_tip in (Talep.TIP_ORTAK, Talep.TIP_FIRMA, Talep.TIP_DIS_KULLANICI):
                # Telefon numarası bul (dış kullanıcı, ortak veya firma yetkilisi)
                telefon = _ilgili_telefon_bul(talep)
                if telefon:
                    if talep.durum == Talep.DURUM_TAMAMLANDI:
                        sms_servisi.talep_tamamlandi_sms(telefon, talep.talep_no)
                    else:
                        sms_servisi.talep_durum_sms(telefon, talep.talep_no, talep.durum_adi)

            flash('Talep durumu güncellendi.', 'success')

        return redirect(url_for('talep.detay', id=talep_id))

    flash('Durum güncellenirken hata oluştu.', 'danger')
    return redirect(request.referrer or url_for('talep.liste'))


@talep_bp.route('/yorum_ekle', methods=['POST'])
@login_required
@modul_erisim_gerekli('talep', 'yazma')
@log_action('Talebe Yorum Ekleme')
def yorum_ekle():
    """Talebe not/yorum ekler."""
    form = TalepYorumForm()
    if form.validate_on_submit():
        gecmis = talep_servisi.talep_yorum_ekle(
            talep_id=form.talep_id.data,
            yorum=form.yorum.data,
            yapan_id=current_user.id,
            yapan_adi=current_user.ad_soyad
        )
        if gecmis:
            flash('Yorum eklendi.', 'success')
        else:
            flash('Talep bulunamadı.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'danger')

    return redirect(request.referrer or url_for('talep.liste'))


def _ilgili_telefon_bul(talep):
    """Talep eden kişinin telefon numarasını bulur."""
    from app.models.dis_kullanici import DisKullanici
    from app.models.crm import Ortak, Firma

    if talep.talep_eden_tip == Talep.TIP_DIS_KULLANICI:
        dk = db.session.get(DisKullanici, talep.talep_eden_id)
        return dk.telefon if dk else None
    elif talep.talep_eden_tip == Talep.TIP_ORTAK:
        o = db.session.get(Ortak, talep.talep_eden_id)
        return o.telefon if o else None
    elif talep.talep_eden_tip == Talep.TIP_FIRMA:
        f = db.session.get(Firma, talep.talep_eden_id)
        return f.telefon if f else None
    return None
