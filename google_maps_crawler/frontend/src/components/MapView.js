import React, { useState, useCallback } from 'react';
import { GoogleMap, LoadScript, Marker, InfoWindow } from '@react-google-maps/api';

const MapView = ({ onRoadSelect, selectedRoad }) => {
  const [selectedBusiness, setSelectedBusiness] = useState(null);
  const [mapCenter, setMapCenter] = useState({ lat: 40.7128, lng: -74.0060 }); // NYC default
  
  // Mock data for businesses
  const businesses = [
    { id: 1, name: 'Joe\'s Pizza', lat: 40.7128, lng: -74.0060, rating: 4.5, types: ['restaurant'] },
    { id: 2, name: 'Central Pharmacy', lat: 40.7135, lng: -74.0055, rating: 4.2, types: ['pharmacy'] },
    { id: 3, name: 'Quick Stop Market', lat: 40.7120, lng: -74.0065, rating: 3.9, types: ['store'] }
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
    console.log('Map loaded');
  }, []);

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="bg-white p-4 rounded-lg shadow">
        <div className="flex space-x-4">
          <input
            type="text"
            placeholder="Search for a road..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">All States</option>
            <option value="NY">New York</option>
            <option value="CA">California</option>
            <option value="TX">Texas</option>
          </select>
          <button className="px-6 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600">
            Search
          </button>
        </div>
      </div>

      {/* Map */}
      <div className="bg-white p-4 rounded-lg shadow">
        <LoadScript googleMapsApiKey={process.env.REACT_APP_GOOGLE_MAPS_API_KEY || ''}>
          <GoogleMap
            mapContainerStyle={mapContainerStyle}
            center={mapCenter}
            zoom={15}
            options={options}
            onLoad={onLoad}
          >
            {/* Business Markers */}
            {businesses.map((business) => (
              <Marker
                key={business.id}
                position={{ lat: business.lat, lng: business.lng }}
                onClick={() => setSelectedBusiness(business)}
              />
            ))}

            {/* Info Window */}
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
        <h3 className="font-semibold mb-2">Legend</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
          <div className="flex items-center">
            <div className="w-4 h-4 bg-red-500 rounded-full mr-2"></div>
            <span>Restaurants</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-blue-500 rounded-full mr-2"></div>
            <span>Stores</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-green-500 rounded-full mr-2"></div>
            <span>Services</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-purple-500 rounded-full mr-2"></div>
            <span>Healthcare</span>
          </div>
        </div>
      </div>

      {/* Selected Road Info */}
      {selectedRoad && (
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="font-semibold mb-2">Selected Road</h3>
          <p className="text-sm">Name: {selectedRoad.name}</p>
          <p className="text-sm">State: {selectedRoad.state_code}</p>
          <p className="text-sm">Category: {selectedRoad.road_category}</p>
        </div>
      )}
    </div>
  );
};

export default MapView;