"""
FDYS — Kimlik Doğrulama Rotaları
Giriş / Çıkış / Profil
"""

from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db, limiter

import sys
import subprocess
import os

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    """Kullanıcı giriş sayfası. 5 başarısız denemede 30 dk kilitleme."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        from app.models.kullanici import Kullanici

        kullanici_adi = request.form.get('kullanici_adi', '').strip()
        sifre = request.form.get('sifre', '')

        kullanici = Kullanici.query.filter_by(kullanici_adi=kullanici_adi).first()

        if kullanici is None:
            flash('Kullanıcı adı veya şifre hatalı.', 'danger')
            return render_template('auth/login.html')

        # Hesap kilidi kontrolü
        if kullanici.hesap_kilitli:
            if kullanici.kilit_zamani and \
               datetime.now(timezone.utc) - kullanici.kilit_zamani < timedelta(minutes=30):
                flash('Hesabınız çok fazla başarısız deneme nedeniyle kilitlendi. '
                      '30 dakika sonra tekrar deneyin.', 'danger')
                return render_template('auth/login.html')
            else:
                # Kilit süresi doldu, kilidi kaldır
                kullanici.hesap_kilitli = False
                kullanici.basarisiz_giris = 0

        if not kullanici.aktif:
            flash('Hesabınız devre dışı bırakılmış. Yöneticiyle iletişime geçin.', 'warning')
            return render_template('auth/login.html')

        if kullanici.sifre_dogrula(sifre):
            kullanici.giris_basarili()
            db.session.commit()
            login_user(kullanici, remember=False)
            flash(f'Hoş geldiniz, {kullanici.ad_soyad}!', 'success')

            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            kullanici.giris_basarisiz()
            db.session.commit()
            kalan = 5 - kullanici.basarisiz_giris
            if kalan > 0:
                flash(f'Şifre hatalı. {kalan} deneme hakkınız kaldı.', 'danger')
            else:
                flash('Hesabınız kilitlendi. 30 dakika sonra tekrar deneyin.', 'danger')
            return render_template('auth/login.html')

    return render_template('auth/login.html')





@auth_bp.route('/logout')
@login_required
def logout():
    """Kullanıcı çıkışı."""
    logout_user()
    flash('Başarıyla çıkış yaptınız.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profil')
@login_required
def profil():
    """Kullanıcı profil sayfası."""
    from app.forms.auth import SifreDegistirForm
    form = SifreDegistirForm()
    return render_template('auth/profil.html', form=form)

@auth_bp.route('/sifre-degistir', methods=['POST'])
@login_required
def sifre_degistir():
    """Kullanıcının kendi şifresini değiştirmesi."""
    from app.forms.auth import SifreDegistirForm
    form = SifreDegistirForm()
    
    if form.validate_on_submit():
        if not current_user.sifre_dogrula(form.mevcut_sifre.data):
            flash('Mevcut şifreniz yanlış.', 'danger')
            return redirect(url_for('auth.profil'))
            
        current_user.sifre_belirle(form.yeni_sifre.data)
        db.session.commit()
        
        # Denetim izi oluştur (manuel olarak çünkü decorator kullanmak routing'i karmaşıklaştırabilir)
        from app.models.kullanici import DenetimIzi
        log = DenetimIzi(
            kullanici_id=current_user.id,
            islem='Şifre Değiştirme',
            tablo='Kullanici',
            ip_adresi=request.remote_addr,
            detay='Kullanıcı kendi şifresini değiştirdi.'
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Şifreniz başarıyla değiştirildi. Lütfen yeni şifrenizle giriş yapın.', 'success')
        logout_user()
        return redirect(url_for('auth.login'))
        
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{getattr(form, field).label.text}: {error}', 'danger')
            
    return redirect(url_for('auth.profil'))
