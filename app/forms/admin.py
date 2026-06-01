from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, Optional, ValidationError
from app.models.kullanici import Kullanici
from app.utils.security import is_strong_password

def StrongPassword(form, field):
    if field.data:
        is_strong, msg = is_strong_password(field.data)
        if not is_strong:
            raise ValidationError(msg)

class KullaniciEkleForm(FlaskForm):
    ad_soyad = StringField('Ad Soyad', validators=[DataRequired(), Length(min=2, max=100)])
    kullanici_adi = StringField('Kullanıcı Adı', validators=[DataRequired(), Length(min=3, max=50)])
    sifre = PasswordField('Şifre', validators=[DataRequired(), Length(min=8, max=255), StrongPassword])
    sifre_tekrar = PasswordField('Şifre Tekrar', validators=[DataRequired(), EqualTo('sifre', message='Şifreler uyuşmuyor.')])
    rol = SelectField('Rol', choices=[
        ('yonetici', 'Yönetici'),
        ('operator', 'Operatör'),
        ('teknisyen', 'Teknisyen'),
        ('ik_uzmani', 'İK Uzmanı'),
        ('isg_uzmani', 'İSG Uzmanı'),
        ('muhasebe', 'Muhasebe'),
        ('crm_yetkilisi', 'CRM Yetkilisi'),
        ('satin_alma', 'Satın Alma')
    ], validators=[DataRequired()])
    departman = StringField('Departman', validators=[Optional(), Length(max=50)])
    
    # Modül erişimleri
    modul_personel = BooleanField('Personel Yönetimi')
    modul_makine = BooleanField('Makine Modülü')
    modul_stok = BooleanField('Stok Modülü')
    modul_kalite = BooleanField('Kalite Modülü')
    modul_enerji = BooleanField('Enerji Modülü')
    modul_isg = BooleanField('İSG Modülü')
    modul_ik = BooleanField('İnsan Kaynakları')
    modul_crm = BooleanField('CRM (Ortak & Firma)')
    modul_sozlesme = BooleanField('Sözleşme & Kontrat')
    modul_talep = BooleanField('Talep & İş Takip')
    modul_satin_alma = BooleanField('Satın Alma')
    modul_dys = BooleanField('Doküman Yönetimi')
    modul_duyuru = BooleanField('Duyuru & İletişim')
    
    aktif = BooleanField('Aktif', default=True)
    submit = SubmitField('Kullanıcı Ekle')

    def validate_kullanici_adi(self, field):
        kullanici = Kullanici.query.filter_by(kullanici_adi=field.data).first()
        if kullanici:
            raise ValidationError('Bu kullanıcı adı zaten alınmış.')

class KullaniciDuzenleForm(FlaskForm):
    ad_soyad = StringField('Ad Soyad', validators=[DataRequired(), Length(min=2, max=100)])
    kullanici_adi = StringField('Kullanıcı Adı', validators=[DataRequired(), Length(min=3, max=50)])
    sifre = PasswordField('Şifre (Değiştirmek istemiyorsanız boş bırakın)', validators=[Optional(), Length(min=8, max=255), StrongPassword])
    sifre_tekrar = PasswordField('Şifre Tekrar', validators=[EqualTo('sifre', message='Şifreler uyuşmuyor.')])
    rol = SelectField('Rol', choices=[
        ('yonetici', 'Yönetici'),
        ('operator', 'Operatör'),
        ('teknisyen', 'Teknisyen'),
        ('ik_uzmani', 'İK Uzmanı'),
        ('isg_uzmani', 'İSG Uzmanı'),
        ('muhasebe', 'Muhasebe'),
        ('crm_yetkilisi', 'CRM Yetkilisi'),
        ('satin_alma', 'Satın Alma')
    ], validators=[DataRequired()])
    departman = StringField('Departman', validators=[Optional(), Length(max=50)])
    
    # Modül erişimleri
    modul_personel = BooleanField('Personel Yönetimi')
    modul_makine = BooleanField('Makine Modülü')
    modul_stok = BooleanField('Stok Modülü')
    modul_kalite = BooleanField('Kalite Modülü')
    modul_enerji = BooleanField('Enerji Modülü')
    modul_isg = BooleanField('İSG Modülü')
    modul_ik = BooleanField('İnsan Kaynakları')
    modul_crm = BooleanField('CRM (Ortak & Firma)')
    modul_sozlesme = BooleanField('Sözleşme & Kontrat')
    modul_talep = BooleanField('Talep & İş Takip')
    modul_satin_alma = BooleanField('Satın Alma')
    modul_dys = BooleanField('Doküman Yönetimi')
    modul_duyuru = BooleanField('Duyuru & İletişim')
    
    aktif = BooleanField('Aktif')
    hesap_kilitli = BooleanField('Hesap Kilitli')
    submit = SubmitField('Güncelle')
