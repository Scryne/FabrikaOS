"""
FDYS — CRM Formları
Faz 2 — Ortak & Firma Yönetimi

Ortak, Firma, Firma Yetkilisi ve İletişim kaydı formlarını içerir.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, SelectField, SubmitField, DecimalField,
    TextAreaField, IntegerField, HiddenField
)
from wtforms.validators import DataRequired, Length, Optional, NumberRange, Email


class OrtakForm(FlaskForm):
    """Ortak ekleme/düzenleme formu."""
    ortak_no = StringField('Ortak No', validators=[DataRequired(), Length(min=1, max=20)])
    ad_soyad = StringField('Ad Soyad', validators=[DataRequired(), Length(min=2, max=150)])
    tc_kimlik = StringField('TC Kimlik No', validators=[Optional(), Length(min=11, max=11)])
    telefon = StringField('Telefon', validators=[Optional(), Length(max=20)])
    telefon2 = StringField('Telefon 2', validators=[Optional(), Length(max=20)])
    eposta = StringField('E-posta', validators=[Optional(), Email(), Length(max=120)])
    adres = TextAreaField('Adres', validators=[Optional()])
    blok = StringField('Blok', validators=[Optional(), Length(max=50)])
    daire_no = StringField('Daire No', validators=[Optional(), Length(max=20)])
    ortak_tipi = SelectField('Ortak Tipi', choices=[
        ('malik', 'Malik'),
        ('kiraci', 'Kiracı'),
        ('yetkili', 'Yetkili'),
        ('vekil', 'Vekil'),
    ], validators=[DataRequired()])
    hisse_orani = DecimalField('Hisse Oranı (%)', places=2,
                                validators=[Optional(), NumberRange(min=0, max=100)])
    m2 = DecimalField('Alan (m²)', places=2,
                       validators=[Optional(), NumberRange(min=0)])
    milliyet = StringField('Milliyet', validators=[Optional(), Length(max=50)], default='T.C.')
    durum = SelectField('Durum', choices=[
        ('aktif', 'Aktif'),
        ('pasif', 'Pasif'),
        ('cikis_yapti', 'Çıkış Yaptı'),
    ], default='aktif')
    harita_enlem = DecimalField('Enlem', places=6, validators=[Optional()])
    harita_boylam = DecimalField('Boylam', places=6, validators=[Optional()])
    notlar = TextAreaField('Notlar', validators=[Optional()])
    submit = SubmitField('Kaydet')


class FirmaForm(FlaskForm):
    """Firma ekleme/düzenleme formu."""
    firma_no = StringField('Firma No', validators=[DataRequired(), Length(min=1, max=20)])
    unvan = StringField('Firma Ünvanı', validators=[DataRequired(), Length(min=2, max=300)])
    vergi_no = StringField('Vergi No', validators=[Optional(), Length(max=20)])
    vergi_dairesi = StringField('Vergi Dairesi', validators=[Optional(), Length(max=100)])
    sektor = SelectField('Sektör', choices=[
        ('uretim', 'Üretim'),
        ('hizmet', 'Hizmet'),
        ('ticaret', 'Ticaret'),
        ('lojistik', 'Lojistik'),
        ('gida', 'Gıda'),
        ('insaat', 'İnşaat'),
        ('tekstil', 'Tekstil'),
        ('metal', 'Metal İşleme'),
        ('kimya', 'Kimya'),
        ('plastik', 'Plastik'),
        ('enerji', 'Enerji'),
        ('bilisim', 'Bilişim'),
        ('otomotiv', 'Otomotiv'),
        ('diger', 'Diğer'),
    ], validators=[Optional()])
    faaliyet_alani = StringField('Faaliyet Alanı', validators=[Optional(), Length(max=200)])
    yetkili_kisi = StringField('Yetkili Kişi', validators=[Optional(), Length(max=150)])
    telefon = StringField('Telefon', validators=[Optional(), Length(max=20)])
    eposta = StringField('E-posta', validators=[Optional(), Email(), Length(max=120)])
    web_sitesi = StringField('Web Sitesi', validators=[Optional(), Length(max=200)])
    adres = TextAreaField('Adres', validators=[Optional()])
    blok = StringField('Blok', validators=[Optional(), Length(max=50)])
    daire_no = StringField('Daire No', validators=[Optional(), Length(max=20)])
    m2 = DecimalField('Alan (m²)', places=2,
                       validators=[Optional(), NumberRange(min=0)])
    calisan_sayisi = IntegerField('Çalışan Sayısı', validators=[Optional(), NumberRange(min=0)])
    durum = SelectField('Durum', choices=[
        ('aktif', 'Aktif'),
        ('pasif', 'Pasif'),
        ('kapandi', 'Kapandı'),
    ], default='aktif')
    harita_enlem = DecimalField('Enlem', places=6, validators=[Optional()])
    harita_boylam = DecimalField('Boylam', places=6, validators=[Optional()])
    notlar = TextAreaField('Notlar', validators=[Optional()])
    submit = SubmitField('Kaydet')


class FirmaYetkilisiForm(FlaskForm):
    """Firma yetkilisi ekleme formu."""
    firma_id = HiddenField('Firma ID')
    ad_soyad = StringField('Ad Soyad', validators=[DataRequired(), Length(min=2, max=150)])
    gorev = StringField('Görev / Unvan', validators=[Optional(), Length(max=100)])
    telefon = StringField('Telefon', validators=[Optional(), Length(max=20)])
    eposta = StringField('E-posta', validators=[Optional(), Email(), Length(max=120)])
    tc_kimlik = StringField('TC Kimlik No', validators=[Optional(), Length(min=11, max=11)])
    submit = SubmitField('Ekle')


class IletisimForm(FlaskForm):
    """İletişim kaydı ekleme formu (AJAX)."""
    ilgili_tip = HiddenField('İlgili Tip', validators=[DataRequired()])
    ilgili_id = HiddenField('İlgili ID', validators=[DataRequired()])
    iletisim_turu = SelectField('İletişim Türü', choices=[
        ('telefon', 'Telefon'),
        ('eposta', 'E-posta'),
        ('yuz_yuze', 'Yüz Yüze'),
        ('mektup', 'Mektup / Yazışma'),
        ('sms', 'SMS'),
    ], validators=[DataRequired()])
    konu = StringField('Konu', validators=[DataRequired(), Length(min=2, max=200)])
    detay = TextAreaField('Detay', validators=[Optional()])
    sonuc = TextAreaField('Sonuç', validators=[Optional()])
    submit = SubmitField('Kaydet')
