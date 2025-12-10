import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Market Data API
export const marketAPI = {
  getCompanies: () => api.get('/market/companies'),
  getCompany: (ticker) => api.get(`/market/companies/${ticker}`),
  getStockPrices: (ticker, params) => api.get(`/market/stocks/${ticker}/prices`, { params }),
  getLatestPrice: (ticker) => api.get(`/market/stocks/${ticker}/latest`),
  updateTickerData: (ticker) => api.post(`/market/stocks/${ticker}/update`),
};

// Risk Analysis API
export const riskAPI = {
  getRiskScore: (ticker) => api.get(`/risk/${ticker}`),
  getRiskTimeline: (ticker, days = 90) => api.get(`/risk/${ticker}/timeline`, { params: { days } }),
  calculateRiskBatch: (tickers) => api.post('/risk/calculate', tickers),
};

// Insights API
export const insightsAPI = {
  queryDocuments: (question, ticker = null) =>
    api.post('/insights/query', { question, ticker }),
  generateRiskStory: (ticker) =>
    api.post('/insights/risk-story', { ticker }),
};

export default api;
