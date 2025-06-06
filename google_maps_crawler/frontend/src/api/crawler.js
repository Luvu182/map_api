import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const fetchStats = async () => {
  const response = await axios.get(`${API_BASE_URL}/stats`);
  return response.data;
};

export const fetchUnprocessedRoads = async (limit = 100) => {
  const response = await axios.get(`${API_BASE_URL}/roads/unprocessed`, {
    params: { limit }
  });
  return response.data;
};

export const fetchCrawlStatus = async (stateCode, countyFips, keyword) => {
  const response = await axios.get(`${API_BASE_URL}/roads/crawl-status`, {
    params: { 
      state_code: stateCode,
      county_fips: countyFips,
      keyword: keyword
    }
  });
  return response.data;
};

export const crawlSingleRoad = async (roadId, keyword) => {
  const response = await axios.post(`${API_BASE_URL}/crawl/road/${roadId}`, null, {
    params: { keyword }
  });
  return response.data;
};

export const startCrawl = async (stateCode, limit) => {
  const response = await axios.post(`${API_BASE_URL}/crawl/start`, null, {
    params: { state_code: stateCode, limit }
  });
  return response.data;
};

export const searchRoads = async (query) => {
  // This would connect to Supabase directly or through your API
  // For now, return mock data
  return {
    roads: [
      { linearid: '123', fullname: 'Broadway', state_code: 'NY', county_fips: '36061' },
      { linearid: '456', fullname: 'Main Street', state_code: 'CA', county_fips: '06037' }
    ]
  };
};

export const fetchBusinessesForRoad = async (roadId) => {
  // This would fetch from your API
  // For now, return mock data
  return {
    businesses: [
      {
        place_id: 'abc123',
        name: 'Sample Restaurant',
        formatted_address: '123 Main St',
        rating: 4.5,
        types: ['restaurant', 'food']
      }
    ]
  };
};

export const fetchCountiesByState = async (stateCode) => {
  const response = await axios.get(`${API_BASE_URL}/counties/${stateCode}`);
  return response.data;
};

export const fetchStatesSummary = async () => {
  const response = await axios.get(`${API_BASE_URL}/states/summary`);
  return response.data;
};