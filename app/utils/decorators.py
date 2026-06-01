"""
FDYS — Yardımcı Dekoratörler (Faz 0 — Genişletilmiş)

@role_required:          Rol bazlı erişim kontrolü
@modul_erisim_gerekli:   Granüler modül erişim kontrolü (okuma/yazma/silme)
@log_action:             Denetim izi kaydı
"""

import logging
from functools import wraps
from flask import abort, request, flash, redirect, url_for
from flask_login import current_user


def role_required(*roller):
    """
    Belirtilen rollerden birine sahip olmayan kullanıcıların erişimini engeller.

    Kullanım:
        @role_required('yonetici')
        @role_required('yonetici', 'teknisyen')
        @role_required('yonetici', 'ik_uzmani', 'isg_uzmani')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Bu sayfaya erişmek için giriş yapmanız gerekiyor.', 'warning')
                return redirect(url_for('auth.login'))

            if current_user.rol not in roller:
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def modul_erisim_gerekli(modul_adi, izin_turu=None):
    """
    Kullanıcının belirtilen modüle (ve opsiyonel izin türüne) erişimi
    olup olmadığını kontrol eder. Yöneticiler tüm modüllere otomatik erişir.

    Granüler kullanım:
        @modul_erisim_gerekli('crm', 'yazma')   # CRM yazma izni gerekli
        @modul_erisim_gerekli('crm', 'silme')   # CRM silme izni gerekli
        @modul_erisim_gerekli('crm', 'okuma')   # CRM okuma izni gerekli

    Basit kullanım (geriye dönük uyumlu):
        @modul_erisim_gerekli('personel')        # Herhangi bir personel erişimi
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Bu sayfaya erişmek için giriş yapmanız gerekiyor.', 'warning')
                return redirect(url_for('auth.login'))

            if not current_user.modul_erisim_var_mi(modul_adi, izin_turu):
                izin_mesaji = f' ({izin_turu})' if izin_turu else ''
                flash(f'Bu modüle{izin_mesaji} erişim yetkiniz bulunmuyor.', 'danger')
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def yazma_izni_gerekli(modul_adi):
    """
    Belirtilen modülde yazma izni olup olmadığını kontrol eden kısayol dekoratör.

    Kullanım:
        @yazma_izni_gerekli('crm')
    """
    return modul_erisim_gerekli(modul_adi, 'yazma')


def silme_izni_gerekli(modul_adi):
    """
    Belirtilen modülde silme izni olup olmadığını kontrol eden kısayol dekoratör.

    Kullanım:
        @silme_izni_gerekli('personel')
    """
    return modul_erisim_gerekli(modul_adi, 'silme')


def log_action(islem_adi):
    """
    Denetim izi kaydı oluşturur. Tüm veri değişiklikleri loglanır.

    Kullanım:
        @log_action('Çalışan Ekleme')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            result = f(*args, **kwargs)

            try:
                from app.extensions import db
                from app.models.kullanici import DenetimIzi

                log = DenetimIzi(
                    kullanici_id=current_user.id if current_user.is_authenticated else None,
                    islem=islem_adi,
                    tablo=f.__name__,
                    ip_adresi=request.remote_addr,
                    detay=f"Rota: {request.path}, Metod: {request.method}"
                )
                db.session.add(log)
                db.session.commit()
            except Exception as e:
                logging.getLogger(__name__).warning(f"Denetim izi kaydı başarısız: {e}")

            return result
        return decorated_function
    return decorator
