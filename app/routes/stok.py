"""FDYS — Stok ve Malzeme Yönetimi Rotaları"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.stok import Malzeme, StokHareketi, Tedarikci
from app.forms.stok import MalzemeForm, StokHareketForm, TedarikciForm
from app.utils.decorators import modul_erisim_gerekli, log_action
from datetime import datetime

stok_bp = Blueprint('stok', __name__, url_prefix='/stok')


@stok_bp.route('/')
@login_required
@modul_erisim_gerekli('stok')
def index():
    """Malzeme listesi ve stok durumu."""
    page = request.args.get('page', 1, type=int)
    malzemeler_pagination = Malzeme.query.filter_by(aktif=True).order_by(Malzeme.ad).paginate(
        page=page, per_page=20, error_out=False)
    kritik_malzemeler = [m for m in malzemeler_pagination.items if m.stok_kritik_mi()]
    
    return render_template('stok/index.html', 
                           malzemeler=malzemeler_pagination.items,
                           pagination=malzemeler_pagination,
                           kritik_sayisi=len(kritik_malzemeler))


@stok_bp.route('/ekle', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('stok')
@log_action('Malzeme Tanımlama')
def ekle():
    form = MalzemeForm()
    # Tedarikçi listesini doldur
    form.tedarikci_id.choices = [(0, '--- Belirlenmedi ---')] + [(t.id, t.ad) for t in Tedarikci.query.filter_by(aktif=True).all()]
    
    if form.validate_on_submit():
        malzeme = Malzeme(
            ad=form.ad.data,
            kod=form.kod.data,
            birim=form.birim.data,
            kategori=form.kategori.data,
            lokasyon=form.lokasyon.data,
            birim_fiyat=form.birim_fiyat.data,
            minimum_stok=form.minimum_stok.data,
            tedarikci_id=form.tedarikci_id.data if form.tedarikci_id.data != 0 else None
        )
        db.session.add(malzeme)
        db.session.commit()
        flash(f'{malzeme.ad} başarıyla tanımlandı.', 'success')
        return redirect(url_for('stok.index'))
        
    return render_template('stok/form.html', form=form, title="Yeni Malzeme Tanımla")


@stok_bp.route('/duzenle/<int:id>', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('stok')
@log_action('Malzeme Düzenleme')
def duzenle(id):
    malzeme = Malzeme.query.get_or_404(id)
    form = MalzemeForm(obj=malzeme)
    # Tedarikçi listesini doldur
    form.tedarikci_id.choices = [(0, '--- Belirlenmedi ---')] + [(t.id, t.ad) for t in Tedarikci.query.filter_by(aktif=True).all()]
    
    # Form GET request'i ile yüklendiğinde mevcut tedarikçi idsini set et
    if request.method == 'GET' and malzeme.tedarikci_id:
        form.tedarikci_id.data = malzeme.tedarikci_id
    
    if form.validate_on_submit():
        malzeme.ad = form.ad.data
        malzeme.kod = form.kod.data
        malzeme.birim = form.birim.data
        malzeme.kategori = form.kategori.data
        malzeme.lokasyon = form.lokasyon.data
        malzeme.birim_fiyat = form.birim_fiyat.data
        malzeme.minimum_stok = form.minimum_stok.data
        malzeme.tedarikci_id = form.tedarikci_id.data if form.tedarikci_id.data != 0 else None
        
        db.session.commit()
        flash(f'{malzeme.ad} başarıyla güncellendi.', 'success')
        return redirect(url_for('stok.index'))
        
    return render_template('stok/form.html', form=form, malzeme=malzeme, title="Malzeme Düzenle")


@stok_bp.route('/hareket/<int:id>', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('stok')
@log_action('Stok Hareketi')
def hareket_ekle(id):
    malzeme = Malzeme.query.get_or_404(id)
    form = StokHareketForm()
    
    if form.validate_on_submit():
        miktar = form.miktar.data
        turu = form.hareket_turu.data
        
        # Stok kontrolü (çıkış için)
        if turu == 'cikis' and malzeme.mevcut_miktar < miktar:
            flash(f'Yetersiz stok! Mevcut: {malzeme.mevcut_miktar} {malzeme.birim}', 'danger')
            return render_template('stok/hareket_form.html', form=form, malzeme=malzeme)
            
        hareket = StokHareketi(
            malzeme_id=id,
            hareket_turu=turu,
            miktar=miktar,
            birim_fiyat=form.birim_fiyat.data or malzeme.birim_fiyat,
            fatura_no=form.fatura_no.data,
            neden=form.neden.data,
            islem_yapan_id=current_user.id
        )
        
        # Miktarı güncelle
        if turu == 'giris':
            malzeme.mevcut_miktar += miktar
        else:
            malzeme.mevcut_miktar -= miktar
            
        db.session.add(hareket)
        db.session.commit()
        
        # Kritik Stok Kontrolü ve Bildirim
        if malzeme.stok_kritik_mi():
            from app.services.bildirim_motoru import bildirim_motoru
            from app.models.kullanici import Kullanici
            yoneticiler = Kullanici.query.filter_by(rol='yonetici').all()
            for y in yoneticiler:
                bildirim_motoru.bildirim_olustur(
                    kullanici_id=y.id,
                    baslik="Kritik Stok Uyarısı",
                    mesaj=f"{malzeme.ad} ({malzeme.kod}) stok seviyesi kritik eşiğin altına düştü! Kalan: {malzeme.mevcut_miktar} {malzeme.birim}",
                    seviye="uyari",
                    modul="stok",
                    url=url_for('stok.index')
                )

            # Otomatik Satın Alma Talebi İş Emri (Kategori 6 — İş Akışı Otomasyonu)
            try:
                from app.services.otomasyon_motoru import otomasyon_motoru
                otomasyon_motoru.stok_satin_alma_talebi(malzeme)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Stok otomasyon tetikleme hatası: {e}")
        
        flash('Stok hareketi başarıyla kaydedildi.', 'success')
        return redirect(url_for('stok.index'))
        
    return render_template('stok/hareket_form.html', form=form, malzeme=malzeme)


@stok_bp.route('/tedarikciler')
@login_required
@modul_erisim_gerekli('stok')
def tedarikciler():
    page = request.args.get('page', 1, type=int)
    liste = Tedarikci.query.order_by(Tedarikci.ad).paginate(page=page, per_page=20, error_out=False)
    return render_template('stok/tedarikciler.html', tedarikciler=liste.items, pagination=liste)


@stok_bp.route('/tedarikci/ekle', methods=['GET', 'POST'])
@login_required
@modul_erisim_gerekli('stok')
@log_action('Tedarikçi Ekleme')
def tedarikci_ekle():
    form = TedarikciForm()
    if form.validate_on_submit():
        t = Tedarikci(
            ad=form.ad.data,
            yetkili_kisi=form.yetkili_kisi.data,
            telefon=form.telefon.data,
            eposta=form.eposta.data,
            adres=form.adres.data,
            ortalama_teslimat_gun=form.ortalama_teslimat_gun.data
        )
        db.session.add(t)
        db.session.commit()
        flash('Tedarikçi kaydedildi.', 'success')
        return redirect(url_for('stok.tedarikciler'))
    return render_template('stok/tedarikci_form.html', form=form)
