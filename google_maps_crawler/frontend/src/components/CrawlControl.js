import React, { useState, useEffect, useRef, useMemo } from 'react';
import { startCrawl, fetchUnprocessedRoads, fetchCountiesByState, fetchStatesSummary, fetchCrawlStatus, crawlSingleRoad, searchRoads } from '../api/crawler';
import { getCountyName } from '../data/countyNames';

const CrawlControl = ({ onCrawlStart }) => {
  const [selectedState, setSelectedState] = useState('');
  const [selectedCounty, setSelectedCounty] = useState('');
  const [selectedRoadTypes, setSelectedRoadTypes] = useState(new Set(['tertiary', 'residential', 'living_street'])); // Default to local business streets
  const [businessKeyword, setBusinessKeyword] = useState('');
  const [roadNameFilter, setRoadNameFilter] = useState('');
  const [minRoadLength, setMinRoadLength] = useState(1); // Minimum road length in km
  const [businessDensity, setBusinessDensity] = useState('all'); // all, high, medium
  const [isLoading, setIsLoading] = useState(false);
  const [allRoads, setAllRoads] = useState([]);
  const [counties, setCounties] = useState([]);
  const [message, setMessage] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [crawlStatus, setCrawlStatus] = useState({});
  const [showOnlyUncrawled, setShowOnlyUncrawled] = useState(true); // Default to show only uncrawled
  const [crawlingRoads, setCrawlingRoads] = useState(new Set());
  const [sortBy, setSortBy] = useState('potential'); // potential, name, length, type
  const [hasSearched, setHasSearched] = useState(false); // Track if user has searched
  const roadsPerPage = 50;

  // All 50 states from database
  const states = [
    { code: 'AL', name: 'Alabama' },
    { code: 'AK', name: 'Alaska' },
    { code: 'AZ', name: 'Arizona' },
    { code: 'AR', name: 'Arkansas' },
    { code: 'CA', name: 'California' },
    { code: 'CO', name: 'Colorado' },
    { code: 'CT', name: 'Connecticut' },
    { code: 'DC', name: 'District of Columbia' },
    { code: 'FL', name: 'Florida' },
    { code: 'GA', name: 'Georgia' },
    { code: 'HI', name: 'Hawaii' },
    { code: 'ID', name: 'Idaho' },
    { code: 'IL', name: 'Illinois' },
    { code: 'IN', name: 'Indiana' },
    { code: 'IA', name: 'Iowa' },
    { code: 'KS', name: 'Kansas' },
    { code: 'KY', name: 'Kentucky' },
    { code: 'LA', name: 'Louisiana' },
    { code: 'ME', name: 'Maine' },
    { code: 'MD', name: 'Maryland' },
    { code: 'MA', name: 'Massachusetts' },
    { code: 'MI', name: 'Michigan' },
    { code: 'MN', name: 'Minnesota' },
    { code: 'MS', name: 'Mississippi' },
    { code: 'MO', name: 'Missouri' },
    { code: 'MT', name: 'Montana' },
    { code: 'NE', name: 'Nebraska' },
    { code: 'NV', name: 'Nevada' },
    { code: 'NH', name: 'New Hampshire' },
    { code: 'NJ', name: 'New Jersey' },
    { code: 'NM', name: 'New Mexico' },
    { code: 'NY', name: 'New York' },
    { code: 'NC', name: 'North Carolina' },
    { code: 'ND', name: 'North Dakota' },
    { code: 'OH', name: 'Ohio' },
    { code: 'OK', name: 'Oklahoma' },
    { code: 'OR', name: 'Oregon' },
    { code: 'PA', name: 'Pennsylvania' },
    { code: 'RI', name: 'Rhode Island' },
    { code: 'SC', name: 'South Carolina' },
    { code: 'SD', name: 'South Dakota' },
    { code: 'TN', name: 'Tennessee' },
    { code: 'TX', name: 'Texas' },
    { code: 'UT', name: 'Utah' },
    { code: 'VA', name: 'Virginia' },
    { code: 'WA', name: 'Washington' },
    { code: 'WV', name: 'West Virginia' },
    { code: 'WI', name: 'Wisconsin' },
    { code: 'WY', name: 'Wyoming' }
  ];

  // Road type categories for OSM data - ordered by business potential
  const roadCategories = {
    local: {
      label: 'Local Business Streets',
      types: ['tertiary', 'residential', 'living_street'],
      description: 'Main St, Broadway, downtown streets',
      businessPotential: 'very-high'
    },
    major: {
      label: 'Major Commercial Roads',
      types: ['primary', 'secondary'],
      description: 'Main arterials, State Routes',
      businessPotential: 'high'
    },
    highways: {
      label: 'Highways & Interstates',
      types: ['motorway', 'trunk'],
      description: 'I-5, I-95, US highways',
      businessPotential: 'medium'
    },
    service: {
      label: 'Service & Access Roads',
      types: ['service', 'unclassified'],
      description: 'Mall access, parking lots',
      businessPotential: 'low'
    }
  };

  // Popular business keywords
  const popularKeywords = [
    'restaurant', 'clothing store', 'grocery store', 'coffee shop',
    'pharmacy', 'gas station', 'hotel', 'bank', 'salon', 'gym'
  ];

  useEffect(() => {
    loadStatesSummary();
  }, []);

  useEffect(() => {
    if (selectedState) {
      loadCountiesForState(selectedState);
    }
  }, [selectedState]);

  // Reset search results when key filters change
  useEffect(() => {
    setHasSearched(false);
    setAllRoads([]);
  }, [selectedState, businessKeyword]);

  // Use refs to track and control requests
  const abortControllerRef = useRef(null);
  const lastRequestTimeRef = useRef(0);
  
  // No auto-search - user must click Search button

  // Toggle road type selection
  const toggleRoadType = (types) => {
    const newSelectedTypes = new Set(selectedRoadTypes);
    types.forEach(type => {
      if (newSelectedTypes.has(type)) {
        newSelectedTypes.delete(type);
      } else {
        newSelectedTypes.add(type);
      }
    });
    setSelectedRoadTypes(newSelectedTypes);
  };

  const loadRoads = async () => {
    try {
      setIsLoading(true);
      
      // Use search API if road name filter is provided
      if (roadNameFilter) {
        const searchResults = await searchRoads(roadNameFilter, selectedState, selectedCounty, 200);
        setAllRoads(searchResults.results || []);
      } else {
        // Fetch all roads with filters
        const data = await fetchUnprocessedRoads(1000, selectedState, selectedCounty);
        setAllRoads(data.roads || []);
      }
      
      // Get crawl status for the business keyword
      if (businessKeyword && selectedState) {
        const statusData = await fetchCrawlStatus(selectedState, selectedCounty, businessKeyword);
        setCrawlStatus(statusData);
      }
    } catch (error) {
      console.error('Failed to load roads:', error);
      setMessage('Error loading roads: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const loadCountiesForState = async (stateCode) => {
    try {
      const data = await fetchCountiesByState(stateCode);
      setCounties(data.counties || data || []);
    } catch (error) {
      console.error('Failed to load counties:', error);
      setCounties([]);
    }
  };

  const loadStatesSummary = async () => {
    try {
      const data = await fetchStatesSummary();
      // Could enhance state list with actual road counts
    } catch (error) {
      console.error('Failed to load states summary:', error);
    }
  };

  const handleSearch = async () => {
    setCurrentPage(1);
    setHasSearched(true);
    await loadRoads();
  };

  const handleCrawlSingleRoad = async (road) => {
    const roadId = road.osm_id;
    
    setCrawlingRoads(prev => new Set([...prev, roadId]));
    
    try {
      const result = await crawlSingleRoad(roadId, businessKeyword);
      
      const newStatus = { ...crawlStatus };
      newStatus[roadId] = { [businessKeyword]: 'processing' };
      setCrawlStatus(newStatus);
      
      setMessage(`Started crawling ${road.name} for "${businessKeyword}"`);
      
      // Refresh status after delay
      setTimeout(async () => {
        const statusData = await fetchCrawlStatus(selectedState, selectedCounty, businessKeyword);
        setCrawlStatus(statusData);
      }, 3000);
      
    } catch (error) {
      const newStatus = { ...crawlStatus };
      newStatus[roadId] = { [businessKeyword]: 'failed' };
      setCrawlStatus(newStatus);
      
      setMessage(`Error crawling ${road.name}: ${error.message}`);
    } finally {
      setCrawlingRoads(prev => {
        const newSet = new Set(prev);
        newSet.delete(roadId);
        return newSet;
      });
    }
  };

  // Calculate business potential score
  const getBusinessPotential = (road) => {
    let score = 0;
    
    // Road type score
    if (['primary', 'secondary', 'tertiary'].includes(road.highway)) score += 3;
    else if (['residential', 'living_street'].includes(road.highway)) score += 2;
    else if (['motorway', 'trunk'].includes(road.highway)) score += 1;
    
    // Length score (optimal: 2-10km)
    const length = road.total_length_km || road.length_km || 0;
    if (length >= 2 && length <= 10) score += 2;
    else if (length > 0 && length < 2) score += 1;
    
    // Name score
    if (road.name) {
      const businessIndicators = ['main', 'broadway', 'market', 'commercial', 'downtown', 'center', 'plaza'];
      if (businessIndicators.some(indicator => road.name.toLowerCase().includes(indicator))) {
        score += 2;
      }
    }
    
    // Population density could be added here if available
    
    return score;
  };

  // Use memo to prevent unnecessary recalculations
  const filteredAndSortedRoads = useMemo(() => {
    
    // Filter roads based on criteria
    const filtered = allRoads.filter(road => {
      // Filter by road types (client-side because API doesn't support this yet)
      if (selectedRoadTypes.size > 0 && !selectedRoadTypes.has(road.highway)) return false;
      
      // Filter by minimum length (client-side)
      const roadLength = road.total_length_km || road.length_km || 0;
      if (minRoadLength > 0 && roadLength < minRoadLength) return false;
      
      // Filter by business density (client-side)
      if (businessDensity !== 'all') {
        const potential = getBusinessPotential(road);
        if (businessDensity === 'high' && potential < 4) return false;
        if (businessDensity === 'medium' && (potential < 2 || potential > 4)) return false;
      }
      
      // Filter by crawl status
      const roadStatus = crawlStatus[road.osm_id]?.[businessKeyword];
      if (showOnlyUncrawled && roadStatus && roadStatus !== 'failed') return false;
      
      return true;
    });

    // Sort roads based on selected criteria
    const sorted = [...filtered].sort((a, b) => {
      switch (sortBy) {
        case 'potential':
          return getBusinessPotential(b) - getBusinessPotential(a);
        case 'name':
          return (a.name || '').localeCompare(b.name || '');
        case 'length':
          return (b.total_length_km || b.length_km || 0) - (a.total_length_km || a.length_km || 0);
        case 'type':
          return (a.highway || '').localeCompare(b.highway || '');
        default:
          return getBusinessPotential(b) - getBusinessPotential(a);
      }
    });
    
    return sorted;
  }, [allRoads, selectedRoadTypes, minRoadLength, businessDensity, crawlStatus, businessKeyword, showOnlyUncrawled, sortBy]);

  // Pagination
  const totalPages = Math.ceil(filteredAndSortedRoads.length / roadsPerPage);
  const paginatedRoads = filteredAndSortedRoads.slice(
    (currentPage - 1) * roadsPerPage,
    currentPage * roadsPerPage
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-2xl font-bold mb-2">Business Discovery Crawler</h2>
        <p className="text-gray-600">
          Find businesses along US roads using Google Maps. Focus on high-potential areas for better results.
        </p>
      </div>

      {/* Quick Start Guide */}
      <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
        <div className="flex">
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">Quick Tips for Finding Businesses:</h3>
            <div className="mt-2 text-sm text-blue-700">
              <ul className="list-disc list-inside space-y-1">
                <li>Start with popular keywords: restaurant, store, pharmacy</li>
                <li>Focus on "Major Commercial Roads" and "Local Business Streets" for best results</li>
                <li>Roads named "Main Street", "Broadway", or with "Plaza/Center" often have more businesses</li>
                <li>Filter by minimum road length (2-10 km is optimal)</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Main Search Section */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Search Configuration</h3>
        
        {/* Business Keyword - Most Important */}
        <div className="mb-6 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            1. What type of business are you looking for? <span className="text-red-500">*</span>
          </label>
          <div className="flex gap-2 mb-3">
            <input
              type="text"
              value={businessKeyword}
              onChange={(e) => setBusinessKeyword(e.target.value)}
              placeholder="e.g. restaurant, clothing store, pharmacy..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <span className="text-xs text-gray-500">Popular searches:</span>
            {popularKeywords.map(keyword => (
              <button
                key={keyword}
                onClick={() => setBusinessKeyword(keyword)}
                className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
              >
                {keyword}
              </button>
            ))}
          </div>
        </div>

        {/* Location Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              2. State <span className="text-red-500">*</span>
            </label>
            <select
              value={selectedState}
              onChange={(e) => {
                setSelectedState(e.target.value);
                setSelectedCounty('');
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select a state...</option>
              {states.map(state => (
                <option key={state.code} value={state.code}>
                  {state.name}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              3. County (Optional)
            </label>
            <select
              value={selectedCounty}
              onChange={(e) => setSelectedCounty(e.target.value)}
              disabled={!selectedState}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
            >
              <option value="">All Counties</option>
              {counties.map(county => (
                <option key={county.county_fips} value={county.county_fips}>
                  {county.county_name || getCountyName(county.county_fips)}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Advanced Filters Section - Open by default */}
        <details className="mb-6" open>
          <summary className="cursor-pointer text-sm font-medium text-gray-700 mb-3 hover:text-gray-900">
            Advanced Filters & Options
          </summary>
          
          <div className="mt-4 space-y-4 p-4 bg-gray-50 rounded-lg">
            {/* Road Type Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Road Types (Pre-selected for best results)
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {Object.entries(roadCategories).map(([key, category]) => (
                  <div key={key} className="flex items-start space-x-2 p-2 rounded hover:bg-gray-100">
                    <input
                      type="checkbox"
                      id={`road-type-${key}`}
                      className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      checked={category.types.every(type => selectedRoadTypes.has(type))}
                      onChange={() => toggleRoadType(category.types)}
                    />
                    <label htmlFor={`road-type-${key}`} className="flex-1 cursor-pointer">
                      <div className="font-medium text-sm">{category.label}</div>
                      <div className="text-xs text-gray-500">{category.description}</div>
                      <div className="text-xs mt-1">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          category.businessPotential === 'very-high' ? 'bg-green-100 text-green-800' :
                          category.businessPotential === 'high' ? 'bg-blue-100 text-blue-800' :
                          category.businessPotential === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {category.businessPotential} business potential
                        </span>
                      </div>
                    </label>
                  </div>
                ))}
              </div>
            </div>

            {/* Road Name Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search by Road Name
              </label>
              <input
                type="text"
                value={roadNameFilter}
                onChange={(e) => setRoadNameFilter(e.target.value)}
                placeholder="e.g. Main Street, Broadway, Market Street..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="mt-1 text-xs text-gray-500">
                Tip: "Main Street" and "Broadway" typically have many businesses
              </p>
            </div>

            {/* Additional Filters */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Minimum Road Length
                </label>
                <select
                  value={minRoadLength}
                  onChange={(e) => setMinRoadLength(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={0}>Any length</option>
                  <option value={1}>At least 1 km</option>
                  <option value={2}>At least 2 km (Recommended)</option>
                  <option value={5}>At least 5 km</option>
                  <option value={10}>At least 10 km</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Business Density Filter
                </label>
                <select
                  value={businessDensity}
                  onChange={(e) => setBusinessDensity(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All roads</option>
                  <option value="high">High potential only</option>
                  <option value="medium">Medium potential</option>
                </select>
              </div>
            </div>
          </div>
        </details>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <button
            onClick={handleSearch}
            disabled={!businessKeyword || !selectedState || isLoading}
            className="flex-1 px-6 py-3 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:bg-gray-400 font-medium flex items-center justify-center"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Searching...
              </>
            ) : (
              'Search Roads'
            )}
          </button>
          
          <label className="flex items-center px-4 py-2 border border-gray-300 rounded-md cursor-pointer hover:bg-gray-50">
            <input
              type="checkbox"
              checked={showOnlyUncrawled}
              onChange={(e) => setShowOnlyUncrawled(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded mr-2"
            />
            <span className="text-sm">Show only uncrawled</span>
          </label>
        </div>
        
        {message && (
          <div className={`mt-4 p-3 rounded ${message.includes('Error') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
            {message}
          </div>
        )}
      </div>

      {/* Results Section - Only show after user clicks Search */}
      {hasSearched && businessKeyword && selectedState && (
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">
              {isLoading ? 'Loading...' : (
                <>
                  {filteredAndSortedRoads.length} Roads Found
                  {selectedState && ` in ${states.find(s => s.code === selectedState)?.name}`}
                  {selectedCounty && `, ${getCountyName(selectedCounty)}`}
                </>
              )}
            </h3>
            {!isLoading && filteredAndSortedRoads.length > 0 && (
              <div className="flex items-center space-x-4">
                <label className="text-sm text-gray-500">Sort by:</label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="text-sm px-2 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="potential">Business Potential</option>
                  <option value="name">Road Name</option>
                  <option value="length">Road Length</option>
                  <option value="type">Road Type</option>
                </select>
              </div>
            )}
          </div>
          
          {!isLoading && filteredAndSortedRoads.length > 0 ? (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Road Name</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Business Potential</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Length</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Location</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Action</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {paginatedRoads.map((road) => {
                      const status = crawlStatus[road.osm_id]?.[businessKeyword];
                      const isCrawling = crawlingRoads.has(road.osm_id);
                      const potential = getBusinessPotential(road);
                      
                      return (
                        <tr key={road.osm_id} className="hover:bg-gray-50">
                          <td className="px-4 py-3">
                            <div className="text-sm font-medium text-gray-900">
                              {road.name || 'Unnamed Road'}
                            </div>
                            {road.ref && (
                              <div className="text-xs text-gray-500">Route: {road.ref}</div>
                            )}
                          </td>
                          <td className="px-4 py-3 text-sm">
                            <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                              ['primary', 'secondary'].includes(road.highway) ? 'bg-blue-100 text-blue-800' :
                              ['residential', 'tertiary'].includes(road.highway) ? 'bg-green-100 text-green-800' :
                              ['motorway', 'trunk'].includes(road.highway) ? 'bg-purple-100 text-purple-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {road.highway}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm">
                            <div className="flex items-center">
                              <div className="flex space-x-1">
                                {[...Array(5)].map((_, i) => (
                                  <div
                                    key={i}
                                    className={`h-2 w-2 rounded-full ${
                                      i < potential ? 'bg-green-500' : 'bg-gray-300'
                                    }`}
                                  />
                                ))}
                              </div>
                              <span className="ml-2 text-xs text-gray-500">
                                {potential >= 5 ? 'Very High' :
                                 potential >= 4 ? 'High' :
                                 potential >= 2 ? 'Medium' : 'Low'}
                              </span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-500">
                            {road.total_length_km || road.length_km ? `${(road.total_length_km || road.length_km).toFixed(1)} km` : 'N/A'}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-500">
                            {getCountyName(road.county_fips)}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                              isCrawling ? 'bg-yellow-100 text-yellow-800' :
                              status === 'completed' ? 'bg-green-100 text-green-800' :
                              status === 'failed' ? 'bg-red-100 text-red-800' :
                              status === 'processing' ? 'bg-blue-100 text-blue-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {isCrawling ? 'Starting...' :
                               status === 'completed' ? '✓ Complete' :
                               status === 'processing' ? 'Processing' :
                               status === 'failed' ? 'Failed' :
                               'Not Crawled'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-center">
                            {(!status || status === 'failed') && !isCrawling && (
                              <button
                                onClick={() => handleCrawlSingleRoad(road)}
                                className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 transition-colors"
                              >
                                {status === 'failed' ? 'Retry' : 'Crawl'}
                              </button>
                            )}
                            {status === 'completed' && (
                              <span className="text-sm text-green-600">✓</span>
                            )}
                            {(status === 'processing' || isCrawling) && (
                              <div className="flex items-center justify-center">
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                              </div>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="mt-4 flex items-center justify-between">
                  <div className="text-sm text-gray-700">
                    Showing {(currentPage - 1) * roadsPerPage + 1} to {Math.min(currentPage * roadsPerPage, filteredAndSortedRoads.length)} of {filteredAndSortedRoads.length} roads
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                      disabled={currentPage === 1}
                      className="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium disabled:bg-gray-100 disabled:text-gray-400 hover:bg-gray-50"
                    >
                      Previous
                    </button>
                    <span className="px-3 py-1 text-sm">
                      Page {currentPage} of {totalPages}
                    </span>
                    <button
                      onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                      disabled={currentPage === totalPages}
                      className="px-3 py-1 border border-gray-300 rounded-md text-sm font-medium disabled:bg-gray-100 disabled:text-gray-400 hover:bg-gray-50"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}

              {/* Summary Statistics */}
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Total Roads:</span>
                    <span className="ml-2 font-semibold">{filteredAndSortedRoads.length}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Completed:</span>
                    <span className="ml-2 font-semibold text-green-600">
                      {Object.values(crawlStatus).filter(s => s[businessKeyword] === 'completed').length}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">In Progress:</span>
                    <span className="ml-2 font-semibold text-blue-600">
                      {Object.values(crawlStatus).filter(s => s[businessKeyword] === 'processing').length + crawlingRoads.size}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Not Crawled:</span>
                    <span className="ml-2 font-semibold text-gray-600">
                      {filteredAndSortedRoads.length - Object.values(crawlStatus).filter(s => s[businessKeyword]).length}
                    </span>
                  </div>
                </div>
              </div>
            </>
          ) : (
            !isLoading && (
              <div className="text-center py-12 text-gray-500">
                <p className="text-lg mb-2">No roads found matching your criteria</p>
                <p className="text-sm">Try adjusting your filters or search in a different area</p>
              </div>
            )
          )}
        </div>
      )}

      {/* Tips Section */}
      <div className="bg-gray-50 p-6 rounded-lg">
        <h3 className="text-lg font-semibold mb-3">Pro Tips for Better Results</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
          <div>
            <h4 className="font-medium text-gray-700 mb-1">🎯 Best Road Types for Businesses:</h4>
            <ul className="list-disc list-inside space-y-1">
              <li>Primary/Secondary roads in downtown areas</li>
              <li>Residential streets named "Main" or "Broadway"</li>
              <li>Roads near shopping centers or plazas</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-gray-700 mb-1">📍 High-Density Business Areas:</h4>
            <ul className="list-disc list-inside space-y-1">
              <li>California: Los Angeles, San Francisco counties</li>
              <li>Texas: Harris (Houston), Dallas counties</li>
              <li>New York: New York, Kings counties</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CrawlControl;