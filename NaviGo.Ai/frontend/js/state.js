/**
 * NaviGo Global Application State
 */
const state = {
  activePage: 'home',
  config: {
    demo_mode: true,
    ai_demo_mode: true,
    environment: 'dev'
  },
  user: {
    id: 'demo-user-1',
    name: 'Traveler',
    email: 'traveler@navigo.pk',
    role: 'tourist'
  },
  destinations: [],
  currentDestination: null,
  places: [],
  activeTrip: null,
  alerts: [],
  currentLanguage: 'en',
  
  listeners: {},

  on(event, callback) {
    if (!this.listeners[event]) this.listeners[event] = [];
    this.listeners[event].push(callback);
  },

  emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(cb => cb(data));
    }
  }
};

window.state = state;
