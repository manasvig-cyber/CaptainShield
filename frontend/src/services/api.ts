/**
 * AegisGuard Backend API Client Service
 */

const API_BASE = 'http://127.0.0.1:5000';

export interface StartSimulationParams {
  preset: string;
  workers: number;
  request_interval: number;
  jitter: number;
  duration: number;
  target_url: string;
}

export const api = {
  async getHealth() {
    const res = await fetch(`${API_BASE}/api/health`);
    return res.json();
  },

  async startSimulation(params: StartSimulationParams) {
    const res = await fetch(`${API_BASE}/api/simulation/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    return res.json();
  },

  async stopSimulation(reason = 'User stopped via Command Center') {
    const res = await fetch(`${API_BASE}/api/simulation/stop`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason }),
    });
    return res.json();
  },

  async getCurrentSimulation() {
    const res = await fetch(`${API_BASE}/api/simulation/current`);
    return res.json();
  },

  async getEvents(sessionId: string, count = 40) {
    const res = await fetch(`${API_BASE}/api/simulation/${sessionId}/events?count=${count}`);
    return res.json();
  },

  async getTelemetry(sessionId: string, count = 30) {
    const res = await fetch(`${API_BASE}/api/simulation/${sessionId}/telemetry?count=${count}`);
    return res.json();
  },

  async getThreatMatrix(sessionId: string) {
    const res = await fetch(`${API_BASE}/api/threat-matrix/${sessionId}`);
    return res.json();
  },

  async getRecentHistory() {
    const res = await fetch(`${API_BASE}/api/recent`);
    return res.json();
  },

  async deleteRecent(sessionId: string) {
    const res = await fetch(`${API_BASE}/api/recent/${sessionId}`, {
      method: 'DELETE',
    });
    return res.json();
  },

  async getSettings() {
    const res = await fetch(`${API_BASE}/api/settings`);
    return res.json();
  },

  async updateSettings(settings: Record<string, any>) {
    const res = await fetch(`${API_BASE}/api/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    return res.json();
  },

  async getModelStatus() {
    const res = await fetch(`${API_BASE}/api/model/status`);
    return res.json();
  },

  async search(query: string) {
    const res = await fetch(`${API_BASE}/api/search?q=${encodeURIComponent(query)}`);
    return res.json();
  },

  async searchIp(ip: string) {
    const res = await fetch(`${API_BASE}/api/search/ip/${encodeURIComponent(ip)}`);
    return res.json();
  },

  async getSearchSuggestions() {
    const res = await fetch(`${API_BASE}/api/search/suggestions`);
    return res.json();
  },

  async testWorkflow() {
    const res = await fetch(`${API_BASE}/api/workflow/test`);
    return res.json();
  },
};
