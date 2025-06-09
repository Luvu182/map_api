import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const fetchStats = async () => {
  const response = await axios.get(`${API_BASE_URL}/stats`);
  return response.data;
};

export const fetchUnprocessedRoads = async (limit = 100, stateCode = null, countyFips = null, cityName = null) => {
  const params = { limit };
  if (stateCode) params.state_code = stateCode;
  if (countyFips) params.county_fips = countyFips;
  if (cityName) params.city_name = cityName;
  
  const response = await axios.get(`${API_BASE_URL}/roads/unprocessed`, {
    params
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

// Deprecated - use crawlSingleRoad instead
// export const startCrawl = async (stateCode, limit) => {
//   const response = await axios.post(`${API_BASE_URL}/crawl/start`, null, {
//     params: { state_code: stateCode, limit }
//   });
//   return response.data;
// };

export const searchRoads = async (query, stateCode = null, countyFips = null, limit = 50) => {
  const params = { 
    q: query,
    limit 
  };
  if (stateCode) params.state_code = stateCode;
  if (countyFips) params.county_fips = countyFips;
  
  const response = await axios.get(`${API_BASE_URL}/roads/search`, { params });
  return response.data;
};

export const searchRoadsWithCoords = async (query, stateCode = null, limit = 50) => {
  const params = { 
    q: query,
    limit 
  };
  if (stateCode) params.state_code = stateCode;
  
  const response = await axios.get(`${API_BASE_URL}/roads/search-with-coords`, { params });
  return response.data;
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

// Deprecated - using city-based approach now
// export const fetchCountiesByState = async (stateCode) => {
//   const response = await axios.get(`${API_BASE_URL}/counties/${stateCode}`);
//   return response.data;
// };

export const fetchStatesSummary = async () => {
  const response = await axios.get(`${API_BASE_URL}/states/summary`);
  return response.data;
};

export const fetchTargetCities = async (stateCode = null) => {
  const params = {};
  if (stateCode) params.state_code = stateCode;
  
  const response = await axios.get(`${API_BASE_URL}/roads/target-cities`, { params });
  return response.data;
};

export const fetchRoadsByCity = async (cityName, stateCode, limit = 100) => {
  const response = await axios.get(`${API_BASE_URL}/roads/by-city`, {
    params: {
      city_name: cityName,
      state_code: stateCode,
      limit
    }
  });
  return response.data;
};

export const fetchCityStats = async (cityName, stateCode) => {
  const response = await axios.get(`${API_BASE_URL}/roads/city-stats`, {
    params: {
      city_name: cityName,
      state_code: stateCode
    }
  });
  return response.data;
};