import React, { useState, useCallback, useEffect } from 'react';
import { GoogleMap, LoadScript, Marker, InfoWindow, Polyline } from '@react-google-maps/api';
import { searchRoadsWithCoords, fetchBusinessesForRoad } from '../api/crawler';
import { useLanguage } from '../contexts/LanguageContext';
import { t } from '../translations/translations';

const MapView = ({ onRoadSelect, selectedRoad }) => {
  const { language } = useLanguage();
  const [selectedBusiness, setSelectedBusiness] = useState(null);
  const [mapCenter, setMapCenter] = useState({ lat: 37.7749, lng: -122.4194 }); // San Francisco default
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedState, setSelectedState] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [businesses, setBusinesses] = useState([]);
  const [selectedRoadData, setSelectedRoadData] = useState(null);
  const [mapInstance, setMapInstance] = useState(null);

  // States list
  const states = [
    { code: 'AL', name: 'Alabama' },
    { code: 'CA', name: 'California' },
    { code: 'FL', name: 'Florida' },
    { code: 'GA', name: 'Georgia' },
    { code: 'IL', name: 'Illinois' },
    { code: 'TX', name: 'Texas' },
    { code: 'NY', name: 'New York' },
    // Add more states as needed
  ];

  const mapContainerStyle = {
    width: '100%',
    height: '600px'
  };

  const options = {
    disableDefaultUI: false,
    zoomControl: true,
    mapTypeControl: true,
    scaleControl: true,
    streetViewControl: true,
    rotateControl: true,
    fullscreenControl: true
  };

  const onLoad = useCallback((map) => {
    setMapInstance(map);
    console.log('Map loaded');
  }, []);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setIsSearching(true);
    try {
      const results = await searchRoadsWithCoords(searchQuery, selectedState || null, 10);
      setSearchResults(results.results || []);
      
      // If we have results, center map on first result
      if (results.results && results.results.length > 0) {
        const firstResult = results.results[0];
        if (firstResult.center_lat && firstResult.center_lon) {
          const newCenter = { 
            lat: firstResult.center_lat, 
            lng: firstResult.center_lon 
          };
          setMapCenter(newCenter);
          if (mapInstance) {
            mapInstance.panTo(newCenter);
            mapInstance.setZoom(14);
          }
        }
      }
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const handleRoadSelect = async (road) => {
    setSelectedRoadData(road);
    if (onRoadSelect) {
      onRoadSelect(road);
    }
    
    // Center map on road
    if (road.center_lat && road.center_lon) {
      const newCenter = { lat: road.center_lat, lng: road.center_lon };
      setMapCenter(newCenter);
      if (mapInstance) {
        mapInstance.panTo(newCenter);
        mapInstance.setZoom(15);
      }
    }
    
    // TODO: Load businesses for this road from crawl data
    // For now, showing mock data
    setBusinesses([]);
  };

  const getMarkerIcon = (roadType) => {
    const iconBase = 'https://maps.google.com/mapfiles/kml/shapes/';
    switch (roadType) {
      case 'primary':
      case 'secondary':
        return iconBase + 'placemark_circle_highlight.png';
      case 'residential':
        return iconBase + 'placemark_circle.png';
      default:
        return null;
    }
  };

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="bg-white p-4 rounded-lg shadow">
        <div className="flex space-x-4">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            placeholder={language === 'vi' ? "Tìm kiếm đường..." : "Search for a road..."}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select 
            value={selectedState}
            onChange={(e) => setSelectedState(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">{language === 'vi' ? "Tất cả bang" : "All States"}</option>
            {states.map(state => (
              <option key={state.code} value={state.code}>{state.name}</option>
            ))}
          </select>
          <button 
            onClick={handleSearch}
            disabled={isSearching}
            className="px-6 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:bg-gray-400"
          >
            {isSearching ? (language === 'vi' ? "Đang tìm..." : "Searching...") : (language === 'vi' ? "Tìm kiếm" : "Search")}
          </button>
        </div>
        
        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="mt-4 max-h-40 overflow-y-auto border-t pt-2">
            <div className="text-sm text-gray-600 mb-2">
              {language === 'vi' ? `Tìm thấy ${searchResults.length} kết quả` : `Found ${searchResults.length} results`}
            </div>
            {searchResults.map((road) => (
              <div 
                key={road.osm_id}
                onClick={() => handleRoadSelect(road)}
                className="p-2 hover:bg-gray-100 cursor-pointer rounded"
              >
                <div className="font-medium">{road.name}</div>
                <div className="text-sm text-gray-600">
                  {road.city_name ? `${road.city_name}, ` : ''}{road.state_code} • {road.highway}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Map */}
      <div className="bg-white p-4 rounded-lg shadow">
        <LoadScript googleMapsApiKey={process.env.REACT_APP_GOOGLE_MAPS_API_KEY || ''}>
          <GoogleMap
            mapContainerStyle={mapContainerStyle}
            center={mapCenter}
            zoom={13}
            options={options}
            onLoad={onLoad}
          >
            {/* Road Markers from Search Results */}
            {searchResults.map((road) => (
              road.center_lat && road.center_lon && (
                <Marker
                  key={road.osm_id}
                  position={{ lat: road.center_lat, lng: road.center_lon }}
                  onClick={() => handleRoadSelect(road)}
                  icon={getMarkerIcon(road.highway)}
                  title={road.name}
                />
              )
            ))}

            {/* Business Markers */}
            {businesses.map((business) => (
              <Marker
                key={business.place_id}
                position={{ lat: business.lat, lng: business.lng }}
                onClick={() => setSelectedBusiness(business)}
              />
            ))}

            {/* Info Window for Selected Road */}
            {selectedRoadData && selectedRoadData.center_lat && selectedRoadData.center_lon && (
              <InfoWindow
                position={{ lat: selectedRoadData.center_lat, lng: selectedRoadData.center_lon }}
                onCloseClick={() => setSelectedRoadData(null)}
              >
                <div className="p-2">
                  <h3 className="font-semibold">{selectedRoadData.name}</h3>
                  <p className="text-sm text-gray-600">Type: {selectedRoadData.highway}</p>
                  <p className="text-sm text-gray-600">
                    {selectedRoadData.city_name ? `${selectedRoadData.city_name}, ` : ''}{selectedRoadData.state_code}
                  </p>
                  {selectedRoadData.total_length_km && (
                    <p className="text-sm text-gray-600">Length: {selectedRoadData.total_length_km.toFixed(2)} km</p>
                  )}
                </div>
              </InfoWindow>
            )}

            {/* Info Window for Business */}
            {selectedBusiness && (
              <InfoWindow
                position={{ lat: selectedBusiness.lat, lng: selectedBusiness.lng }}
                onCloseClick={() => setSelectedBusiness(null)}
              >
                <div className="p-2">
                  <h3 className="font-semibold">{selectedBusiness.name}</h3>
                  <p className="text-sm text-gray-600">Rating: {selectedBusiness.rating}/5</p>
                  <p className="text-sm text-gray-600">Type: {selectedBusiness.types.join(', ')}</p>
                </div>
              </InfoWindow>
            )}
          </GoogleMap>
        </LoadScript>
      </div>

      {/* Map Legend */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="font-semibold mb-2">{language === 'vi' ? 'Chú thích' : 'Legend'}</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
          <div className="flex items-center">
            <div className="w-4 h-4 bg-red-500 rounded-full mr-2"></div>
            <span>{language === 'vi' ? 'Đường chính' : 'Major Roads'}</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-blue-500 rounded-full mr-2"></div>
            <span>{language === 'vi' ? 'Đường phụ' : 'Secondary Roads'}</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-green-500 rounded-full mr-2"></div>
            <span>{language === 'vi' ? 'Đường dân cư' : 'Residential'}</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-purple-500 rounded-full mr-2"></div>
            <span>{language === 'vi' ? 'Businesses' : 'Businesses'}</span>
          </div>
        </div>
      </div>

      {/* Selected Road Info */}
      {selectedRoadData && (
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="font-semibold mb-2">{language === 'vi' ? 'Thông tin đường' : 'Selected Road'}</h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className="text-gray-600">{language === 'vi' ? 'Tên:' : 'Name:'}</span>
              <span className="ml-2 font-medium">{selectedRoadData.name}</span>
            </div>
            <div>
              <span className="text-gray-600">{language === 'vi' ? 'Loại:' : 'Type:'}</span>
              <span className="ml-2">{selectedRoadData.highway}</span>
            </div>
            <div>
              <span className="text-gray-600">{language === 'vi' ? 'Vị trí:' : 'Location:'}</span>
              <span className="ml-2">
                {selectedRoadData.city_name ? `${selectedRoadData.city_name}, ` : ''}{selectedRoadData.state_code}
              </span>
            </div>
            {selectedRoadData.total_length_km && (
              <div>
                <span className="text-gray-600">{language === 'vi' ? 'Chiều dài:' : 'Length:'}</span>
                <span className="ml-2">{selectedRoadData.total_length_km.toFixed(2)} km</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default MapView;