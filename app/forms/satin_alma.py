"""
FDYS — Satın Alma Modülü Formları
Faz 7

Satın alma talebi, sipariş ve teklif karşılaştırma formları.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SelectField,
    DecimalField, IntegerField, DateField,
    BooleanField, HiddenField
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange


class SatinAlmaTalebiForm(FlaskForm):
    """Satın alma talebi oluşturma ve düzenleme formu."""

    malzeme_hizmet = SelectField(
        'Tür',
        choices=[
            ('malzeme', 'Malzeme'),
            ('hizmet', 'Hizmet'),
        ],
        validators=[DataRequired(message='Tür seçimi zorunludur.')]
    )
    kalem_adi = StringField(
        'Kalem Adı / Açıklaması',
        validators=[DataRequired(message='Kalem adı zorunludur.'), Length(max=300)],
        description='Satın alınacak malzeme veya hizmetin kısa tanımı'
    )
    miktar = DecimalField(
        'Miktar',
        validators=[DataRequired(message='Miktar zorunludur.'), NumberRange(min=0.01)],
        places=2
    )
    birim = SelectField(
        'Birim',
        choices=[
            ('adet', 'Adet'),
            ('kg', 'Kilogram'),
            ('litre', 'Litre'),
            ('metre', 'Metre'),
            ('paket', 'Paket'),
            ('kutu', 'Kutu'),
            ('ton', 'Ton'),
            ('set', 'Set'),
            ('takım', 'Takım'),
            ('diger', 'Diğer'),
        ],
        validators=[DataRequired()]
    )
    tahmini_birim_fiyat = DecimalField(
        'Tahmini Birim Fiyat (₺)',
        validators=[Optional(), NumberRange(min=0)],
        places=2,
        description='Yaklaşık birim fiyat bilgisi'
    )
    departman = StringField(
        'Departman',
        validators=[Optional(), Length(max=100)],
        description='Talebi oluşturan departman'
    )
    aciliyet = SelectField(
        'Aciliyet',
        choices=[
            ('normal', 'Normal'),
            ('acil', 'Acil'),
        ],
        validators=[DataRequired()]
    )
    aciklama = TextAreaField(
        'Açıklama',
        validators=[Optional(), Length(max=2000)],
        description='Detaylı açıklama ve teknik özellikler'
    )
    gerekce = TextAreaField(
        'Satın Alma Gerekçesi',
        validators=[Optional(), Length(max=1000)],
        description='Neden bu satın alma gerekli?'
    )
    istenen_teslim_tarihi = DateField(
        'İstenen Teslim Tarihi',
        format='%Y-%m-%d',
        validators=[Optional()],
        description='En geç ne zaman teslim alınması isteniyor?'
    )
    tedarikci_id = SelectField(
        'Tercih Edilen Tedarikçi',
        coerce=int,
        validators=[Optional()],
        description='Bilinen bir tedarikçi varsa seçin (opsiyonel)'
    )


class SatinAlmaSiparisForm(FlaskForm):
    """Satın alma siparişi oluşturma formu."""

    tedarikci_id = SelectField(
        'Tedarikçi',
        coerce=int,
        validators=[DataRequired(message='Tedarikçi seçimi zorunludur.')]
    )
    birim_fiyat = DecimalField(
        'Birim Fiyat (₺)',
        validators=[DataRequired(message='Birim fiyat zorunludur.'), NumberRange(min=0.01)],
        places=2
    )
    miktar = DecimalField(
        'Miktar',
        validators=[DataRequired(message='Miktar zorunludur.'), NumberRange(min=0.01)],
        places=2
    )
    kdv_orani = DecimalField(
        'KDV Oranı (%)',
        validators=[Optional(), NumberRange(min=0, max=100)],
        places=2,
        default=20
    )
    beklenen_teslim = DateField(
        'Beklenen Teslim Tarihi',
        format='%Y-%m-%d',
        validators=[Optional()]
    )
    fatura_no = StringField(
        'Fatura No',
        validators=[Optional(), Length(max=50)]
    )
    notlar = TextAreaField(
        'Sipariş Notları',
        validators=[Optional(), Length(max=2000)]
    )

    # Hidden field for talep_id
    talep_id = HiddenField()


class TeklifKarsilastirmaForm(FlaskForm):
    """Teklif karşılaştırma formu — tek bir tedarikçi teklifi eklemek için."""

    tedarikci_id = SelectField(
        'Tedarikçi',
        coerce=int,
        validators=[DataRequired(message='Tedarikçi seçimi zorunludur.')]
    )
    birim_fiyat = DecimalField(
        'Birim Fiyat (₺)',
        validators=[DataRequired(message='Birim fiyat zorunludur.'), NumberRange(min=0.01)],
        places=2
    )
    toplam_fiyat = DecimalField(
        'Toplam Fiyat (₺)',
        validators=[Optional(), NumberRange(min=0)],
        places=2,
        description='Miktar × birim fiyat + ek masraflar'
    )
    teslimat_suresi = IntegerField(
        'Teslimat Süresi (Gün)',
        validators=[Optional(), NumberRange(min=0)],
        description='Gün cinsinden tahmini teslimat süresi'
    )
    garanti_suresi = IntegerField(
        'Garanti Süresi (Ay)',
        validators=[Optional(), NumberRange(min=0)],
        description='Ay cinsinden garanti süresi'
    )
    notlar = TextAreaField(
        'Teklif Notları',
        validators=[Optional(), Length(max=1000)],
        description='Ödeme koşulları, kargo dahil/hariç vb.'
    )


class TalepRedForm(FlaskForm):
    """Talep reddetme formu — red nedeni zorunlu."""

    red_nedeni = TextAreaField(
        'Red Nedeni',
        validators=[DataRequired(message='Red nedeni zorunludur.'), Length(max=500)]
    )


class TeslimAlmaForm(FlaskForm):
    """Sipariş teslim alma formu."""

    gercek_teslim = DateField(
        'Teslim Tarihi',
        format='%Y-%m-%d',
        validators=[DataRequired(message='Teslim tarihi zorunludur.')]
    )
    fatura_no = StringField(
        'Fatura No',
        validators=[Optional(), Length(max=50)]
    )
    notlar = TextAreaField(
        'Teslim Alma Notları',
        validators=[Optional(), Length(max=1000)]
    )
