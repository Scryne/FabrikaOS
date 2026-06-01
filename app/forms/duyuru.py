"""
FDYS — Duyuru & İletişim Formları
Faz 6

Duyuru oluşturma ve düzenleme formları.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SelectField,
    BooleanField, DateTimeLocalField
)
from wtforms.validators import DataRequired, Optional, Length


class DuyuruForm(FlaskForm):
    """Duyuru oluşturma ve düzenleme formu."""

    baslik = StringField(
        'Duyuru Başlığı',
        validators=[DataRequired(message='Başlık zorunludur.'), Length(max=300)]
    )
    icerik = TextAreaField(
        'Duyuru İçeriği',
        validators=[DataRequired(message='İçerik zorunludur.')],
        description='HTML formatında zengin metin desteklenir'
    )
    tur = SelectField(
        'Duyuru Türü',
        choices=[
            ('bilgi', 'Bilgilendirme'),
            ('acil', 'Acil Duyuru'),
            ('etkinlik', 'Etkinlik'),
            ('bakim', 'Bakım Bildirimi'),
            ('toplanti', 'Toplantı'),
        ],
        validators=[DataRequired()]
    )
    oncelik = SelectField(
        'Öncelik',
        choices=[
            ('normal', 'Normal'),
            ('onemli', 'Önemli'),
            ('acil', 'Acil'),
        ],
        validators=[DataRequired()]
    )
    hedef_kitle = SelectField(
        'Hedef Kitle',
        choices=[
            ('tumu', 'Tüm Kullanıcılar'),
            ('departman', 'Belirli Departman'),
            ('rol', 'Belirli Rol'),
            ('kisi', 'Belirli Kişiler'),
        ],
        validators=[DataRequired()]
    )
    hedef_deger = StringField(
        'Hedef Değer',
        validators=[Optional(), Length(max=500)],
        description='Departman adı, rol adı veya virgülle ayrılmış kullanıcı ID\'leri'
    )
    bitis_tarihi = DateTimeLocalField(
        'Bitiş Tarihi',
        format='%Y-%m-%dT%H:%M',
        validators=[Optional()],
        description='Boş bırakılırsa duyuru süresiz olarak yayınlanır'
    )
    sabitle = BooleanField(
        'Üst Çubuğa Sabitle',
        default=False,
        description='İşaretlenirse duyuru tüm sayfaların üst çubuğunda görüntülenir'
    )
