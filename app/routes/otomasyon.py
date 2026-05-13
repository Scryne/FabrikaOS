"""FDYS — Otomasyon & Kurallar Frontend Rotaları"""

from flask import Blueprint, render_template
from flask_login import login_required
from app.utils.decorators import role_required

otomasyon_bp = Blueprint('otomasyon', __name__, url_prefix='/otomasyon')

@otomasyon_bp.route('/')
@login_required
@role_required('yonetici')
def index():
    """Otomasyon kuralları yönetim paneli."""
    return render_template('otomasyon/index.html')
