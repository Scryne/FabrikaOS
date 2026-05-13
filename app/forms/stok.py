from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, Email, Regexp

class MalzemeForm(FlaskForm):
    ad = StringField('Malzeme Adı', validators=[DataRequired(), Length(min=2, max=150)])
    kod = StringField('Malzeme Kodu', validators=[DataRequired(), Length(min=2, max=50)])
    birim = SelectField('Birim', choices=[('adet', 'Adet'), ('kg', 'Kilogram'), ('litre', 'Litre'), ('metre', 'Metre')], validators=[DataRequired()])
    kategori = StringField('Kategori', validators=[Optional(), Length(max=100)])
    lokasyon = StringField('Lokasyon (Raf/Bölüm)', validators=[Optional(), Length(max=100)])
    birim_fiyat = DecimalField('Birim Fiyat', validators=[Optional(), NumberRange(min=0)])
    minimum_stok = DecimalField('Kritik Stok Seviyesi', validators=[DataRequired(), NumberRange(min=0)], default=0)
    tedarikci_id = SelectField('Tedarikçi', coerce=int, validators=[Optional()])
    submit = SubmitField('Kaydet')

class StokHareketForm(FlaskForm):
    hareket_turu = SelectField('İşlem Türü', choices=[('giris', 'Stok Girişi (+)'), ('cikis', 'Stok Çıkışı (-)')], validators=[DataRequired()])
    miktar = DecimalField('Miktar', validators=[DataRequired(), NumberRange(min=0.01)])
    birim_fiyat = DecimalField('Birim Fiyat (Opsiyonel)', validators=[Optional(), NumberRange(min=0)])
    fatura_no = StringField('Fatura/Belge No', validators=[Optional(), Length(max=50)])
    neden = StringField('Açıklama/Neden', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Hareketi Kaydet')

class TedarikciForm(FlaskForm):
    ad = StringField('Tedarikçi Firma Adı', validators=[DataRequired(), Length(min=2, max=150)])
    yetkili_kisi = StringField('Yetkili Kişi', validators=[Optional(), Regexp(r'^[^0-9]*$', message="Yetkili kişi adında rakam bulunamaz."), Length(max=100)])
    telefon = StringField('Telefon', validators=[Optional(), Regexp(r'^0\d{3} \d{3} \d{4}$', message="Geçerli format: 0XXX XXX XXXX"), Length(max=20)])
    eposta = StringField('E-posta', validators=[Optional(), Email(message="Lütfen geçerli bir e-posta adresi giriniz.", check_deliverability=True), Length(max=120)])
    adres = TextAreaField('Adres', validators=[Optional()])
    ortalama_teslimat_gun = IntegerField('Ort. Teslimat Süresi (Gün)', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Tedarikçiyi Kaydet')
