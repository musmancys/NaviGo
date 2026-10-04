/**
 * NaviGo Interactive Map Controller (Leaflet.js + OpenStreetMap)
 * Replaces fake CSS map with real spatial layers, category filters, and "What's Around Me?".
 */

let leafletMap = null;
let markersGroup = null;
let userLocationMarker = null;
let loadedPlaces = [];
let activeMarkerId = null;

const CATEGORY_COLORS = {
  attraction: '#13B8A6',
  hotel: '#4DA3FF',
  restaurant: '#F59E0B',
  fuel: '#0B1F33',
  hospital: '#EF4444',
  atm: '#64748B'
};

function initExploreMap() {
  const mapContainer = document.getElementById('mapArea');
  if (!mapContainer) return;

  // Clear static SVG overlays from fake map
  const svgs = mapContainer.querySelectorAll('svg.map-roads, svg.map-river');
  svgs.forEach(s => s.remove());

  if (!leafletMap) {
    // Center at Northern Pakistan (Kaghan/Naran/Hunza corridor)
    leafletMap = L.map('mapArea', {
      zoomControl: false,
      attributionControl: true
    }).setView([35.15, 73.85], 8);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '© OpenStreetMap contributors | NaviGo'
    }).addTo(leafletMap);

    markersGroup = L.layerGroup().addTo(leafletMap);

    // Wire up custom zoom buttons in UI
    const zoomInBtn = document.querySelector('.map-zoom button:first-child');
    if (zoomInBtn) zoomInBtn.onclick = () => leafletMap.zoomIn();

    const zoomOutBtn = document.querySelector('.map-zoom button:last-child');
    if (zoomOutBtn) zoomOutBtn.onclick = () => leafletMap.zoomOut();
  }

  // Ensure map sizes correctly when tab becomes active
  setTimeout(() => {
    leafletMap.invalidateSize();
  }, 200);

  fetchAndRenderPlaces();
}
window.initExploreMap = initExploreMap;

async function fetchAndRenderPlaces(category = 'all', searchQuery = '') {
  try {
    const params = {};
    if (category && category !== 'all') params.type = category;
    if (searchQuery) params.search = searchQuery;

    const places = await api.get('/places', params);
    loadedPlaces = places;
    state.places = places;

    renderMapMarkers(places);
    renderPlacesList(places);
  } catch (err) {
    console.error("Failed to load map places:", err);
    toast("Could not load places data");
  }
}

function createMarkerIcon(place, isActive = false) {
  const color = CATEGORY_COLORS[place.place_type] || '#13B8A6';
  const html = `
    <div style="
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      border-radius: 999px;
      background: ${isActive ? color : 'white'};
      color: ${isActive ? 'white' : '#102A43'};
      border: 2px solid ${color};
      box-shadow: 0 4px 16px rgba(11,31,51,0.22);
      font-size: 11.5px;
      font-weight: 800;
      white-space: nowrap;
      transform: translate(-50%, -100%);
      cursor: pointer;
    ">
      <span>${place.icon || '📍'}</span>
      <span>${api.sanitize(place.name)}</span>
    </div>
  `;

  return L.divIcon({
    html: html,
    className: 'custom-navigo-marker',
    iconSize: [0, 0]
  });
}

function renderMapMarkers(places) {
  if (!markersGroup) return;
  markersGroup.clearLayers();

  const bounds = [];

  places.forEach(p => {
    if (!p.latitude || !p.longitude) return;

    const latLng = [p.latitude, p.longitude];
    bounds.push(latLng);

    const marker = L.marker(latLng, {
      icon: createMarkerIcon(p, activeMarkerId === p.id)
    });

    const popupContent = `
      <div style="font-family:'Inter',sans-serif;padding:6px;max-width:240px;">
        <div style="font-weight:800;font-size:14px;color:#0B1F33;margin-bottom:4px;">${p.icon || ''} ${api.sanitize(p.name)}</div>
        <div style="font-size:11.5px;color:#64748B;margin-bottom:6px;">📍 ${api.sanitize(p.address || p.destination_slug)}</div>
        <p style="font-size:12px;color:#102A43;line-height:1.4;margin-bottom:8px;">${api.sanitize(p.description || '')}</p>
        <div style="display:flex;justify-content:space-between;align-items:center;font-size:12px;">
          <strong>⭐ ${p.rating || 4.5}</strong>
          <span style="color:#059669;font-weight:700;">${api.sanitize(p.price_level || '')}</span>
        </div>
        ${p.contact_phone ? `<div style="margin-top:6px;font-size:11px;color:#2563EB;">📞 ${api.sanitize(p.contact_phone)}</div>` : ''}
      </div>
    `;

    marker.bindPopup(popupContent);

    marker.on('click', () => {
      selectPlace(p.id, false);
    });

    markersGroup.addLayer(marker);
  });

  if (bounds.length > 0 && !userLocationMarker) {
    leafletMap.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 });
  }
}

function renderPlacesList(places) {
  const listContainer = document.getElementById('placesList');
  if (!listContainer) return;

  if (places.length === 0) {
    listContainer.innerHTML = '<div class="place-item"><p style="color:var(--muted)">No places match your search filter.</p></div>';
    return;
  }

  listContainer.innerHTML = places.map(p => `
    <div class="place-item ${activeMarkerId === p.id ? 'active' : ''}" id="place-item-${p.id}" onclick="selectPlace('${p.id}', true)">
      <div class="place-icon" style="color:${CATEGORY_COLORS[p.place_type] || '#13B8A6'};">
        ${p.icon || '📍'}
      </div>
      <div style="flex:1;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <h4>${api.sanitize(p.name)}</h4>
          ${p.distance_km !== null && p.distance_km !== undefined ? `<span style="font-size:11px;font-weight:700;color:#2563EB;">${p.distance_km} km</span>` : ''}
        </div>
        <div class="loc">📍 ${api.sanitize(p.address || p.destination_slug)}</div>
        <p>${api.sanitize(p.description || '')}</p>
        <div style="display:flex;gap:12px;margin-top:6px;font-size:12px;font-weight:600;">
          <span>⭐ ${p.rating || 4.5}</span>
          <span style="color:#059669;">${api.sanitize(p.price_level || '')}</span>
        </div>
      </div>
    </div>
  `).join('');
}

function selectPlace(placeId, shouldPan = true) {
  activeMarkerId = placeId;
  const place = loadedPlaces.find(p => p.id === placeId);
  if (!place) return;

  // Highlight list item
  document.querySelectorAll('.place-item').forEach(el => el.classList.remove('active'));
  const targetItem = document.getElementById(`place-item-${placeId}`);
  if (targetItem) {
    targetItem.classList.add('active');
    targetItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  // Pan map and open popup
  if (leafletMap && shouldPan && place.latitude && place.longitude) {
    leafletMap.flyTo([place.latitude, place.longitude], 13, { duration: 0.8 });
  }
}
window.selectPlace = selectPlace;

// Category Filter Chip Click Handler
let currentCategory = 'all';
function setCategory(btn) {
  document.querySelectorAll('#categoryChips .chip').forEach(c => c.classList.remove('active'));
  btn.classList.add('active');
  currentCategory = btn.getAttribute('data-cat') || 'all';

  const searchQuery = document.getElementById('searchInput')?.value.trim() || '';
  fetchAndRenderPlaces(currentCategory, searchQuery);
}
window.setCategory = setCategory;

// Search Input Handler with Debounce
let searchDebounce = null;
function filterPlaces() {
  clearTimeout(searchDebounce);
  searchDebounce = setTimeout(() => {
    const q = document.getElementById('searchInput')?.value.trim() || '';
    fetchAndRenderPlaces(currentCategory, q);
  }, 250);
}
window.filterPlaces = filterPlaces;

// "What's Around Me?" Geolocation Feature
async function locateUserAroundMe() {
  toast("Locating your coordinates...");

  function onLocationSuccess(position) {
    const lat = position.coords.latitude;
    const lng = position.coords.longitude;
    showNearbyLocation(lat, lng, "Your Current Location");
  }

  function onLocationError() {
    toast("Using default Northern Pakistan location (Naran)");
    // Default to Naran Center for desktop demo
    showNearbyLocation(34.9089, 73.6528, "Naran Center (Demo Geolocation)");
  }

  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(onLocationSuccess, onLocationError, { timeout: 6000 });
  } else {
    onLocationError();
  }
}
window.locateUserAroundMe = locateUserAroundMe;

async function showNearbyLocation(lat, lng, label) {
  if (!leafletMap) initExploreMap();

  if (userLocationMarker) {
    leafletMap.removeLayer(userLocationMarker);
  }

  // Add blue pulsing marker for user
  userLocationMarker = L.circleMarker([lat, lng], {
    radius: 10,
    fillColor: '#2563EB',
    color: '#FFFFFF',
    weight: 3,
    opacity: 1,
    fillOpacity: 0.85
  }).addTo(leafletMap);

  userLocationMarker.bindPopup(`<strong>📍 ${label}</strong><br><small>Emergency Services Active</small>`).openPopup();
  leafletMap.flyTo([lat, lng], 11, { duration: 1.2 });

  // Fetch nearby places from API
  try {
    const nearby = await api.get('/places/nearby', { lat, lng, radius_km: 40 });
    loadedPlaces = nearby;
    renderMapMarkers(nearby);

    // Prepend emergency contacts notice in list
    const listContainer = document.getElementById('placesList');
    if (listContainer) {
      renderPlacesList(nearby);
      const emergencyCard = `
        <div style="background:rgba(239,68,68,0.08);border:1.5px solid rgba(239,68,68,0.3);border-radius:14px;padding:14px;margin-bottom:12px;">
          <strong style="color:#EF4444;font-size:13px;display:block;margin-bottom:4px;">🚨 Northern Pakistan Emergency Helpline</strong>
          <div style="font-size:12px;color:#102A43;line-height:1.5;">
            <div>🚑 Rescue: <strong>1122</strong> | 🚓 Police: <strong>15</strong></div>
            <div>🏔️ KPK Tourism Police: <strong>1422</strong> | GBDMA: <strong>05811-920874</strong></div>
          </div>
        </div>
      `;
      listContainer.insertAdjacentHTML('afterbegin', emergencyCard);
    }
  } catch (err) {
    console.error("Failed to query nearby places:", err);
  }
}
