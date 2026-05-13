"""
FDYS — Makine Modülü Form Tanımları (Faz 3 — Profesyonel)
"""

from flask_wtf import FlaskForm
from wtforms import (StringField, IntegerField, DecimalField, DateField,
                     SelectField, SubmitField, TextAreaField, DateTimeField)
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from datetime import datetime, timezone


class MakineForm(FlaskForm):
    ad = StringField('Makine Adı', validators=[DataRequired(), Length(min=2, max=100)])
    kod = StringField('Makine Kodu', validators=[DataRequired(), Length(min=2, max=50)])
    model = StringField('Model', validators=[Optional(), Length(max=100)])
    marka = StringField('Marka', validators=[Optional(), Length(max=100)])
    teorik_kapasite = IntegerField('Teorik Kapasite (adet/saat)',
                                   validators=[DataRequired(), NumberRange(min=1)])
    hedef_oee = DecimalField('Hedef OEE (%)',
                              validators=[DataRequired(), NumberRange(min=0, max=100)], default=85.00)
    satin_alma_tarihi = DateField('Satın Alma Tarihi', format='%Y-%m-%d',
                                  validators=[DataRequired()], default=lambda: datetime.now(timezone.utc))
    garantisi_bitis = DateField('Garanti Bitiş Tarihi', format='%Y-%m-%d', validators=[Optional()])
    periyodik_bakim_gun = IntegerField('Bakım Periyodu (Gün)',
                                       validators=[DataRequired(), NumberRange(min=1)], default=90)
    lokasyon = StringField('Lokasyon', validators=[Optional(), Length(max=100)])
    durum = SelectField('Durum', choices=[
        ('aktif', 'Aktif'), ('arizali', 'Arızalı'), ('bakimda', 'Bakımda')
    ], default='aktif')
    submit = SubmitField('Kaydet')


class UretimGirisForm(FlaskForm):
    tarih = DateField('Üretim Tarihi', format='%Y-%m-%d',
                      validators=[DataRequired()], default=lambda: datetime.now(timezone.utc))
    vardiya = SelectField('Vardiya', choices=[
        ('sabah', 'Sabah (06:00–14:00)'),
        ('ogleden_sonra', 'Öğleden Sonra (14:00–22:00)'),
        ('gece', 'Gece (22:00–06:00)')
    ], validators=[DataRequired()])
    calisan_id = SelectField('Operatör', coerce=int, validators=[DataRequired()])
    planlanan_sure_dk = IntegerField('Planlanan Süre (Dakika)',
                                     validators=[DataRequired(), NumberRange(min=1)], default=480)
    gercek_calisma_dk = IntegerField('Gerçek Çalışma Süresi (Dakika)',
                                     validators=[DataRequired(), NumberRange(min=0)])
    gercek_uretim = IntegerField('Gerçek Üretim (Adet)',
                                  validators=[DataRequired(), NumberRange(min=0)])
    hatali_uretim = IntegerField('Hatalı Üretim (Adet)',
                                  validators=[DataRequired(), NumberRange(min=0)], default=0)
    notlar = TextAreaField('Notlar', validators=[Optional()])
    submit = SubmitField('Üretim Kaydet')


class ArizaBildirimForm(FlaskForm):
    ariza_turu = StringField('Arıza Türü', validators=[DataRequired(), Length(max=50)])
    oncelik = SelectField('Öncelik', choices=[
        ('dusuk', 'Düşük'), ('normal', 'Normal'), ('yuksek', 'Yüksek'), ('kritik', 'Kritik')
    ], default='normal')
    aciklama = TextAreaField('Arıza Açıklaması', validators=[DataRequired()])
    submit = SubmitField('Arıza Bildir')


class ArizaCozumForm(FlaskForm):
    cozum = TextAreaField('Çözüm Detayı', validators=[DataRequired()])
    durum = SelectField('Durum', choices=[
        ('kapali', 'Çözüldü/Kapalı'), ('beklemede', 'Yedek Parça Bekleniyor')
    ], default='kapali')
    submit = SubmitField('Kaydı Güncelle')


class BakimKaydiForm(FlaskForm):
    bakim_turu = SelectField('Bakım Türü', choices=[
        ('periyodik', 'Periyodik Bakım'),
        ('korektif', 'Korektif (Arıza Sonrası)'),
        ('prediktif', 'Prediktif (Tahmine Dayalı)'),
        ('revizyon', 'Genel Revizyon'),
    ], validators=[DataRequired()])
    tarih = DateField('Bakım Tarihi', format='%Y-%m-%d',
                      validators=[DataRequired()], default=lambda: datetime.now(timezone.utc))
    yapilan_islem = TextAreaField('Yapılan İşlemler', validators=[DataRequired()])
    sure_dk = IntegerField('Bakım Süresi (Dakika)',
                           validators=[Optional(), NumberRange(min=1)])
    maliyet = DecimalField('Maliyet (₺)',
                           validators=[Optional(), NumberRange(min=0)], places=2)
    notlar = TextAreaField('Notlar', validators=[Optional()])
    submit = SubmitField('Bakım Kaydı Oluştur')


class DurusKaydiForm(FlaskForm):
    baslangic = DateTimeField('Başlangıç', format='%Y-%m-%dT%H:%M',
                              validators=[DataRequired()], default=lambda: datetime.now(timezone.utc))
    bitis = DateTimeField('Bitiş', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    neden = StringField('Duruş Nedeni', validators=[DataRequired(), Length(max=100)])
    kategori = SelectField('Kategori (Altı Büyük Kayıp)', choices=[
        ('ariza', '1. Ekipman Arızası'),
        ('ayar', '2. Ayar ve Setup'),
        ('kisa_durus', '3. Küçük Duraklamalar'),
        ('hiz_kaybi', '4. Düşük Hız'),
        ('kalite', '5. Kalite Hataları'),
        ('baslangic', '6. Başlangıç Kayıpları')
    ], validators=[DataRequired()])
    aciklama = TextAreaField('Açıklama', validators=[Optional()])
    submit = SubmitField('Duruşu Kaydet')
