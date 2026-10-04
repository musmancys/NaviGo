/**
 * NaviGo Core Application Script
 * Controls page routing, UI modals, alerts drawer, and initialization.
 */

// Toast notification helper
let toastTimer = null;
function toast(msg) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    t.classList.remove('show');
  }, 2500);
}
window.toast = toast;

// Page Navigation
function showPage(name) {
  const pages = document.querySelectorAll('.page');
  pages.forEach(p => p.classList.remove('active'));

  const target = document.getElementById(`page-${name}`);
  if (target) {
    target.classList.add('active');
    state.activePage = name;
  }

  // Update navbar links
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.toggle('active', link.getAttribute('data-page') === name);
  });

  // Update mobile bottom nav links
  document.querySelectorAll('.mobile-bottom-nav a').forEach(link => {
    link.classList.toggle('active', link.getAttribute('data-page') === name);
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });

  // Hook into page-specific loaders
  if (name === 'explore' && window.initExploreMap) {
    window.initExploreMap();
  } else if (name === 'history' && window.loadTripHistory) {
    window.loadTripHistory();
  } else if (name === 'analyzer' && window.loadCommunityReports) {
    window.loadCommunityReports();
  }
}
window.showPage = showPage;

// Mobile menu toggles
function toggleMenu() {
  const nav = document.getElementById('navLinks');
  if (nav) nav.classList.toggle('mobile-open');
}
window.toggleMenu = toggleMenu;

function closeMobileMenu() {
  const nav = document.getElementById('navLinks');
  if (nav) nav.classList.remove('mobile-open');
}
window.closeMobileMenu = closeMobileMenu;

// Demo info modal / toast
function showDemoInfo() {
  const isDemo = state.config.demo_mode;
  if (isDemo) {
    alert("⚡ Demo Mode Active\n\nNaviGo is operating in zero-dependency offline mode using local seeded data and realistic AI responses. Real-time external keys for Supabase/Gemini are not required for this demo.");
  } else {
    toast(`Connected to Cloud (${state.config.environment})`);
  }
}
window.showDemoInfo = showDemoInfo;

// Alerts Drawer Toggle
function toggleAlertsDrawer() {
  const drawer = document.getElementById('alertDrawer');
  if (drawer) {
    drawer.classList.toggle('open');
  }
}
window.toggleAlertsDrawer = toggleAlertsDrawer;

// Kashmir fallback image handler
function kashFallback(img) {
  const steps = [
    'https://images.unsplash.com/photo-1614591276564-7b3e69347a48?auto=format&fit=crop&w=1200&q=80',
    'https://commons.wikimedia.org/wiki/Special:FilePath/Kel_Valley_-_Neelum_Kashmir.jpg?width=1200',
    'https://images.unsplash.com/photo-1595815771614-ade9d652a65d?auto=format&fit=crop&w=1200&q=80'
  ];
  let i = parseInt(img.getAttribute('data-fb') || '0', 10);
  if (i >= steps.length) { img.onerror = null; return; }
  img.setAttribute('data-fb', i + 1);
  img.src = steps[i];
}
window.kashFallback = kashFallback;

// Urdu Localization Dictionary
const I18N = {
  en: {
    nav_home: "Home",
    nav_explore: "Explore",
    nav_plan: "Plan Trip",
    nav_assistant: "AI Assistant",
    nav_reports: "Road Reports",
    nav_history: "History",
    hero_title: "Explore More.<br><span class=\"accent\">Plan Smarter.</span>",
    hero_sub: "Discover Pakistan, create personalized trips, and explore destinations with NaviGo.",
    btn_start: "Get Started",
    btn_create_trip: "✨ Create AI Trip",
    search_head: "🗺️ Where are you going?",
    label_dest: "Destination",
    label_duration: "Duration",
    label_travelers: "Travelers",
    label_budget: "Budget (PKR)",
    explore_head: "Explore Pakistan",
    explore_sub: "Search destinations, hotels, restaurants, and more."
  },
  ur: {
    nav_home: "ہوم",
    nav_explore: "دریافت کریں",
    nav_plan: "سفر کا منصوبہ",
    nav_assistant: "اے آئی معاون",
    nav_reports: "سڑک کے حالات",
    nav_history: "تاریخچہ",
    hero_title: "نیا راستہ دریافت کریں۔<br><span class=\"accent\">ذہانت سے منصوبہ بنائیں۔</span>",
    hero_sub: "پاکستان کے خوبصورت مقامات دریافت کریں اور محفوظ سفر کا مکمل پلان حاصل کریں۔",
    btn_start: "شروع کریں",
    btn_create_trip: "✨ اے آئی ٹرپ بنائیں",
    search_head: "🗺️ آپ کہاں جانا چاہتے ہیں؟",
    label_dest: "منزل",
    label_duration: "مدت",
    label_travelers: "مسافر",
    label_budget: "بجٹ (روپے)",
    explore_head: "شمالی علاقہ جات دریافت کریں",
    explore_sub: "ہوٹل، ریسٹورنٹ، راستے اور ایمرجنسی خدمات تلاش کریں۔"
  }
};

function toggleLanguage(lang) {
  const targetLang = lang || (state.currentLanguage === 'en' ? 'ur' : 'en');
  state.currentLanguage = targetLang;
  const dict = I18N[targetLang] || I18N.en;

  if (targetLang === 'ur') {
    document.body.setAttribute('dir', 'rtl');
    document.documentElement.setAttribute('lang', 'ur');
  } else {
    document.body.removeAttribute('dir');
    document.documentElement.setAttribute('lang', 'en');
  }

  // Update text elements if present
  const heroTitle = document.querySelector('.hero h1');
  if (heroTitle) heroTitle.innerHTML = dict.hero_title;

  const heroSub = document.querySelector('.hero p');
  if (heroSub) heroSub.textContent = dict.hero_sub;

  const searchHead = document.querySelector('.search-card h3');
  if (searchHead) searchHead.textContent = dict.search_head;

  toast(targetLang === 'ur' ? "اردو موڈ فعال ہے" : "Switched to English");
}
window.toggleLanguage = toggleLanguage;

// Profile Page Dynamic Interactions
async function showSavedDestinations() {
  try {
    const list = await api.get('/me/saved');
    if (!list || list.length === 0) {
      alert("No saved destinations yet. Click on any destination to save it!");
      return;
    }
    const names = list.map(d => `• ${d.name} (${d.best_season || 'Summer'})`).join('\n');
    alert(`⭐ Your Saved Destinations:\n\n${names}`);
  } catch (err) {
    toast("Could not load saved destinations");
  }
}
window.showSavedDestinations = showSavedDestinations;

async function showMyReports() {
  try {
    const reports = await api.get('/me/reports');
    if (!reports || reports.length === 0) {
      alert("You haven't submitted any road reports yet.");
      return;
    }
    const reportList = reports.map(r => `• ${r.road_name}: Status ${r.status.toUpperCase()} (${r.created_at.split('T')[0]})`).join('\n');
    alert(`📝 Your Submitted Road Reports:\n\n${reportList}`);
  } catch (err) {
    toast("Could not load reports");
  }
}
window.showMyReports = showMyReports;

function showSettingsModal() {
  const currentLang = state.currentLanguage.toUpperCase();
  const choice = confirm(`⚙️ NaviGo Settings\n\nCurrent Language: ${currentLang}\nUnits: Metric (°C, km)\n\nClick OK to toggle Language (English ↔ اردو).`);
  if (choice) {
    toggleLanguage();
  }
}
window.showSettingsModal = showSettingsModal;

// "Identify This Place" Modal Trigger
function triggerIdentifyPlace() {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/*';
  input.onchange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    toast("Inspecting landmark image with Vision AI...");
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await api.upload('/vision/identify-place', formData);
      alert(`📷 Landmark Identified!\n\n${res.phrasing}\nDestination: ${res.destination}\nConfidence: ${Math.round(res.confidence * 100)}%\n\n${res.description}\nBest Time: ${res.best_visiting_time}\n\n⚠️ Disclaimer: ${res.disclaimer}`);
    } catch (err) {
      toast("Could not identify landmark.");
    }
  };
  input.click();
}
window.triggerIdentifyPlace = triggerIdentifyPlace;

// Application Initialization
document.addEventListener('DOMContentLoaded', async () => {
  // Splash Screen auto-hide after 1.5s
  setTimeout(() => {
    const splash = document.getElementById('splash');
    if (splash) splash.classList.add('hide');
  }, 1500);

  // Fetch runtime configuration from /api/config
  try {
    const config = await api.get('/config');
    state.config = config;
    const badge = document.getElementById('demoBadge');
    if (badge) {
      if (config.demo_mode) {
        badge.textContent = "⚡ Demo Mode";
        badge.style.display = "inline-flex";
      } else {
        badge.textContent = `🟢 Cloud (${config.environment})`;
        badge.style.background = "rgba(16, 185, 129, 0.15)";
        badge.style.color = "#059669";
        badge.style.borderColor = "rgba(16, 185, 129, 0.3)";
      }
    }
  } catch (e) {
    console.log("Running in offline demo mode:", e);
  }

  // Load Initial Destinations and Alerts
  if (window.loadDestinations) window.loadDestinations();
  if (window.loadAlerts) window.loadAlerts();
});
