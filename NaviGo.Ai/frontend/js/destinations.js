/**
 * NaviGo Destinations Controller
 * Handles dynamic destination fetching, Home grid rendering, and Destination detail view.
 */

let cachedDestinations = [];

async function loadDestinations() {
  try {
    const list = await api.get('/destinations');
    if (list && list.length > 0) {
      cachedDestinations = list;
      state.destinations = list;
      renderHomeDestinations(list);
      populateDestinationDropdowns(list);
    }
  } catch (err) {
    console.error("Failed to load destinations:", err);
  }
}
window.loadDestinations = loadDestinations;

function renderHomeDestinations(destinations) {
  const container = document.querySelector('#page-home .dest-grid');
  if (!container) return;

  container.innerHTML = destinations.map(d => {
    const tags = Array.isArray(d.tags) ? d.tags.join(' • ') : (d.tags || 'Scenic');
    const priceFormatted = d.from_price_pkr ? `From Rs. ${d.from_price_pkr.toLocaleString()}` : 'Explore';
    const safeName = api.sanitize(d.name);
    const safeSub = api.sanitize(d.sub_title || '');

    return `
      <div class="dest-card" onclick="showDestination('${d.slug}')">
        <div class="dest-img">
          <img src="${d.hero_image_url || 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=800&q=80'}" alt="${safeName}" loading="lazy" onerror="kashFallback(this)">
          <span class="dest-tag">${api.sanitize(tags)}</span>
          <span class="dest-price">${priceFormatted}</span>
        </div>
        <div class="dest-body">
          <div>
            <h3>${safeName}</h3>
            <p>${safeSub}</p>
          </div>
          <div class="dest-arrow">↗</div>
        </div>
      </div>
    `;
  }).join('');
}

function populateDestinationDropdowns(destinations) {
  const selects = [
    document.getElementById('homeDest'),
    document.getElementById('planDest')
  ];

  selects.forEach(select => {
    if (!select) return;
    const currentVal = select.value;
    select.innerHTML = destinations.map(d => 
      `<option value="${d.slug}">${api.sanitize(d.name)}</option>`
    ).join('');
    if (currentVal && destinations.some(d => d.slug === currentVal)) {
      select.value = currentVal;
    }
  });
}

async function showDestination(slug) {
  try {
    toast(`Loading ${slug.toUpperCase()} details...`);
    const d = await api.get(`/destinations/${slug}`);
    if (!d) return;

    state.currentDestination = d;

    // Update Hero elements
    const heroImg = document.getElementById('destHeroImg');
    if (heroImg) {
      heroImg.removeAttribute('data-fb');
      heroImg.onerror = () => kashFallback(heroImg);
      heroImg.src = d.hero_image_url || '';
    }

    const titleEl = document.getElementById('destHeroTitle');
    if (titleEl) titleEl.textContent = d.name;

    const subEl = document.getElementById('destHeroSub');
    if (subEl) subEl.textContent = d.sub_title || '';

    const aboutTitle = document.getElementById('destAboutTitle');
    if (aboutTitle) aboutTitle.textContent = `About ${d.name}`;

    const aboutEl = document.getElementById('destAbout');
    if (aboutEl) aboutEl.textContent = d.about || '';

    // Weather section
    const w = d.weather || { temp: 18, cond: "Partly Cloudy", high: 21, low: 12, icon: "⛅" };
    const destTemp = document.getElementById('destTemp');
    if (destTemp) destTemp.textContent = `🌡️ ${w.temp}°C`;

    const destCond = document.getElementById('destCond');
    if (destCond) destCond.textContent = `${w.icon || '☁️'} ${w.cond}`;

    const wTemp = document.getElementById('wTemp');
    if (wTemp) wTemp.textContent = `${w.temp}°C`;

    const wCond = document.getElementById('wCond');
    if (wCond) wCond.textContent = w.cond;

    const wHigh = document.getElementById('wHigh');
    if (wHigh) wHigh.textContent = `${w.high}°C`;

    const wLow = document.getElementById('wLow');
    if (wLow) wLow.textContent = `${w.low}°C`;

    // Road conditions
    const roadStatus = d.road_status || 'Open';
    const destRoad = document.getElementById('destRoad');
    if (destRoad) {
      destRoad.className = `meta-chip ${roadStatus.toLowerCase() === 'open' ? 'green' : 'amber'}`;
      destRoad.textContent = `🚦 Road ${roadStatus} (Unofficial / Community)`;
    }

    // Popular Places
    const placesContainer = document.getElementById('destPlaces');
    if (placesContainer && d.popular_places) {
      placesContainer.innerHTML = d.popular_places.map(p => `
        <div class="place-box" onclick="filterExploreToPlace('${p.name}')" style="cursor:pointer;" title="View on map">
          <div class="emoji">${p.icon || '🏔️'}</div>
          <strong>${api.sanitize(p.name)}</strong>
          <small style="color:var(--muted);display:block;margin-top:4px;">${api.sanitize(p.price_level || '')}</small>
        </div>
      `).join('');
    }

    // Add or Update Verified Businesses Section
    renderDestinationBusinesses(d);

    showPage('destination');
  } catch (err) {
    console.error("Failed to fetch destination detail:", err);
    toast("Failed to load destination details");
  }
}
window.showDestination = showDestination;

function renderDestinationBusinesses(d) {
  let section = document.getElementById('destBusinessesSection');
  if (!section) {
    const parent = document.querySelector('#page-destination .dest-detail-grid > div:first-child');
    if (parent) {
      section = document.createElement('div');
      section.id = 'destBusinessesSection';
      section.className = 'detail-card';
      parent.appendChild(section);
    }
  }

  if (section && d.verified_businesses && d.verified_businesses.length > 0) {
    section.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
        <h2>Verified Hotels & Guides</h2>
        <span class="verified-badge">✓ Verified Platform Partners</span>
      </div>
      <div style="display:flex;flex-direction:column;gap:12px;">
        ${d.verified_businesses.map(b => `
          <div style="padding:14px;border:1.5px solid var(--border);border-radius:14px;display:flex;justify-content:space-between;align-items:center;background:#FAFAFA;">
            <div>
              <strong style="font-size:15px;">${api.sanitize(b.name)}</strong>
              <div style="font-size:12px;color:var(--muted);margin-top:3px;">
                <span>⭐ ${b.rating}</span> • <span>${b.business_type.toUpperCase()}</span> • <span>${api.sanitize(b.price_range || '')}</span>
              </div>
              <div style="font-size:11px;color:#059669;font-weight:700;margin-top:4px;">
                ✓ Verified Business · Last verified: ${api.sanitize(b.verified_at || 'September 2026')}
              </div>
            </div>
            ${b.phone ? `<a href="tel:${b.phone}" class="btn-secondary" style="padding:8px 14px;font-size:12px;">📞 Call</a>` : ''}
          </div>
        `).join('')}
      </div>
    `;
  } else if (section) {
    section.innerHTML = `
      <h2>Local Guides & Hotels</h2>
      <p style="color:var(--muted);">No verified partners listed for this destination yet.</p>
    `;
  }
}

function filterExploreToPlace(placeName) {
  showPage('explore');
  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.value = placeName;
    if (window.filterPlaces) window.filterPlaces();
  }
}
window.filterExploreToPlace = filterExploreToPlace;

function applyHomeSearchToPlan() {
  const dest = document.getElementById('homeDest')?.value;
  const duration = document.getElementById('homeDuration')?.value;
  const travelers = document.getElementById('homeTravelers')?.value;
  const budget = document.getElementById('homeBudget')?.value;

  if (dest && document.getElementById('planDest')) {
    document.getElementById('planDest').value = dest;
  }
  if (duration && document.getElementById('planDuration')) {
    document.getElementById('planDuration').value = duration;
  }
  if (travelers && document.getElementById('planTravelers')) {
    document.getElementById('planTravelers').value = travelers;
  }
  if (budget && document.getElementById('planBudget')) {
    document.getElementById('planBudget').value = budget;
  }

  showPage('plan');
}
window.applyHomeSearchToPlan = applyHomeSearchToPlan;
