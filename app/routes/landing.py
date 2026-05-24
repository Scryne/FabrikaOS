"""
FabrikaOS — Landing Page (Ana Tanıtım Sayfası) Rotası
Giriş yapmamış kullanıcılara proje tanıtım sayfasını gösterir.
"""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

landing_bp = Blueprint('landing', __name__)


@landing_bp.route('/')
def index():
    """
    Ana sayfa — Landing Page.
    Giriş yapılmışsa dashboard'a yönlendir,
    yapılmamışsa tanıtım sayfasını göster.
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('landing.html')
