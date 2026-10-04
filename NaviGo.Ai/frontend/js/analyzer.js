/**
 * NaviGo Multimodal Road Photo Analyzer & Community Reports Controller
 */

let currentPhotoFile = null;
let currentAnalysis = null;

function handlePhoto(e) {
  const file = e.target.files[0];
  if (!file) return;

  if (file.size > 8 * 1024 * 1024) {
    alert("Please select an image smaller than 8 MB.");
    return;
  }

  currentPhotoFile = file;
  const reader = new FileReader();
  reader.onload = function(ev) {
    const preview = document.getElementById('photoPreview');
    if (preview) preview.src = ev.target.result;
    document.getElementById('uploadZone')?.classList.add('hidden');
    document.getElementById('photoPreviewWrap')?.classList.remove('hidden');
    document.getElementById('analysisResult')?.classList.add('hidden');
  };
  reader.readAsDataURL(file);
}
window.handlePhoto = handlePhoto;

async function analyzePhoto() {
  if (!currentPhotoFile) return;

  toast("Analyzing road image with AI...");
  const formData = new FormData();
  formData.append('file', currentPhotoFile);

  try {
    const res = await api.upload('/vision/road', formData);
    currentAnalysis = res;
    renderAnalysisResult(res);
  } catch (err) {
    console.error("Vision analysis failed:", err);
    toast("Image analysis failed. Please try another photo.");
  }
}
window.analyzePhoto = analyzePhoto;

function renderAnalysisResult(analysis) {
  const resultContainer = document.getElementById('analysisResult');
  if (!resultContainer) return;

  resultContainer.classList.remove('hidden');

  const severityColor = analysis.severity === 'severe' ? '#EF4444' : (analysis.severity === 'high' ? '#F59E0B' : '#059669');
  const issuesHtml = (analysis.issues || []).map(i => 
    `<span style="padding:4px 10px;border-radius:999px;background:#F1F5F9;font-size:12px;font-weight:700;">${api.sanitize(i)}</span>`
  ).join(' ');

  resultContainer.innerHTML = `
    <div class="analysis-card" style="border-left-color: ${severityColor};">
      <div class="warn" style="color: ${severityColor};">
        ⚠️ Possible Issue Detected — AI Suggestion
      </div>
      <h3>${api.sanitize(analysis.summary)}</h3>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin:10px 0;">
        ${issuesHtml}
      </div>
      <div style="font-size:12px;color:var(--muted);margin-bottom:12px;">
        Confidence: <strong>${Math.round(analysis.confidence * 100)}%</strong>
      </div>
      
      <div style="background:#FFFBEB;border:1px solid #FDE68A;padding:12px;border-radius:12px;font-size:12px;color:#92400E;margin-bottom:16px;">
        <strong>Advisory Disclaimer:</strong> ${api.sanitize(analysis.disclaimer)}
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:16px;">
        <div>
          <label style="display:block;font-size:12px;font-weight:700;margin-bottom:4px;">Road Location</label>
          <input type="text" id="reportRoadLocation" value="Naran – Kaghan Road" style="width:100%;padding:10px;border:1.5px solid var(--border);border-radius:10px;font-family:inherit;font-size:13px;">
        </div>
        <div>
          <label style="display:block;font-size:12px;font-weight:700;margin-bottom:4px;">Road Condition</label>
          <select id="reportStatus" style="width:100%;padding:10px;border:1.5px solid var(--border);border-radius:10px;font-family:inherit;font-size:13px;">
            <option value="caution" ${analysis.suggested_status === 'caution' ? 'selected' : ''}>⚠️ Caution Required</option>
            <option value="closed" ${analysis.suggested_status === 'closed' ? 'selected' : ''}>⛔ Road Closed</option>
            <option value="open" ${analysis.suggested_status === 'open' ? 'selected' : ''}>🟢 Road Open / Passable</option>
          </select>
        </div>
      </div>

      <button class="btn-primary" style="width:100%;justify-content:center;padding:14px;" onclick="submitRoadReport()">
        📢 Submit Official Community Report
      </button>
    </div>
  `;

  window.scrollTo({ top: resultContainer.offsetTop - 80, behavior: 'smooth' });
}

async function submitRoadReport() {
  if (!currentAnalysis) return;

  const roadLocation = document.getElementById('reportRoadLocation')?.value.trim() || 'Naran Valley Road';
  const status = document.getElementById('reportStatus')?.value || currentAnalysis.suggested_status || 'caution';

  const payload = {
    destination_slug: 'naran',
    road_name: roadLocation,
    status: status,
    issue_tags: currentAnalysis.issues || ['Mud', 'Standing Water'],
    severity: currentAnalysis.severity || 'medium',
    confidence: currentAnalysis.confidence || 0.85,
    summary: currentAnalysis.summary
  };

  try {
    toast("Submitting road report...");
    await api.post('/reports', payload);
    toast("Report submitted — thank you for keeping travelers safe!");
    resetPhoto();
    loadCommunityReports();
    loadAlerts();
  } catch (err) {
    toast("Failed to submit report. Please try again.");
  }
}
window.submitRoadReport = submitRoadReport;

function resetPhoto() {
  const photoInput = document.getElementById('photoInput');
  if (photoInput) photoInput.value = '';
  document.getElementById('photoPreviewWrap')?.classList.add('hidden');
  document.getElementById('analysisResult')?.classList.add('hidden');
  document.getElementById('uploadZone')?.classList.remove('hidden');
  currentPhotoFile = null;
  currentAnalysis = null;
}
window.resetPhoto = resetPhoto;

// Community Road Reports Feed Loader
async function loadCommunityReports() {
  const container = document.querySelector('#page-analyzer .reports-grid');
  if (!container) return;

  try {
    const reports = await api.get('/reports');
    if (!reports || reports.length === 0) return;

    container.innerHTML = reports.map(r => {
      const dotClass = r.status.toLowerCase() === 'open' ? 'open' : (r.status.toLowerCase() === 'closed' ? 'closed' : 'caution');
      const tags = (r.issue_tags || []).join(', ');

      return `
        <div class="report-card" id="report-${r.id}">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <div class="report-status">
              <span class="status-dot ${dotClass}"></span>
              ${api.sanitize(r.status.toUpperCase())}
            </div>
            <small style="color:var(--muted);font-size:11px;">${r.time_ago || 'Recently'}</small>
          </div>
          <h4>${api.sanitize(r.summary || r.road_name)}</h4>
          <p style="font-size:12.5px;color:var(--muted);margin-top:2px;">📍 ${api.sanitize(r.road_name)}</p>
          ${tags ? `<div style="font-size:11px;color:#64748B;margin-top:4px;">Issues: ${api.sanitize(tags)}</div>` : ''}

          <div style="display:flex;justify-content:space-between;align-items:center;margin-top:12px;padding-top:10px;border-top:1px solid #F1F5F9;">
            <div style="display:flex;gap:6px;">
              <button class="btn-secondary" style="padding:4px 10px;font-size:11px;border-radius:8px;" onclick="voteReport('${r.id}', 'confirm')">
                👍 Still There (${r.confirmations_count || 1})
              </button>
              <button class="btn-secondary" style="padding:4px 10px;font-size:11px;border-radius:8px;" onclick="voteReport('${r.id}', 'cleared')">
                ✓ Cleared (${r.cleared_votes_count || 0})
              </button>
            </div>
            <span style="font-size:10.5px;color:var(--muted);">Unofficial</span>
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    console.error("Failed to load road reports:", err);
  }
}
window.loadCommunityReports = loadCommunityReports;

async function voteReport(reportId, voteType) {
  try {
    await api.post(`/reports/${reportId}/vote`, { vote_type: voteType });
    toast(voteType === 'confirm' ? "Report confirmed" : "Cleared vote recorded");
    loadCommunityReports();
  } catch (err) {
    toast("Voting failed");
  }
}
window.voteReport = voteReport;

// Live Travel Alerts Loader & SSE Listener
async function loadAlerts() {
  try {
    const alerts = await api.get('/alerts');
    renderAlerts(alerts);
  } catch (err) {
    console.error("Failed to fetch alerts:", err);
  }
}
window.loadAlerts = loadAlerts;

function renderAlerts(alerts) {
  const badgeCount = document.getElementById('alertCount');
  const drawerList = document.getElementById('alertDrawerList');
  if (!drawerList) return;

  if (alerts && alerts.length > 0) {
    if (badgeCount) {
      badgeCount.textContent = alerts.length;
      badgeCount.style.display = 'flex';
    }

    drawerList.innerHTML = alerts.map(a => `
      <div class="alert-item-card ${a.severity === 'emergency' ? 'emergency' : 'warning'}">
        <strong style="display:block;margin-bottom:3px;font-size:13px;">${api.sanitize(a.title)}</strong>
        <p style="font-size:12px;color:var(--ink);line-height:1.4;">${api.sanitize(a.description)}</p>
        <span style="display:inline-block;margin-top:6px;font-size:10.5px;font-weight:700;color:var(--muted);text-transform:uppercase;">
          Source: ${api.sanitize(a.source)}
        </span>
      </div>
    `).join('');
  } else {
    if (badgeCount) badgeCount.style.display = 'none';
    drawerList.innerHTML = `<div style="color:var(--muted);font-size:13px;padding:12px;text-align:center;">No active travel alerts right now. Roads are clear.</div>`;
  }
}
