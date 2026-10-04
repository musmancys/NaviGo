/**
 * NaviGo AI Trip Planner & Itinerary Controller
 * Drives SSE generation, 4-step animation, dynamic day cards, budget card, and PDF export.
 */

async function generateTrip() {
  const origin = document.getElementById('planOrigin')?.value.trim() || 'Islamabad';
  const dest = document.getElementById('planDest')?.value || 'naran';
  const duration = parseInt(document.getElementById('planDuration')?.value || '3', 10);
  const travelers = parseInt(document.getElementById('planTravelers')?.value || '4', 10);
  const budget = parseInt(document.getElementById('planBudget')?.value || '35000', 10);
  const transport = document.getElementById('planTransport')?.value || 'car';

  const interests = [];
  document.querySelectorAll('#interestChips .chip.active').forEach(c => {
    interests.push(c.getAttribute('data-interest') || c.textContent.trim());
  });

  const payload = {
    origin,
    destination_slug: dest,
    duration_days: duration,
    travelers_count: travelers,
    budget_pkr: budget,
    transport_type: transport,
    interests: interests.length > 0 ? interests : ['nature', 'adventure']
  };

  // UI transition to loading
  document.getElementById('planForm')?.classList.add('hidden');
  document.getElementById('planResult')?.classList.add('hidden');
  document.getElementById('planLoading')?.classList.remove('hidden');

  // Reset steps
  const steps = document.querySelectorAll('.loading-step');
  steps.forEach((s, idx) => {
    s.classList.remove('done');
    const check = s.querySelector('.step-check');
    if (check) check.textContent = (idx + 1);
  });

  try {
    const response = await fetch('/api/trips/plan', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${api.getToken()}`
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) throw new Error('Trip planning failed');

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop(); // keep last incomplete line

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (line.startsWith('data:')) {
          const jsonStr = line.substring(5).trim();
          try {
            const data = JSON.parse(jsonStr);
            if (data.step !== undefined) {
              markStepDone(data.step);
            } else if (data.id && data.days) {
              // Complete trip response
              state.activeTrip = data;
              setTimeout(() => {
                renderTripResult(data);
              }, 400);
            }
          } catch (e) {
            // Ignore non-json lines
          }
        }
      }
    }
  } catch (err) {
    console.error("Plan SSE error:", err);
    toast("Failed to generate plan. Please try again.");
    backToForm();
  }
}
window.generateTrip = generateTrip;

function markStepDone(stepIdx) {
  const steps = document.querySelectorAll('.loading-step');
  if (steps[stepIdx]) {
    steps[stepIdx].classList.add('done');
    const check = steps[stepIdx].querySelector('.step-check');
    if (check) check.textContent = '✓';
  }
}

function renderTripResult(trip) {
  document.getElementById('planLoading')?.classList.add('hidden');
  const resultContainer = document.getElementById('planResult');
  if (!resultContainer) return;

  resultContainer.classList.remove('hidden');

  // Headings
  const titleEl = resultContainer.querySelector('.result-head h1');
  if (titleEl) titleEl.textContent = trip.title;

  const metaEl = document.getElementById('resultMeta');
  if (metaEl) {
    metaEl.textContent = `${trip.duration_days} Days • ${trip.travelers_count} Travelers • Origin: ${trip.origin} • Transport: ${trip.transport_type.toUpperCase()}`;
  }

  // Timeline Column
  const timelineCol = resultContainer.querySelector('.timeline-col');
  if (timelineCol) {
    let warningsHtml = '';
    if (trip.road_warnings && trip.road_warnings.length > 0) {
      warningsHtml = `
        <div style="background:rgba(245,158,11,0.08);border:1.5px solid rgba(245,158,11,0.3);border-radius:18px;padding:18px;margin-bottom:12px;">
          <strong style="color:#B45309;font-size:13.5px;display:flex;align-items:center;gap:6px;margin-bottom:6px;">
            ⚠️ Weather & Road Travel Advisory
          </strong>
          <ul style="margin-left:18px;font-size:12.5px;color:#102A43;line-height:1.5;">
            ${trip.road_warnings.map(w => `<li>${api.sanitize(w)}</li>`).join('')}
          </ul>
        </div>
      `;
    }

    const daysHtml = trip.days.map(d => `
      <div class="day-card">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span class="day-badge">${api.sanitize(d.day_badge)}</span>
          <strong style="font-size:14px;color:var(--navy);">${api.sanitize(d.theme)}</strong>
        </div>
        <div class="timeline" style="margin-top:14px;">
          ${d.stops.map(s => `
            <div class="tl-item">
              <span class="tl-dot"></span>
              <span class="pin">📍</span>
              <strong>${api.sanitize(s.time_of_day)}:</strong>&nbsp;${api.sanitize(s.place_name)}
              <span style="color:var(--muted);font-size:12.5px;">— ${api.sanitize(s.activity)}</span>
            </div>
          `).join('')}
        </div>
        ${d.notes ? `<div style="margin-top:12px;font-size:12px;color:var(--muted);font-style:italic;">💡 ${api.sanitize(d.notes)}</div>` : ''}
      </div>
    `).join('');

    timelineCol.innerHTML = warningsHtml + daysHtml;
  }

  // Budget Column
  const budgetCard = resultContainer.querySelector('.budget-card');
  if (budgetCard && trip.budget_breakdown) {
    const bd = trip.budget_breakdown;
    const b = bd.breakdown || {};
    const statusClass = bd.status_class || 'within';
    const badgeColor = statusClass === 'within' ? '#059669' : (statusClass === 'close' ? '#B45309' : '#DC2626');
    const badgeBg = statusClass === 'within' ? 'rgba(16,185,129,0.1)' : (statusClass === 'close' ? 'rgba(245,158,11,0.1)' : 'rgba(239,68,68,0.1)');

    budgetCard.innerHTML = `
      <h3>Estimated Budget</h3>
      <div class="budget-row"><span>Transport (${trip.transport_type})</span><strong>Rs. ${(b.transport || 0).toLocaleString()}</strong></div>
      <div class="budget-row"><span>Hotel (${trip.duration_days - 1} nights)</span><strong>Rs. ${(b.hotel || 0).toLocaleString()}</strong></div>
      <div class="budget-row"><span>Food (${trip.travelers_count} people)</span><strong>Rs. ${(b.food || 0).toLocaleString()}</strong></div>
      <div class="budget-row"><span>Activities & Jeeps</span><strong>Rs. ${(b.activities || 0).toLocaleString()}</strong></div>
      <div class="budget-row"><span>Contingency (5%)</span><strong>Rs. ${(b.contingency || 0).toLocaleString()}</strong></div>
      <div class="budget-total">
        <span>Total Estimated</span>
        <span>Rs. ${(bd.total_estimated_pkr || 0).toLocaleString()}</span>
      </div>
      <div class="budget-badge" style="background:${badgeBg};color:${badgeColor};">
        ${statusClass === 'within' ? '🟢' : (statusClass === 'close' ? '🟡' : '🔴')} ${api.sanitize(bd.status || 'Within Budget')}
      </div>
      ${bd.tips && bd.tips.length > 0 ? `<p style="font-size:12px;color:var(--muted);margin-top:12px;line-height:1.4;">${api.sanitize(bd.tips[0])}</p>` : ''}

      <div style="display:flex;flex-direction:column;gap:8px;margin-top:20px;">
        <button class="btn-primary" style="justify-content:center;padding:12px;" onclick="downloadTripPDF('${trip.id}')">
          📄 Download PDF Itinerary
        </button>
        <button class="btn-secondary" style="justify-content:center;padding:12px;" onclick="shareTrip('${trip.share_slug || trip.id}')">
          🔗 Share Itinerary Link
        </button>
      </div>
    `;
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function backToForm() {
  document.getElementById('planResult')?.classList.add('hidden');
  document.getElementById('planLoading')?.classList.add('hidden');
  document.getElementById('planForm')?.classList.remove('hidden');
  window.scrollTo({ top: 0, behavior: 'smooth' });
}
window.backToForm = backToForm;

function downloadTripPDF(tripId) {
  toast("Preparing PDF download...");
  window.open(`/api/trips/${tripId}/pdf`, '_blank');
}
window.downloadTripPDF = downloadTripPDF;

function shareTrip(slug) {
  const shareUrl = `${window.location.origin}/#trip-${slug}`;
  navigator.clipboard.writeText(shareUrl).then(() => {
    toast("Share link copied to clipboard!");
  }).catch(() => {
    prompt("Copy trip link:", shareUrl);
  });
}
window.shareTrip = shareTrip;

const DEST_THUMBS = {
  naran: 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=400&q=80',
  hunza: 'https://images.unsplash.com/photo-1589308078059-be1415eab4c3?auto=format&fit=crop&w=400&q=80',
  skardu: 'https://images.unsplash.com/photo-1509316785289-025f5b846b35?auto=format&fit=crop&w=400&q=80',
  kashmir: 'https://images.unsplash.com/photo-1595815771614-ade9d652a65d?auto=format&fit=crop&w=400&q=80',
  swat: 'https://images.unsplash.com/photo-1533130061792-64b345e4a833?auto=format&fit=crop&w=400&q=80',
  'fairy-meadows': 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=400&q=80',
  fairy: 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=400&q=80',
  gilgit: 'https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=400&q=80',
  murree: 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=400&q=80'
};

// Dynamic Trip History Loader
async function loadTripHistory() {
  const container = document.querySelector('#page-history .history-grid');
  if (!container) return;

  try {
    const trips = await api.get('/trips');
    if (!trips || trips.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 48px 20px; background: white; border-radius: 20px; border: 1.5px dashed var(--border); box-shadow: var(--shadow-soft);">
          <div style="font-size: 40px; margin-bottom: 12px;">🗺️</div>
          <h3 style="font-size: 18px; font-weight: 700; color: var(--navy); margin-bottom: 6px;">No Saved Trips</h3>
          <p style="color: var(--muted); font-size: 14px; margin-bottom: 20px;">Your travel history is currently empty. Plan a new trip to get started!</p>
          <button class="btn-primary" onclick="showPage('plan')" style="padding: 10px 24px; border-radius: 12px; font-weight: 600;">Plan a New Trip</button>
        </div>
      `;
      return;
    }

    container.innerHTML = trips.map(t => {
      const status = t.status || 'completed';
      const statusLabel = status === 'completed' ? '✓ Completed' : (status === 'upcoming' ? '⏱ Upcoming' : '✎ Draft');
      const slug = (t.destination_slug || '').toLowerCase().replace(/_/g, '-');
      const img = t.img || DEST_THUMBS[slug] || 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=400&q=80';

      return `
        <div class="history-card" id="history-card-${t.id}" onclick="openTripFromHistory('${t.id}')">
          <button class="delete-trip-btn" onclick="deleteTripFromHistory(event, '${t.id}')" title="Delete this trip" aria-label="Delete trip">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              <line x1="10" y1="11" x2="10" y2="17"></line>
              <line x1="14" y1="11" x2="14" y2="17"></line>
            </svg>
          </button>
          <div class="history-img">
            <img src="${img}" alt="${api.sanitize(t.title)}" onerror="kashFallback(this)">
          </div>
          <div class="history-body">
            <h3>${api.sanitize(t.title)}</h3>
            <div class="meta">
              <span>📅 ${t.duration_days} Days</span>
              <span>👥 ${t.travelers_count} Travelers</span>
            </div>
            <span class="history-status ${status}">${statusLabel}</span>
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    console.error("Failed to load history:", err);
  }
}
window.loadTripHistory = loadTripHistory;

async function deleteTripFromHistory(event, tripId) {
  if (event) {
    event.stopPropagation();
    event.preventDefault();
  }

  if (!confirm("Are you sure you want to remove this trip from your history?")) {
    return;
  }

  try {
    const cardEl = document.getElementById(`history-card-${tripId}`);
    if (cardEl) {
      cardEl.style.transition = "all 0.25s ease";
      cardEl.style.opacity = "0.3";
      cardEl.style.transform = "scale(0.95)";
    }

    const res = await api.delete(`/trips/${tripId}`);
    toast("Trip deleted from history");
    await loadTripHistory();
  } catch (err) {
    console.error("Failed to delete trip:", err);
    toast("Could not delete trip");
    await loadTripHistory();
  }
}
window.deleteTripFromHistory = deleteTripFromHistory;

async function openTripFromHistory(tripId) {
  try {
    toast("Opening trip details...");
    const trip = await api.get(`/trips/${tripId}`);
    if (trip) {
      showPage('plan');
      document.getElementById('planForm')?.classList.add('hidden');
      renderTripResult(trip);
    }
  } catch (err) {
    toast("Could not open trip details");
  }
}
window.openTripFromHistory = openTripFromHistory;
