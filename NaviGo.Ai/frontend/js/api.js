/**
 * NaviGo API Client Wrapper
 * Handles relative path calls, auth tokens, error notifications, and SSE streams.
 */
const api = {
  baseUrl: '/api',

  getToken() {
    return localStorage.getItem('navigo_token') || '';
  },

  setToken(token) {
    if (token) localStorage.setItem('navigo_token', token);
    else localStorage.removeItem('navigo_token');
  },

  getHeaders(customHeaders = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...customHeaders
    };
    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  },

  async request(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
    const config = {
      ...options,
      headers: this.getHeaders(options.headers || {})
    };

    try {
      const response = await fetch(url, config);
      if (response.status === 204) return null;

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const errorMsg = data?.error?.message || data?.detail || `Request failed with status ${response.status}`;
        throw new Error(errorMsg);
      }
      return data;
    } catch (err) {
      console.warn(`[NaviGo API Error] ${endpoint}:`, err);
      throw err;
    }
  },

  get(endpoint, params = {}) {
    const query = new URLSearchParams(params).toString();
    const fullUrl = query ? `${endpoint}?${query}` : endpoint;
    return this.request(fullUrl, { method: 'GET' });
  },

  post(endpoint, body = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(body)
    });
  },

  put(endpoint, body = {}) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body)
    });
  },

  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  },

  async upload(endpoint, formData) {
    const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
    const headers = {};
    const token = this.getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data?.error?.message || 'Upload failed');
    }
    return response.json();
  },

  /**
   * Safe HTML string sanitizer using DOMPurify with strict fallback.
   */
  sanitize(html) {
    if (window.DOMPurify) {
      return window.DOMPurify.sanitize(html);
    }
    const div = document.createElement('div');
    div.textContent = html;
    return div.innerHTML;
  }
};

window.api = api;
