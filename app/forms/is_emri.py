"""
FDYS — İş Emri Form Tanımları
Kategori 6 — İş Akışı Otomasyonu
"""

from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, SelectField,
                     IntegerField, SubmitField)
from wtforms.validators import DataRequired, Length, Optional, NumberRange


class IsEmriForm(FlaskForm):
    """Yeni iş emri oluşturma formu."""
    baslik = StringField('İş Emri Başlığı', validators=[DataRequired(), Length(min=5, max=200)])
    aciklama = TextAreaField('Açıklama', validators=[Optional()])
    kategori = SelectField('Kategori', choices=[
        ('genel', 'Genel'),
        ('ariza', 'Arıza'),
        ('bakim', 'Bakım'),
        ('satin_alma', 'Satın Alma'),
        ('egitim', 'Eğitim'),
    ], validators=[DataRequired()])
    oncelik = SelectField('Öncelik', choices=[
        ('dusuk', 'Düşük'),
        ('normal', 'Normal'),
        ('yuksek', 'Yüksek'),
        ('kritik', 'Kritik'),
    ], default='normal', validators=[DataRequired()])
    atanan_id = SelectField('Atanan Kişi', coerce=int, validators=[Optional()])
    sla_saat = IntegerField('SLA Süresi (Saat)', validators=[Optional(), NumberRange(min=1, max=720)],
                            description="Boş bırakılırsa önceliğe göre otomatik atanır.")
    submit = SubmitField('İş Emri Oluştur')


class IsEmriGuncellemeForm(FlaskForm):
    """İş emri durum güncelleme formu."""
    durum = SelectField('Yeni Durum', choices=[
        ('atandi', 'Atandı'),
        ('devam', 'Devam Ediyor'),
        ('tamamlandi', 'Tamamlandı'),
        ('onaylandi', 'Onaylandı'),
        ('iptal', 'İptal'),
    ], validators=[DataRequired()])
    cozum_notu = TextAreaField('Çözüm / Açıklama Notu', validators=[Optional()])
    submit = SubmitField('Durumu Güncelle')


class IsEmriYorumForm(FlaskForm):
    """İş emrine yorum ekleme formu."""
    icerik = TextAreaField('Yorum', validators=[DataRequired(), Length(min=2, max=2000)])
    submit = SubmitField('Yorum Ekle')
