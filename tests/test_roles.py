import pytest

def test_yonetici_erisim(auth_client_yonetici):
    """Yöneticinin tüm modüllere erişebildiğini doğrula."""
    # Personel Modülü
    assert auth_client_yonetici.get('/personel/').status_code == 200
    # Makine Modülü
    assert auth_client_yonetici.get('/makine/').status_code == 200
    # Raporlama Modülü
    assert auth_client_yonetici.get('/rapor/').status_code == 200
    # Sistem Ayarları
    assert auth_client_yonetici.get('/admin/').status_code == 200

def test_operator_erisim(auth_client_operator):
    """Operatörün kısıtlı erişimlerini doğrula."""
    # Personel Modülü (Kendisi hariç görmemeli veya liste görmeli)
    assert auth_client_operator.get('/personel/').status_code in [200, 403]
    # Makine modülü görebilir
    assert auth_client_operator.get('/makine/').status_code == 200
    
    # Sistem Ayarlarına girememeli (403 Forbidden)
    res = auth_client_operator.get('/admin/')
    assert res.status_code == 403
    
    # Raporlama modülüne girememeli (Role_required('yonetici'))
    res2 = auth_client_operator.get('/rapor/')
    assert res2.status_code == 403

def test_teknisyen_erisim(auth_client_teknisyen):
    """Teknisyenin bakım ve arızalara erişimini, admin paneline erişemediğini doğrula."""
    # Makine görebilir
    assert auth_client_teknisyen.get('/makine/').status_code == 200
    
    # Admin erişimi yok
    assert auth_client_teknisyen.get('/admin/').status_code == 403
    
    # Rapor erişimi yok
    assert auth_client_teknisyen.get('/rapor/').status_code == 403
