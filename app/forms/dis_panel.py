"""
FDYS — Dış Kullanıcı Paneli Formları
Faz 4 — WTForms tanımları
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class DisKullaniciLoginForm(FlaskForm):
    """Dış kullanıcı giriş formu."""
    kullanici_adi = StringField('Kullanıcı Adı / TC No', validators=[
        DataRequired(message='Kullanıcı adı zorunludur.')
    ])
    sifre = PasswordField('Şifre', validators=[
        DataRequired(message='Şifre zorunludur.')
    ])
    hatirla = BooleanField('Beni Hatırla')


class SifreDegistirForm(FlaskForm):
    """Geçici şifreyi değiştirme formu."""
    eski_sifre = PasswordField('Mevcut / Geçici Şifre', validators=[
        DataRequired(message='Mevcut şifre zorunludur.')
    ])
    yeni_sifre = PasswordField('Yeni Şifre', validators=[
        DataRequired(message='Yeni şifre zorunludur.'),
        Length(min=6, message='Şifre en az 6 karakter olmalıdır.')
    ])
    yeni_sifre_tekrar = PasswordField('Yeni Şifre (Tekrar)', validators=[
        DataRequired(message='Şifre tekrarı zorunludur.'),
        EqualTo('yeni_sifre', message='Şifreler eşleşmiyor.')
    ])


class ProfilGuncelleForm(FlaskForm):
    """Dış kullanıcı profil güncelleme formu."""
    telefon = StringField('Telefon Numarası', validators=[
        DataRequired(message='Telefon numarası zorunludur.'),
        Length(max=20)
    ])
    eposta = StringField('E-posta Adresi', validators=[
        DataRequired(message='E-posta zorunludur.'),
        Email(message='Geçerli bir e-posta adresi girin.'),
        Length(max=120)
    ])
