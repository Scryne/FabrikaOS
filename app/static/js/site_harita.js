/**
 * FDYS - Sanayi Sitesi İnteraktif Harita Modülü
 * Faz 8 - Leaflet.js
 */

let map;
let markersOrtaklar;
let markersFirmalar;
let markersTalepler;
let apiEndpoint = '';

/**
 * Haritayı başlatır
 */
function initSiteMap(elementId, apiUrl, isDark = false) {
    apiEndpoint = apiUrl;

    // Haritayı başlat
    map = L.map(elementId).setView([41.0082, 28.9784], 14);

    // Tile Layer
    const tileUrl = isDark 
        ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
        : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
        
    L.tileLayer(tileUrl, {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);

    // Cluster Grupları
    markersOrtaklar = L.markerClusterGroup({
        iconCreateFunction: function(cluster) {
            return L.divIcon({ 
                html: `<div><span>${cluster.getChildCount()}</span></div>`,
                className: 'marker-cluster marker-cluster-small', 
                iconSize: L.point(40, 40) 
            });
        }
    });

    markersFirmalar = L.markerClusterGroup({
        iconCreateFunction: function(cluster) {
            return L.divIcon({ 
                html: `<div><span>${cluster.getChildCount()}</span></div>`,
                className: 'marker-cluster marker-cluster-small', 
                iconSize: L.point(40, 40) 
            });
        }
    });

    markersTalepler = L.markerClusterGroup();

    // Verileri Yükle
    loadMapData();

    // Filtre Eventleri
    document.getElementById('filterBlok').addEventListener('change', loadMapData);
    
    document.getElementById('layerOrtaklar').addEventListener('change', function(e) {
        if(e.target.checked) map.addLayer(markersOrtaklar);
        else map.removeLayer(markersOrtaklar);
    });

    document.getElementById('layerFirmalar').addEventListener('change', function(e) {
        if(e.target.checked) map.addLayer(markersFirmalar);
        else map.removeLayer(markersFirmalar);
    });

    document.getElementById('layerTalepler').addEventListener('change', function(e) {
        if(e.target.checked) map.addLayer(markersTalepler);
        else map.removeLayer(markersTalepler);
    });

    document.getElementById('btnOdakla').addEventListener('click', function() {
        let bounds = L.latLngBounds();
        let hasBounds = false;
        
        if (map.hasLayer(markersOrtaklar) && Object.keys(markersOrtaklar.getBounds()).length > 0) { 
            bounds.extend(markersOrtaklar.getBounds()); hasBounds = true; 
        }
        if (map.hasLayer(markersFirmalar) && Object.keys(markersFirmalar.getBounds()).length > 0) { 
            bounds.extend(markersFirmalar.getBounds()); hasBounds = true; 
        }
        
        if (hasBounds) {
            map.fitBounds(bounds, {padding: [50, 50]});
        }
    });
}

function loadMapData() {
    const blok = document.getElementById('filterBlok').value;
    const url = `${apiEndpoint}?blok=${encodeURIComponent(blok)}`;

    markersOrtaklar.clearLayers();
    markersFirmalar.clearLayers();
    markersTalepler.clearLayers();

    fetch(url)
        .then(res => res.json())
        .then(data => {
            let bounds = L.latLngBounds();
            let hasPoints = false;

            // Ortaklar
            if (data.ortaklar && data.ortaklar.length > 0) {
                data.ortaklar.forEach(o => {
                    if (o.lat && o.lng) {
                        const marker = createMarker(o, 'ortak');
                        markersOrtaklar.addLayer(marker);
                        bounds.extend([o.lat, o.lng]);
                        hasPoints = true;
                    }
                });
                if(document.getElementById('layerOrtaklar').checked) map.addLayer(markersOrtaklar);
            }

            // Firmalar
            if (data.firmalar && data.firmalar.length > 0) {
                data.firmalar.forEach(f => {
                    if (f.lat && f.lng) {
                        const marker = createMarker(f, 'firma');
                        markersFirmalar.addLayer(marker);
                        bounds.extend([f.lat, f.lng]);
                        hasPoints = true;
                    }
                });
                if(document.getElementById('layerFirmalar').checked) map.addLayer(markersFirmalar);
            }

            // Talepler
            if (data.talepler && data.talepler.length > 0) {
                // Taleplerin konum_bilgi'sinden (Blok A, No 1 gibi) koordinat çıkarımı
                // Bu örnekte basitleştirilmiş bir eşleştirme kullanılmıştır (gerçekte DB'de lat/lng tutulmalıdır).
                // API şimdilik talepler tablosunda koordinat tutmadığından bu kısmı atlıyoruz
                // İleride eklendiğinde aynı mantıkla eklenecektir.
            }

            if (hasPoints && blok === '') {
                map.fitBounds(bounds, {padding: [50, 50]});
            } else if (hasPoints) {
                map.fitBounds(bounds, {padding: [20, 20], maxZoom: 17});
            }
        })
        .catch(err => console.error('Harita veri hatası:', err));
}

function createMarker(item, type) {
    // Sözleşme durumuna göre renk kodu belirle
    let borderColor = '#6c757d'; // gray
    if (item.sozlesme_renk === 'green') borderColor = '#198754';
    else if (item.sozlesme_renk === 'yellow') borderColor = '#ffc107';
    else if (item.sozlesme_renk === 'red') borderColor = '#dc3545';

    let iconHtml = '';
    let iconSize = [24, 24];

    if (type === 'ortak') {
        iconHtml = `<div style='background-color:#3b82f6; width:24px; height:24px; border-radius:50%; border:3px solid ${borderColor}; box-shadow:0 0 5px rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center;'><i class='bi bi-person text-white' style='font-size:12px;'></i></div>`;
    } else {
        iconSize = [28, 28];
        iconHtml = `<div style='background-color:#10b981; width:28px; height:28px; border-radius:4px; border:3px solid ${borderColor}; box-shadow:0 0 5px rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center;'><i class='bi bi-building text-white' style='font-size:14px;'></i></div>`;
    }

    const icon = L.divIcon({
        className: 'custom-div-icon',
        html: iconHtml,
        iconSize: iconSize,
        iconAnchor: [iconSize[0]/2, iconSize[1]/2],
        popupAnchor: [0, -iconSize[1]/2]
    });

    const marker = L.marker([item.lat, item.lng], {
        icon: icon,
        draggable: true // Yetkili kontrolü yapılabilir, şimdilik aktif
    });

    const title = type === 'ortak' ? item.ad_soyad : item.unvan;
    const badgeColor = type === 'ortak' ? 'primary' : 'success';
    const linkUrl = type === 'ortak' ? `/crm/ortaklar/${item.id}` : `/crm/firmalar/${item.id}`;

    let sozlesmeBadge = '';
    if (item.sozlesme_sayisi > 0) {
        if (item.sozlesme_renk === 'green') sozlesmeBadge = '<span class="badge bg-success mt-2 d-block">Aktif Sözleşme</span>';
        else if (item.sozlesme_renk === 'yellow') sozlesmeBadge = '<span class="badge bg-warning text-dark mt-2 d-block">Sözleşme Yaklaşıyor</span>';
        else if (item.sozlesme_renk === 'red') sozlesmeBadge = '<span class="badge bg-danger mt-2 d-block">Sözleşme Bitti/İptal</span>';
    } else {
        sozlesmeBadge = '<span class="badge bg-secondary mt-2 d-block">Sözleşme Yok</span>';
    }

    const popupContent = `
        <div class="map-popup-header text-${badgeColor}">
            <i class="bi bi-${type === 'ortak' ? 'person' : 'building'} me-1"></i>${title}
        </div>
        <div class="small">
            <strong>Konum:</strong> ${item.konum}<br>
            <strong>Tel:</strong> ${item.telefon || '-'}<br>
            ${item.m2 ? `<strong>Alan:</strong> ${item.m2} m²<br>` : ''}
            ${sozlesmeBadge}
        </div>
        <div class="mt-2 text-center">
            <a href="${linkUrl}" class="btn btn-sm btn-outline-${badgeColor} w-100 py-0" style="font-size:0.75rem;">Detay Görüntüle</a>
        </div>
    `;

    marker.bindPopup(popupContent);

    // Sürükle-bırak koordinat güncelleme
    marker.on('dragend', function(e) {
        const position = marker.getLatLng();
        
        fetch('/sanayi-harita/api/koordinat-guncelle', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            },
            body: JSON.stringify({
                tip: type,
                id: item.id,
                lat: position.lat,
                lng: position.lng
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                if(typeof showToast === 'function') showToast('Başarılı', data.message, 'success');
            } else {
                // Hata varsa geri al
                marker.setLatLng([item.lat, item.lng]);
                if(typeof showToast === 'function') showToast('Hata', data.error || 'Güncelleme hatası', 'danger');
            }
        })
        .catch(err => {
            marker.setLatLng([item.lat, item.lng]);
            console.error(err);
        });
    });

    return marker;
}
