/**
 * FDYS - CRM Harita Modülü
 * Faz 2 - Leaflet.js Entegrasyonu
 * Ortak ve Firma lokasyonlarını harita üzerinde gösterir.
 */

let map;
let markersOrtaklar;
let markersFirmalar;

/**
 * Haritayı başlatır ve verileri çeker
 * @param {string} elementId Haritanın bağlanacağı div ID'si
 * @param {string} apiUrl Verilerin çekileceği API endpoint
 * @param {boolean} isDark Karanlık tema aktif mi?
 */
function initMap(elementId, apiUrl, isDark = false) {
    // 1. Haritayı merkezle (Varsayılan Türkiye geneli veya İstanbul)
    map = L.map(elementId).setView([41.0082, 28.9784], 10);

    // 2. Tile Layer (Harita altlığı) - Karanlık veya Aydınlık temaya göre
    const tileUrl = isDark 
        ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
        : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
        
    L.tileLayer(tileUrl, {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);

    // 3. Cluster Grupları (Çoklu pinleri gruplama)
    markersOrtaklar = L.markerClusterGroup({
        iconCreateFunction: function(cluster) {
            return L.divIcon({ 
                html: '<div><span>' + cluster.getChildCount() + '</span></div>',
                className: 'marker-cluster marker-cluster-small bg-primary bg-opacity-75 text-white fw-bold border border-primary', 
                iconSize: L.point(40, 40) 
            });
        }
    });

    markersFirmalar = L.markerClusterGroup({
        iconCreateFunction: function(cluster) {
            return L.divIcon({ 
                html: '<div><span>' + cluster.getChildCount() + '</span></div>',
                className: 'marker-cluster marker-cluster-small bg-success bg-opacity-75 text-white fw-bold border border-success', 
                iconSize: L.point(40, 40) 
            });
        }
    });

    // 4. İkonlar
    const ortakIcon = L.divIcon({
        className: 'custom-div-icon',
        html: "<div style='background-color:#3b82f6; width:24px; height:24px; border-radius:50%; border:2px solid white; box-shadow:0 0 5px rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center;'><i class='bi bi-person text-white' style='font-size:12px;'></i></div>",
        iconSize: [24, 24],
        iconAnchor: [12, 12],
        popupAnchor: [0, -12]
    });

    const firmaIcon = L.divIcon({
        className: 'custom-div-icon',
        html: "<div style='background-color:#10b981; width:28px; height:28px; border-radius:4px; border:2px solid white; box-shadow:0 0 5px rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center;'><i class='bi bi-building text-white' style='font-size:14px;'></i></div>",
        iconSize: [28, 28],
        iconAnchor: [14, 14],
        popupAnchor: [0, -14]
    });

    // 5. Verileri Çek ve Pinleri Oluştur
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            let bounds = L.latLngBounds();
            let hasPoints = false;

            // Ortaklar
            if (data.ortaklar && data.ortaklar.length > 0) {
                data.ortaklar.forEach(o => {
                    if (o.lat && o.lng) {
                        const marker = L.marker([o.lat, o.lng], {icon: ortakIcon});
                        const popupContent = `
                            <div class="map-popup-header text-primary"><i class="bi bi-person me-1"></i>Ortak: ${o.ad_soyad}</div>
                            <div class="small">
                                <strong>No:</strong> ${o.ortak_no}<br>
                                <strong>Konum:</strong> Blok ${o.blok || '-'} / Daire ${o.daire_no || '-'}<br>
                                <strong>Tip:</strong> ${o.ortak_tipi}<br>
                                <strong>Tel:</strong> ${o.telefon || '-'}
                            </div>
                            <div class="mt-2 text-center">
                                <a href="/crm/ortaklar/${o.id}" class="btn btn-sm btn-outline-primary w-100 py-0" style="font-size:0.75rem;">Detay Görüntüle</a>
                            </div>
                        `;
                        marker.bindPopup(popupContent);
                        markersOrtaklar.addLayer(marker);
                        bounds.extend([o.lat, o.lng]);
                        hasPoints = true;
                    }
                });
                map.addLayer(markersOrtaklar);
            }

            // Firmalar
            if (data.firmalar && data.firmalar.length > 0) {
                data.firmalar.forEach(f => {
                    if (f.lat && f.lng) {
                        const marker = L.marker([f.lat, f.lng], {icon: firmaIcon});
                        const popupContent = `
                            <div class="map-popup-header text-success"><i class="bi bi-building me-1"></i>Firma: ${f.unvan}</div>
                            <div class="small">
                                <strong>Sektör:</strong> ${f.sektor}<br>
                                <strong>Konum:</strong> Blok ${f.blok || '-'} / Daire ${f.daire_no || '-'}<br>
                                <strong>Tel:</strong> ${f.telefon || '-'}
                            </div>
                            <div class="mt-2 text-center">
                                <a href="/crm/firmalar/${f.id}" class="btn btn-sm btn-outline-success w-100 py-0" style="font-size:0.75rem;">Firma Profiline Git</a>
                            </div>
                        `;
                        marker.bindPopup(popupContent);
                        markersFirmalar.addLayer(marker);
                        bounds.extend([f.lat, f.lng]);
                        hasPoints = true;
                    }
                });
                map.addLayer(markersFirmalar);
            }

            // Haritayı pinlere göre odakla
            if (hasPoints) {
                map.fitBounds(bounds, {padding: [50, 50]});
            }
        })
        .catch(error => console.error('Harita veri yükleme hatası:', error));

    // 6. Filtre Kontrollerini Bağla
    document.getElementById('layerOrtaklar').addEventListener('change', function(e) {
        if(e.target.checked) map.addLayer(markersOrtaklar);
        else map.removeLayer(markersOrtaklar);
    });

    document.getElementById('layerFirmalar').addEventListener('change', function(e) {
        if(e.target.checked) map.addLayer(markersFirmalar);
        else map.removeLayer(markersFirmalar);
    });

    document.getElementById('btnSifirla').addEventListener('click', function() {
        let bounds = L.latLngBounds();
        let hasBounds = false;
        
        if (map.hasLayer(markersOrtaklar)) {
            let oBounds = markersOrtaklar.getBounds();
            if(Object.keys(oBounds).length > 0) { bounds.extend(oBounds); hasBounds = true; }
        }
        
        if (map.hasLayer(markersFirmalar)) {
            let fBounds = markersFirmalar.getBounds();
            if(Object.keys(fBounds).length > 0) { bounds.extend(fBounds); hasBounds = true; }
        }
        
        if (hasBounds) {
            map.fitBounds(bounds, {padding: [50, 50]});
        }
    });
}
