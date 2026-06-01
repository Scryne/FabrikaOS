"""
FDYS — Sözleşme Formları
Faz 3 — Sözleşme, Kira Kontrat & Sigorta Poliçe

Sözleşme oluşturma/düzenleme, kira kontratı detayları,
sigorta poliçesi ve standart metin şablonu formlarını içerir.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, SelectField, SubmitField, DecimalField,
    TextAreaField, IntegerField, HiddenField, DateField,
    BooleanField
)
from wtforms.validators import DataRequired, Length, Optional, NumberRange


class SozlesmeForm(FlaskForm):
    """Ana sözleşme ekleme/düzenleme formu."""
    sozlesme_no = StringField('Sözleşme No', validators=[DataRequired(), Length(min=1, max=30)])
    tur = SelectField('Sözleşme Türü', choices=[
        ('kira', 'Kira Sözleşmesi'),
        ('hizmet', 'Hizmet Sözleşmesi'),
        ('bakim', 'Bakım Sözleşmesi'),
        ('sigorta', 'Sigorta Poliçesi'),
        ('diger', 'Diğer'),
    ], validators=[DataRequired()])

    taraf_tip = SelectField('Taraf Tipi', choices=[
        ('ortak', 'Ortak'),
        ('firma', 'Firma'),
    ], validators=[DataRequired()])
    taraf_id = SelectField('Taraf', choices=[], coerce=int, validators=[DataRequired()])

    baslik = StringField('Sözleşme Başlığı', validators=[DataRequired(), Length(min=3, max=300)])
    aciklama = TextAreaField('Açıklama', validators=[Optional()])

    baslangic_tarihi = DateField('Başlangıç Tarihi', validators=[DataRequired()])
    bitis_tarihi = DateField('Bitiş Tarihi', validators=[Optional()])

    tutar = DecimalField('Tutar', places=2, validators=[Optional(), NumberRange(min=0)])
    para_birimi = SelectField('Para Birimi', choices=[
        ('TL', '₺ TL'),
        ('USD', '$ USD'),
        ('EUR', '€ EUR'),
    ], default='TL')
    odeme_periyodu = SelectField('Ödeme Periyodu', choices=[
        ('aylik', 'Aylık'),
        ('3_aylik', '3 Aylık'),
        ('6_aylik', '6 Aylık'),
        ('yillik', 'Yıllık'),
        ('tek_sefer', 'Tek Seferlik'),
    ], validators=[Optional()])

    otomatik_yenileme = BooleanField('Otomatik Yenileme', default=False)
    yenileme_suresi_ay = IntegerField('Yenileme Süresi (Ay)',
                                       validators=[Optional(), NumberRange(min=1, max=120)])
    hatirlatma_gun = IntegerField('Hatırlatma (Gün Önce)',
                                   validators=[Optional(), NumberRange(min=1, max=365)],
                                   default=30)

    standart_metin_id = SelectField('Standart Metin Şablonu', choices=[], coerce=int,
                                     validators=[Optional()])

    durum = SelectField('Durum', choices=[
        ('aktif', 'Aktif'),
        ('sona_erdi', 'Sona Erdi'),
        ('iptal', 'İptal Edildi'),
        ('askida', 'Askıda'),
    ], default='aktif')
    notlar = TextAreaField('Notlar', validators=[Optional()])
    submit = SubmitField('Kaydet')


class KiraKontratForm(FlaskForm):
    """Kira kontratı detay formu (Sözleşme formuna ek olarak kullanılır)."""
    daire_no = StringField('Daire No', validators=[Optional(), Length(max=20)])
    blok = StringField('Blok', validators=[Optional(), Length(max=50)])
    kat = StringField('Kat', validators=[Optional(), Length(max=10)])
    m2 = DecimalField('Alan (m²)', places=2, validators=[Optional(), NumberRange(min=0)])

    kira_tutari = DecimalField('Kira Tutarı (₺)', places=2,
                                validators=[Optional(), NumberRange(min=0)])
    depozito = DecimalField('Depozito (₺)', places=2,
                             validators=[Optional(), NumberRange(min=0)])
    aidat_tutari = DecimalField('Aylık Aidat (₺)', places=2,
                                 validators=[Optional(), NumberRange(min=0)])

    artis_turu = SelectField('Artış Türü', choices=[
        ('tufe', 'TÜFE Bazlı'),
        ('yfe', 'ÜFE/YFE Bazlı'),
        ('sabit_yuzde', 'Sabit Yüzde'),
        ('anlasmali', 'Anlaşmalı'),
    ], validators=[Optional()])
    artis_orani = DecimalField('Artış Oranı (%)', places=2,
                                validators=[Optional(), NumberRange(min=0, max=100)])
    son_artis_tarihi = DateField('Son Artış Tarihi', validators=[Optional()])
    sonraki_artis_tarihi = DateField('Sonraki Artış Tarihi', validators=[Optional()])

    odeme_gunu = IntegerField('Ödeme Günü (1-31)',
                               validators=[Optional(), NumberRange(min=1, max=31)])
    gecikme_faiz_orani = DecimalField('Gecikme Faizi (%/ay)', places=2,
                                       validators=[Optional(), NumberRange(min=0, max=100)])
    submit = SubmitField('Kaydet')


class SigortaPoliceForm(FlaskForm):
    """Sigorta poliçesi ekleme/düzenleme formu."""
    police_no = StringField('Poliçe No', validators=[DataRequired(), Length(min=1, max=50)])
    sigorta_sirketi = StringField('Sigorta Şirketi', validators=[DataRequired(), Length(min=2, max=150)])
    sigorta_turu = SelectField('Sigorta Türü', choices=[
        ('yangin', 'Yangın Sigortası'),
        ('deprem', 'Deprem / DASK'),
        ('kasko', 'Araç Kasko'),
        ('isveren_sorumluluk', 'İşveren Sorumluluk'),
        ('genel_sorumluluk', 'Genel Sorumluluk'),
        ('ferdi_kaza', 'Ferdi Kaza'),
    ], validators=[DataRequired()])

    police_baslangic = DateField('Poliçe Başlangıcı', validators=[DataRequired()])
    police_bitis = DateField('Poliçe Bitişi', validators=[DataRequired()])

    prim_tutari = DecimalField('Prim Tutarı (₺)', places=2,
                                validators=[Optional(), NumberRange(min=0)])
    teminat_tutari = DecimalField('Teminat Tutarı (₺)', places=2,
                                   validators=[Optional(), NumberRange(min=0)])

    hatirlatma_gun = IntegerField('Hatırlatma (Gün Önce)',
                                   validators=[Optional(), NumberRange(min=1, max=365)],
                                   default=30)

    # Sözleşme bağlantısı (opsiyonel)
    sozlesme_id = SelectField('Bağlı Sözleşme', choices=[], coerce=int,
                               validators=[Optional()])

    durum = SelectField('Durum', choices=[
        ('aktif', 'Aktif'),
        ('suresi_doldu', 'Süresi Doldu'),
        ('iptal', 'İptal Edildi'),
    ], default='aktif')
    notlar = TextAreaField('Notlar', validators=[Optional()])
    submit = SubmitField('Kaydet')


class StandartMetinForm(FlaskForm):
    """Standart metin şablonu oluşturma/düzenleme formu."""
    baslik = StringField('Şablon Başlığı', validators=[DataRequired(), Length(min=3, max=200)])
    icerik = TextAreaField('Şablon İçeriği', validators=[DataRequired()])
    tur = SelectField('Şablon Türü', choices=[
        ('kira', 'Kira Sözleşmesi'),
        ('hizmet', 'Hizmet Sözleşmesi'),
        ('bakim', 'Bakım Sözleşmesi'),
        ('genel', 'Genel Şablon'),
    ], validators=[DataRequired()])
    submit = SubmitField('Kaydet')
