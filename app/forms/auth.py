from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from app.utils.security import is_strong_password

def StrongPassword(form, field):
    if field.data:
        is_strong, msg = is_strong_password(field.data)
        if not is_strong:
            raise ValidationError(msg)

class SifreDegistirForm(FlaskForm):
    mevcut_sifre = PasswordField('Mevcut Şifre', validators=[DataRequired()])
    yeni_sifre = PasswordField('Yeni Şifre', validators=[DataRequired(), Length(min=8, max=255), StrongPassword])
    yeni_sifre_tekrar = PasswordField('Yeni Şifre (Tekrar)', validators=[DataRequired(), EqualTo('yeni_sifre', message='Şifreler uyuşmuyor.')])
    submit = SubmitField('Şifreyi Değiştir')
