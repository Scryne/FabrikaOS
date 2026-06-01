"""
FDYS — Talep & İş Takip Formları
Faz 4 — WTForms tanımları
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SelectField, BooleanField,
    HiddenField, IntegerField, DecimalField, DateField
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange

from app.models.talep import Talep


class TalepForm(FlaskForm):
    """Talep oluşturma/düzenleme formu."""
    baslik = StringField('Talep Başlığı', validators=[
        DataRequired(message='Başlık zorunludur.'),
        Length(min=5, max=200, message='Başlık 5-200 karakter arasında olmalıdır.')
    ])
    aciklama = TextAreaField('Açıklama', validators=[
        Optional(),
        Length(max=5000, message='Açıklama en fazla 5000 karakter olabilir.')
    ])
    kategori = SelectField('Kategori', choices=[
        ('teknik_hizmet', 'Teknik Hizmet'),
        ('guvenlik', 'Güvenlik'),
        ('idari', 'İdari İşler'),
        ('temizlik', 'Temizlik'),
        ('otopark', 'Otopark'),
        ('ortak_alan', 'Ortak Alan'),
        ('elektrik', 'Elektrik'),
        ('mekanik', 'Mekanik / Tesisat'),
        ('diger', 'Diğer'),
    ], validators=[DataRequired()])
    alt_kategori = StringField('Alt Kategori', validators=[
        Optional(),
        Length(max=100)
    ])
    oncelik = SelectField('Öncelik', choices=[
        ('normal', 'Normal'),
        ('dusuk', 'Düşük'),
        ('yuksek', 'Yüksek'),
        ('acil', 'Acil'),
    ], validators=[DataRequired()], default='normal')
    konum_bilgi = StringField('Konum (Blok / Kat / Daire)', validators=[
        Optional(),
        Length(max=200)
    ])
    sms_bildirim = BooleanField('SMS ile bildirim gönder', default=False)
    eposta_bildirim = BooleanField('E-posta ile bildirim gönder', default=True)


class TalepYonlendirmeForm(FlaskForm):
    """Talep yönlendirme formu."""
    talep_id = HiddenField('Talep ID', validators=[DataRequired()])
    atanan_departman = SelectField('Departman', choices=[
        ('teknik', 'Teknik'),
        ('guvenlik', 'Güvenlik'),
        ('idari', 'İdari'),
        ('yonetim', 'Yönetim'),
    ], validators=[DataRequired()])
    atanan_id = SelectField('Sorumlu Kişi', coerce=int, choices=[], validators=[Optional()])
    aciklama = TextAreaField('Not', validators=[
        Optional(),
        Length(max=500)
    ])


class TalepDurumForm(FlaskForm):
    """Talep durum güncelleme formu."""
    talep_id = HiddenField('Talep ID', validators=[DataRequired()])
    yeni_durum = SelectField('Yeni Durum', choices=[
        ('acik', 'Açık'),
        ('yonlendirildi', 'Yönlendirildi'),
        ('devam', 'Devam Ediyor'),
        ('tamamlandi', 'Tamamlandı'),
        ('kapandi', 'Kapandı'),
        ('reddedildi', 'Reddedildi'),
    ], validators=[DataRequired()])
    cozum_notu = TextAreaField('Çözüm Notu', validators=[
        Optional(),
        Length(max=2000)
    ])
    aciklama = TextAreaField('Açıklama', validators=[
        Optional(),
        Length(max=500)
    ])


class TalepYorumForm(FlaskForm):
    """Talebe yorum ekleme formu."""
    talep_id = HiddenField('Talep ID', validators=[DataRequired()])
    yorum = TextAreaField('Yorum', validators=[
        DataRequired(message='Yorum zorunludur.'),
        Length(min=3, max=2000, message='Yorum 3-2000 karakter arasında olmalıdır.')
    ])


class BorcForm(FlaskForm):
    """Borç kaydı oluşturma formu."""
    ilgili_tip = SelectField('İlgili Tip', choices=[
        ('ortak', 'Ortak'),
        ('firma', 'Firma'),
    ], validators=[DataRequired()])
    ilgili_id = SelectField('İlgili Kişi/Firma', coerce=int, choices=[], validators=[DataRequired()])
    borc_turu = SelectField('Borç Türü', choices=[
        ('aidat', 'Aidat'),
        ('kira', 'Kira'),
        ('ceza', 'Ceza'),
        ('bakim', 'Bakım Ücreti'),
        ('diger', 'Diğer'),
    ], validators=[DataRequired()])
    tutar = DecimalField('Tutar (TL)', validators=[
        DataRequired(message='Tutar zorunludur.'),
        NumberRange(min=0.01, message='Tutar 0\'dan büyük olmalıdır.')
    ], places=2)
    aciklama = StringField('Açıklama', validators=[Optional(), Length(max=300)])
    donem = StringField('Dönem (Ay-Yıl)', validators=[Optional(), Length(max=20)])
    son_odeme_tarihi = DateField('Son Ödeme Tarihi', validators=[Optional()], format='%Y-%m-%d')


class TahsilatForm(FlaskForm):
    """Tahsilat (ödeme) kayıt formu."""
    borc_id = HiddenField('Borç ID', validators=[DataRequired()])
    tutar = DecimalField('Ödeme Tutarı (TL)', validators=[
        DataRequired(message='Tutar zorunludur.'),
        NumberRange(min=0.01, message='Tutar 0\'dan büyük olmalıdır.')
    ], places=2)
    odeme_turu = SelectField('Ödeme Türü', choices=[
        ('nakit', 'Nakit'),
        ('havale', 'Havale / EFT'),
        ('kredi_karti', 'Kredi Kartı'),
        ('pos', 'POS'),
        ('cevrimici', 'Çevrimiçi Ödeme'),
    ], validators=[DataRequired()])
    makbuz_no = StringField('Makbuz No', validators=[Optional(), Length(max=50)])
    aciklama = StringField('Açıklama', validators=[Optional(), Length(max=300)])


class MemnuniyetForm(FlaskForm):
    """Memnuniyet puanı formu."""
    talep_id = HiddenField('Talep ID', validators=[DataRequired()])
    puan = IntegerField('Memnuniyet Puanı (1-5)', validators=[
        DataRequired(),
        NumberRange(min=1, max=5, message='Puan 1-5 arasında olmalıdır.')
    ])
    yorum = TextAreaField('Görüşleriniz', validators=[
        Optional(),
        Length(max=500)
    ])
