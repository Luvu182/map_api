# Frontend Complete Guide

## Overview
This guide consolidates all frontend-related documentation including current implementation, API updates, and future roadmap.

## Current Implementation

### Technology Stack
- **Frontend**: React 18, Material-UI 5, Tailwind CSS
- **Map**: Leaflet with OpenStreetMap tiles
- **State Management**: React Context API
- **API Client**: Axios
- **Build Tool**: Create React App

### Key Components

#### 1. Authentication System
- **Login Component**: JWT-based authentication
- **Protected Routes**: Using React Router
- **Token Storage**: localStorage
- **Auto-logout**: On 401 responses

#### 2. Dashboard Layout
- **App Bar**: City/state selector, language toggle
- **Map View**: Interactive map with road overlay
- **Road List**: Filterable list with POI stats
- **Crawl Control**: Single/bulk crawl modes

#### 3. City-Only Mode
The frontend now operates in city-only mode for better performance:

```javascript
// Only fetch roads for selected city
const fetchRoads = async (city, state) => {
  const response = await axios.get('/api/roads', {
    params: { city, state, limit: 1000 }
  });
  return response.data;
};
```

### API Endpoints

#### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration (admin only)

#### Roads & POIs
- `GET /api/roads` - Get roads with filters
  - Params: city, state, importance, has_businesses, limit
  - Returns: roads with business statistics
  
- `GET /api/roads/{osm_id}` - Get single road details
  - Returns: road info + nearby POIs

- `GET /api/roads/stats` - Get road statistics
  - Returns: total roads, with businesses, by importance

#### Crawl Management
- `POST /api/crawl` - Start crawl session
  - Body: { osm_id, radius, business_types }
  
- `GET /api/crawl/sessions` - Get crawl history
  - Returns: sessions with statistics

- `GET /api/crawl/session/{id}` - Get session details

### Recent Updates

#### 1. OSM Data Migration (June 2025)
- Switched from TIGER to OSM data
- Added business_type and business_subtype filters
- Integrated POI statistics into road list
- Updated map to show POI density

#### 2. Performance Optimizations
- Implemented city-only data loading
- Added pagination to road list
- Optimized map rendering with clustering
- Reduced API payload sizes

#### 3. UI Enhancements
- Added bulk crawl functionality
- Improved mobile responsiveness
- Added language support (EN/VI)
- Enhanced filter controls

### State Management

#### City Context
```javascript
const CityContext = createContext({
  selectedCity: null,
  selectedState: null,
  roads: [],
  stats: {},
  loading: false,
  error: null
});
```

#### Authentication Context
```javascript
const AuthContext = createContext({
  user: null,
  token: null,
  login: async () => {},
  logout: () => {},
  isAuthenticated: false
});
```

## Component Architecture

### Main Components Tree
```
App.js
├── AuthProvider
├── CityProvider
├── Router
│   ├── Login
│   └── ProtectedRoute
│       └── Dashboard
│           ├── AppBar
│           │   ├── CitySelector
│           │   └── LanguageSelector
│           ├── MapView
│           │   ├── RoadLayer
│           │   └── POILayer
│           ├── RoadList
│           │   ├── FilterControls
│           │   └── RoadItem
│           └── CrawlControl
│               ├── SingleMode
│               └── BulkMode
```

### Key Features Implementation

#### 1. City-Based Road Loading
```javascript
// Load roads when city changes
useEffect(() => {
  if (selectedCity && selectedState) {
    loadCityRoads(selectedCity, selectedState);
  }
}, [selectedCity, selectedState]);
```

#### 2. Real-time Statistics
```javascript
// Update stats after crawl
const handleCrawlComplete = (result) => {
  updateRoadStats(result.road_id, result.new_businesses);
  showNotification('Crawl completed successfully');
};
```

#### 3. Bulk Operations
```javascript
// Bulk crawl with progress tracking
const bulkCrawl = async (roadIds) => {
  for (let i = 0; i < roadIds.length; i++) {
    setProgress((i / roadIds.length) * 100);
    await crawlRoad(roadIds[i]);
  }
};
```

## API Integration

### Request Interceptors
```javascript
// Add auth token to requests
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      logout();
      navigate('/login');
    }
    return Promise.reject(error);
  }
);
```

### Error Handling
```javascript
const apiCall = async (method, url, data) => {
  try {
    setLoading(true);
    const response = await axios[method](url, data);
    return response.data;
  } catch (error) {
    setError(error.response?.data?.detail || 'An error occurred');
    throw error;
  } finally {
    setLoading(false);
  }
};
```

## Future Roadmap

### Planned Features

1. **Advanced Analytics Dashboard**
   - Business growth trends
   - Crawl efficiency metrics
   - ROI calculations
   - Heat maps for opportunity areas

2. **Route Planning**
   - Multi-road route optimization
   - Time-based scheduling
   - Territory management

3. **Collaborative Features**
   - Team management
   - Task assignment
   - Progress sharing

4. **Data Export**
   - CSV/Excel export
   - API integration
   - Automated reports

### Performance Improvements

1. **Virtualization**
   - Virtual scrolling for large lists
   - Map tile caching
   - Lazy loading components

2. **Offline Support**
   - Service worker implementation
   - Offline data caching
   - Background sync

3. **Real-time Updates**
   - WebSocket for live updates
   - Collaborative editing
   - Push notifications

## Development Guidelines

### Code Style
- Use functional components with hooks
- Follow ESLint configuration
- Use Prettier for formatting
- Write unit tests for utils

### Component Guidelines
```javascript
// Component template
const ComponentName = ({ prop1, prop2 }) => {
  const [state, setState] = useState(initialState);
  
  useEffect(() => {
    // Side effects
  }, [dependencies]);
  
  const handleEvent = useCallback(() => {
    // Event handler
  }, [dependencies]);
  
  return (
    <Container>
      {/* JSX */}
    </Container>
  );
};

ComponentName.propTypes = {
  prop1: PropTypes.string.required,
  prop2: PropTypes.number
};
```

### API Integration Pattern
```javascript
// Create API service
const roadService = {
  getAll: (params) => api.get('/roads', { params }),
  getOne: (id) => api.get(`/roads/${id}`),
  update: (id, data) => api.put(`/roads/${id}`, data),
  delete: (id) => api.delete(`/roads/${id}`)
};

// Use in component
const useRoads = () => {
  const [roads, setRoads] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const fetchRoads = async (params) => {
    setLoading(true);
    try {
      const data = await roadService.getAll(params);
      setRoads(data);
    } finally {
      setLoading(false);
    }
  };
  
  return { roads, loading, fetchRoads };
};
```

## Deployment

### Environment Variables
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_MAP_TILE_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png
REACT_APP_DEFAULT_CENTER=[34.0522, -118.2437]
REACT_APP_DEFAULT_ZOOM=12
```

### Build Process
```bash
# Development
npm start

# Production build
npm run build

# Serve production build
serve -s build -l 3000
```

### Docker Deployment
```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```