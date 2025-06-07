# Map Visualization Plan

## Overview
Tích hợp map visualization vào UI hiện tại để hiển thị tiến độ crawl và phân bố dữ liệu.

## Tech Stack
- **Frontend**: React + Mapbox GL JS (hoặc Leaflet)
- **Backend**: FastAPI endpoints trả GeoJSON
- **Database**: PostGIS spatial queries

## Implementation Plan

### 1. Backend API Endpoints

```python
# app/main.py - Thêm các endpoints mới

@app.get("/api/map/counties/{state_code}")
async def get_county_map_data(state_code: str):
    """Get county boundaries with crawl statistics"""
    query = """
        SELECT 
            cb.county_fips,
            cb.county_name,
            ST_AsGeoJSON(cb.boundary) as geometry,
            COUNT(DISTINCT r.osm_id) as total_roads,
            COUNT(DISTINCT b.road_id) as crawled_roads,
            ROUND(100.0 * COUNT(DISTINCT b.road_id) / 
                  NULLIF(COUNT(DISTINCT r.osm_id), 0), 1) as crawl_percentage
        FROM county_boundaries cb
        LEFT JOIN osm_roads r ON cb.county_fips = r.county_fips
        LEFT JOIN businesses b ON r.osm_id = b.road_id
        WHERE cb.state_code = %s
        GROUP BY cb.county_fips, cb.county_name, cb.boundary
    """
    # Return as GeoJSON FeatureCollection

@app.get("/api/map/roads/{county_fips}")
async def get_roads_map_data(county_fips: str, road_type: str = None):
    """Get roads for a county with crawl status"""
    query = """
        SELECT 
            r.osm_id,
            r.name,
            r.highway,
            ST_AsGeoJSON(r.geometry) as geometry,
            COUNT(b.id) as business_count,
            CASE 
                WHEN COUNT(b.id) > 0 THEN 'crawled'
                ELSE 'pending'
            END as status
        FROM osm_roads r
        LEFT JOIN businesses b ON r.osm_id = b.road_id
        WHERE r.county_fips = %s
        GROUP BY r.osm_id
    """
```

### 2. Frontend Components

#### MapView Component
```javascript
// frontend/src/components/MapView.js
import React, { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

const MapView = ({ selectedCounty, selectedState, onCountyClick }) => {
  const mapContainer = useRef(null);
  const map = useRef(null);

  useEffect(() => {
    if (map.current) return; // Initialize once

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/light-v10',
      center: [-95.7129, 37.0902], // US center
      zoom: 4
    });

    // Add counties layer
    map.current.on('load', () => {
      loadCountyData();
    });
  }, []);

  const loadCountyData = async () => {
    const response = await fetch(`/api/map/counties/${selectedState || 'all'}`);
    const data = await response.json();

    map.current.addSource('counties', {
      type: 'geojson',
      data: data
    });

    // Choropleth based on crawl percentage
    map.current.addLayer({
      'id': 'county-fills',
      'type': 'fill',
      'source': 'counties',
      'paint': {
        'fill-color': [
          'interpolate',
          ['linear'],
          ['get', 'crawl_percentage'],
          0, '#f7f7f7',    // Not crawled - light gray
          25, '#fee08b',   // 25% - yellow
          50, '#fdae61',   // 50% - orange
          75, '#f46d43',   // 75% - red-orange
          100, '#d73027'   // 100% - red
        ],
        'fill-opacity': 0.7
      }
    });

    // County borders
    map.current.addLayer({
      'id': 'county-borders',
      'type': 'line',
      'source': 'counties',
      'paint': {
        'line-color': '#627BC1',
        'line-width': 1
      }
    });

    // Click handler
    map.current.on('click', 'county-fills', (e) => {
      const properties = e.features[0].properties;
      onCountyClick(properties.county_fips);
      
      // Show popup
      new mapboxgl.Popup()
        .setLngLat(e.lngLat)
        .setHTML(`
          <h3>${properties.county_name}</h3>
          <p>Total roads: ${properties.total_roads}</p>
          <p>Crawled: ${properties.crawled_roads} (${properties.crawl_percentage}%)</p>
        `)
        .addTo(map.current);
    });
  };

  return <div ref={mapContainer} style={{ height: '500px', width: '100%' }} />;
};
```

#### Integration với Dashboard
```javascript
// frontend/src/components/Dashboard.js
import MapView from './MapView';

function Dashboard() {
  const [selectedCounty, setSelectedCounty] = useState(null);
  const [mapView, setMapView] = useState('counties'); // 'counties' or 'roads'

  return (
    <div className="dashboard-container">
      <div className="left-panel">
        <CrawlControl 
          onCountySelect={setSelectedCounty}
          selectedCounty={selectedCounty}
        />
        <Statistics county={selectedCounty} />
      </div>
      
      <div className="right-panel">
        <div className="map-controls">
          <button onClick={() => setMapView('counties')}>County View</button>
          <button onClick={() => setMapView('roads')}>Road View</button>
        </div>
        
        <MapView 
          selectedCounty={selectedCounty}
          view={mapView}
          onCountyClick={setSelectedCounty}
        />
      </div>
    </div>
  );
}
```

### 3. Real-time Updates

```javascript
// WebSocket for live updates
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000/ws');
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'road_crawled') {
      // Update road color on map
      updateRoadStatus(data.road_id, 'crawled');
      
      // Update county statistics
      updateCountyStats(data.county_fips);
    }
  };
  
  return () => ws.close();
}, []);
```

### 4. Color Schemes

#### County View
- **Gradient by crawl %**: Gray → Yellow → Orange → Red
- **Border**: Blue for selected, gray for others

#### Road View  
- **By status**:
  - Green: Crawled with businesses
  - Blue: Crawled, no businesses
  - Gray: Not crawled
  - Red: Currently crawling (animated)
  
- **By road type**:
  - Highways: Thick lines
  - Major roads: Medium
  - Residential: Thin

### 5. Features

1. **Interactive**:
   - Click county → zoom in + show roads
   - Click road → show business list
   - Hover → show statistics

2. **Filters**:
   - By state
   - By crawl status
   - By road type
   - By business density

3. **Legend**:
   - Color scale for percentages
   - Road type symbols
   - Statistics summary

### 6. Performance Optimization

```javascript
// Load data progressively
const loadRoadsForCounty = async (countyFips) => {
  // Only load when zoomed in enough
  if (map.current.getZoom() < 10) return;
  
  // Load in chunks
  const response = await fetch(`/api/map/roads/${countyFips}?limit=1000`);
  // ...
};

// Cluster businesses at low zoom
map.current.addSource('businesses', {
  type: 'geojson',
  data: businessData,
  cluster: true,
  clusterMaxZoom: 14,
  clusterRadius: 50
});
```

### 7. Alternative: Leaflet (Free)

```javascript
// Using Leaflet instead of Mapbox
import L from 'leaflet';

const map = L.map('map').setView([37.0902, -95.7129], 4);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Load GeoJSON
fetch('/api/map/counties/all')
  .then(res => res.json())
  .then(data => {
    L.geoJSON(data, {
      style: feature => ({
        fillColor: getColor(feature.properties.crawl_percentage),
        weight: 1,
        opacity: 1,
        color: 'white',
        fillOpacity: 0.7
      }),
      onEachFeature: (feature, layer) => {
        layer.on('click', () => {
          onCountyClick(feature.properties.county_fips);
        });
      }
    }).addTo(map);
  });
```

## Next Steps

1. **Phase 1**: Basic county choropleth
2. **Phase 2**: Road-level visualization  
3. **Phase 3**: Real-time updates
4. **Phase 4**: Business clustering
5. **Phase 5**: Analytics dashboard

## Resources

- [Mapbox GL JS Docs](https://docs.mapbox.com/mapbox-gl-js/guides/)
- [Leaflet Docs](https://leafletjs.com/reference.html)
- [PostGIS GeoJSON](https://postgis.net/docs/ST_AsGeoJSON.html)
- [D3.js for advanced viz](https://d3js.org/)