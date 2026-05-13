from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, SubmitField, DecimalField, TextAreaField, TimeField
from wtforms.validators import DataRequired, Length, Optional, Email, Regexp
from datetime import datetime, timezone

class CalisanForm(FlaskForm):
    sicil_no = StringField('Sicil No', validators=[DataRequired(), Length(min=2, max=20)])
    ad_soyad = StringField('Ad Soyad', validators=[DataRequired(), Length(min=2, max=100)])
    departman = StringField('Departman', validators=[DataRequired(), Length(max=100)])
    pozisyon = StringField('Pozisyon', validators=[DataRequired(), Length(max=100)])
    telefon = StringField('Telefon', validators=[Optional(), Regexp(r'^0\d{3} \d{3} \d{4}$', message="Geçerli format: 0XXX XXX XXXX"), Length(max=20)])
    eposta = StringField('E-posta', validators=[Optional(), Email(message="Geçersiz e-posta adresi.", check_deliverability=True), Length(max=120)])
    ise_baslama = DateField('İşe Başlama Tarihi', format='%Y-%m-%d', validators=[DataRequired()], default=lambda: datetime.now(timezone.utc))
    ucret = DecimalField('Ücret (Opsiyonel)', validators=[Optional()])
    submit = SubmitField('Kaydet')

class VardiyaForm(FlaskForm):
    tarih = DateField('Tarih', format='%Y-%m-%d', validators=[DataRequired()], default=lambda: datetime.now(timezone.utc))
    vardiya_turu = SelectField('Vardiya Türü', choices=[('sabah', 'Sabah'), ('ogleden_sonra', 'Öğleden Sonra'), ('gece', 'Gece'), ('off', 'Off/İzin')], validators=[DataRequired()])
    baslangic = TimeField('Başlangıç Saati', format='%H:%M', validators=[DataRequired()])
    bitis = TimeField('Bitiş Saati', format='%H:%M', validators=[DataRequired()])
    notlar = TextAreaField('Notlar', validators=[Optional()])
    submit = SubmitField('Ata')

class IzinTalebiForm(FlaskForm):
    baslangic_tarihi = DateField('Başlangıç Tarihi', format='%Y-%m-%d', validators=[DataRequired()], default=lambda: datetime.now(timezone.utc))
    bitis_tarihi = DateField('Bitiş Tarihi', format='%Y-%m-%d', validators=[DataRequired()], default=lambda: datetime.now(timezone.utc))
    tur = SelectField('İzin Türü', choices=[('yillik', 'Yıllık İzin'), ('mazeret', 'Mazeret İzni'), ('saglik', 'Sağlık İzni'), ('ucretsiz', 'Ücretsiz İzin')], validators=[DataRequired()])
    aciklama = TextAreaField('Açıklama', validators=[Optional()])
    submit = SubmitField('Talep Et')
