import React, { useState, useEffect } from 'react';
import { fetchBusinessesForRoad } from '../api/crawler';

const BusinessList = ({ selectedRoad }) => {
  const [businesses, setBusinesses] = useState([]);
  const [filter, setFilter] = useState('all');
  const [sortBy, setSortBy] = useState('rating');

  // Mock data - in production would fetch from API
  const mockBusinesses = [
    {
      place_id: '1',
      name: 'Starbucks Coffee',
      formatted_address: '123 Broadway, New York, NY',
      rating: 4.2,
      user_ratings_total: 856,
      types: ['cafe', 'food'],
      price_level: 2,
      road_name: 'Broadway',
      distance_to_road: 15
    },
    {
      place_id: '2',
      name: 'CVS Pharmacy',
      formatted_address: '456 Broadway, New York, NY',
      rating: 3.8,
      user_ratings_total: 234,
      types: ['pharmacy', 'store'],
      price_level: 2,
      road_name: 'Broadway',
      distance_to_road: 20
    },
    {
      place_id: '3',
      name: 'Broadway Pizza',
      formatted_address: '789 Broadway, New York, NY',
      rating: 4.6,
      user_ratings_total: 1523,
      types: ['restaurant', 'food'],
      price_level: 1,
      road_name: 'Broadway',
      distance_to_road: 5
    }
  ];

  useEffect(() => {
    // In production, fetch real data
    setBusinesses(mockBusinesses);
  }, [selectedRoad]);

  const businessTypes = [
    { value: 'all', label: 'All Types' },
    { value: 'restaurant', label: 'Restaurants' },
    { value: 'store', label: 'Stores' },
    { value: 'cafe', label: 'Cafes' },
    { value: 'pharmacy', label: 'Pharmacy' },
    { value: 'bank', label: 'Banks' }
  ];

  const filteredBusinesses = businesses
    .filter(b => filter === 'all' || b.types.includes(filter))
    .sort((a, b) => {
      if (sortBy === 'rating') return b.rating - a.rating;
      if (sortBy === 'reviews') return b.user_ratings_total - a.user_ratings_total;
      if (sortBy === 'distance') return a.distance_to_road - b.distance_to_road;
      return 0;
    });

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow">
        <div className="flex flex-wrap gap-4 items-center">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Business Type
            </label>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {businessTypes.map(type => (
                <option key={type.value} value={type.value}>{type.label}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Sort By
            </label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="rating">Rating</option>
              <option value="reviews">Review Count</option>
              <option value="distance">Distance to Road</option>
            </select>
          </div>
          
          <div className="ml-auto">
            <p className="text-sm text-gray-600">
              Showing {filteredBusinesses.length} businesses
            </p>
          </div>
        </div>
      </div>

      {/* Business Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredBusinesses.map(business => (
          <BusinessCard key={business.place_id} business={business} />
        ))}
      </div>

      {/* Export Options */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="font-semibold mb-3">Export Data</h3>
        <div className="flex gap-4">
          <button className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600">
            Export to CSV
          </button>
          <button className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
            Export to JSON
          </button>
          <button className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600">
            Generate Report
          </button>
        </div>
      </div>
    </div>
  );
};

const BusinessCard = ({ business }) => {
  const getPriceLevelText = (level) => {
    if (!level) return 'N/A';
    return '$'.repeat(level);
  };

  const getTypeIcon = (types) => {
    if (types.includes('restaurant')) return '🍽️';
    if (types.includes('cafe')) return '☕';
    if (types.includes('store')) return '🛒';
    if (types.includes('pharmacy')) return '💊';
    if (types.includes('bank')) return '🏦';
    return '📍';
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="font-semibold text-lg flex items-center gap-2">
            <span className="text-2xl">{getTypeIcon(business.types)}</span>
            {business.name}
          </h3>
          <p className="text-sm text-gray-600 mt-1">{business.formatted_address}</p>
          
          <div className="mt-3 flex items-center gap-4 text-sm">
            <div className="flex items-center">
              <span className="text-yellow-500">★</span>
              <span className="ml-1">{business.rating}</span>
              <span className="text-gray-500 ml-1">({business.user_ratings_total})</span>
            </div>
            
            <div className="text-gray-600">
              {getPriceLevelText(business.price_level)}
            </div>
          </div>
          
          <div className="mt-2 flex flex-wrap gap-1">
            {business.types.slice(0, 3).map(type => (
              <span
                key={type}
                className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded"
              >
                {type}
              </span>
            ))}
          </div>
          
          <div className="mt-3 text-xs text-gray-500">
            {business.distance_to_road}m from {business.road_name}
          </div>
        </div>
      </div>
    </div>
  );
};

export default BusinessList;