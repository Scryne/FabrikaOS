"""
FDYS — DYS (Doküman Yönetim Sistemi) Formları
Faz 6

Doküman yükleme, düzenleme, onay ve arama formları.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, TextAreaField, SelectField, HiddenField,
    IntegerField, BooleanField
)
from wtforms.validators import DataRequired, Optional, Length


class DokumanYukleForm(FlaskForm):
    """Doküman yükleme ve düzenleme formu."""

    baslik = StringField(
        'Doküman Başlığı',
        validators=[DataRequired(message='Başlık zorunludur.'), Length(max=300)]
    )
    kategori = SelectField(
        'Kategori',
        choices=[
            ('prosedur', 'Prosedür'),
            ('talimat', 'Talimat'),
            ('form', 'Form'),
            ('rapor', 'Rapor'),
            ('sozlesme', 'Sözleşme'),
            ('diger', 'Diğer'),
        ],
        validators=[DataRequired()]
    )
    alt_kategori = StringField(
        'Alt Kategori',
        validators=[Optional(), Length(max=100)]
    )
    etiketler_metin = StringField(
        'Etiketler',
        validators=[Optional(), Length(max=500)],
        description='Virgülle ayırarak yazın: ISO9001, kalite, prosedür'
    )
    departman = SelectField(
        'Departman',
        choices=[
            ('', '— Departman Seçin —'),
            ('uretim', 'Üretim'),
            ('kalite', 'Kalite'),
            ('bakim', 'Bakım'),
            ('ik', 'İnsan Kaynakları'),
            ('isg', 'İSG'),
            ('idari', 'İdari İşler'),
            ('muhasebe', 'Muhasebe'),
            ('bilgi_islem', 'Bilgi İşlem'),
            ('genel', 'Genel'),
        ],
        validators=[Optional()]
    )
    erisim_seviyesi = SelectField(
        'Erişim Seviyesi',
        choices=[
            ('herkese_acik', 'Herkese Açık'),
            ('departman', 'Departman İçi'),
            ('ozel', 'Özel (Sadece Ben)'),
            ('yonetim', 'Yönetim Kadrosu'),
        ],
        validators=[DataRequired()]
    )
    aciklama = TextAreaField(
        'Açıklama',
        validators=[Optional(), Length(max=2000)]
    )
    dosya = FileField(
        'Dosya',
        validators=[
            FileAllowed(
                ['jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf', 'doc', 'docx',
                 'xls', 'xlsx', 'csv', 'txt', 'md', 'ppt', 'pptx', 'zip', 'rar'],
                'Desteklenmeyen dosya formatı!'
            )
        ]
    )
    onay_gonder = BooleanField(
        'Onaya Gönder',
        default=False,
        description='İşaretlenirse doküman onay sürecine girer'
    )


class DokumanDuzenleForm(FlaskForm):
    """Doküman bilgilerini düzenleme formu (dosya değiştirilmez)."""

    baslik = StringField(
        'Doküman Başlığı',
        validators=[DataRequired(message='Başlık zorunludur.'), Length(max=300)]
    )
    kategori = SelectField(
        'Kategori',
        choices=[
            ('prosedur', 'Prosedür'),
            ('talimat', 'Talimat'),
            ('form', 'Form'),
            ('rapor', 'Rapor'),
            ('sozlesme', 'Sözleşme'),
            ('diger', 'Diğer'),
        ],
        validators=[DataRequired()]
    )
    alt_kategori = StringField(
        'Alt Kategori',
        validators=[Optional(), Length(max=100)]
    )
    etiketler_metin = StringField(
        'Etiketler',
        validators=[Optional(), Length(max=500)],
        description='Virgülle ayırarak yazın: ISO9001, kalite, prosedür'
    )
    departman = SelectField(
        'Departman',
        choices=[
            ('', '— Departman Seçin —'),
            ('uretim', 'Üretim'),
            ('kalite', 'Kalite'),
            ('bakim', 'Bakım'),
            ('ik', 'İnsan Kaynakları'),
            ('isg', 'İSG'),
            ('idari', 'İdari İşler'),
            ('muhasebe', 'Muhasebe'),
            ('bilgi_islem', 'Bilgi İşlem'),
            ('genel', 'Genel'),
        ],
        validators=[Optional()]
    )
    erisim_seviyesi = SelectField(
        'Erişim Seviyesi',
        choices=[
            ('herkese_acik', 'Herkese Açık'),
            ('departman', 'Departman İçi'),
            ('ozel', 'Özel (Sadece Ben)'),
            ('yonetim', 'Yönetim Kadrosu'),
        ],
        validators=[DataRequired()]
    )
    aciklama = TextAreaField(
        'Açıklama',
        validators=[Optional(), Length(max=2000)]
    )


class DokumanOnayForm(FlaskForm):
    """Doküman onay/red formu."""

    islem = SelectField(
        'İşlem',
        choices=[
            ('onaylandi', 'Onayla'),
            ('reddedildi', 'Reddet'),
        ],
        validators=[DataRequired()]
    )
    red_nedeni = TextAreaField(
        'Red Nedeni',
        validators=[Optional(), Length(max=1000)],
        description='Reddedilen dokümanlar için neden belirtiniz.'
    )


class DokumanAramaForm(FlaskForm):
    """Doküman tam metin arama formu."""

    arama_metni = StringField(
        'Arama',
        validators=[Optional(), Length(max=200)],
        description='Başlık, etiket veya OCR içerik araması'
    )
    kategori = SelectField(
        'Kategori',
        choices=[
            ('', 'Tüm Kategoriler'),
            ('prosedur', 'Prosedür'),
            ('talimat', 'Talimat'),
            ('form', 'Form'),
            ('rapor', 'Rapor'),
            ('sozlesme', 'Sözleşme'),
            ('diger', 'Diğer'),
        ],
        validators=[Optional()]
    )
    departman = SelectField(
        'Departman',
        choices=[
            ('', 'Tüm Departmanlar'),
            ('uretim', 'Üretim'),
            ('kalite', 'Kalite'),
            ('bakim', 'Bakım'),
            ('ik', 'İnsan Kaynakları'),
            ('isg', 'İSG'),
            ('idari', 'İdari İşler'),
            ('muhasebe', 'Muhasebe'),
            ('bilgi_islem', 'Bilgi İşlem'),
            ('genel', 'Genel'),
        ],
        validators=[Optional()]
    )
    onay_durumu = SelectField(
        'Onay Durumu',
        choices=[
            ('', 'Tüm Durumlar'),
            ('taslak', 'Taslak'),
            ('onay_bekliyor', 'Onay Bekliyor'),
            ('onaylandi', 'Onaylandı'),
            ('reddedildi', 'Reddedildi'),
        ],
        validators=[Optional()]
    )
