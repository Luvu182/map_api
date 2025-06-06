import React, { useState, useEffect } from 'react';
import { startCrawl, fetchUnprocessedRoads, fetchCountiesByState, fetchStatesSummary, fetchCrawlStatus, crawlSingleRoad } from '../api/crawler';
import { getCountyName } from '../data/countyNames';

const CrawlControl = ({ onCrawlStart }) => {
  const [selectedState, setSelectedState] = useState('');
  const [selectedCounty, setSelectedCounty] = useState('');
  const [selectedRoadType, setSelectedRoadType] = useState('all');
  const [searchKeyword, setSearchKeyword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [allRoads, setAllRoads] = useState([]);
  const [counties, setCounties] = useState([]);
  const [message, setMessage] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [crawlStatus, setCrawlStatus] = useState({}); // Track crawl status by linearid
  const [showOnlyUncrawled, setShowOnlyUncrawled] = useState(false);
  const [crawlingRoads, setCrawlingRoads] = useState(new Set()); // Roads currently being crawled
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
    { code: 'DE', name: 'Delaware' },
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
    { code: 'VT', name: 'Vermont' },
    { code: 'VA', name: 'Virginia' },
    { code: 'WA', name: 'Washington' },
    { code: 'WV', name: 'West Virginia' },
    { code: 'WI', name: 'Wisconsin' },
    { code: 'WY', name: 'Wyoming' }
  ];

  const roadTypes = [
    { 
      value: 'all', 
      label: 'All Road Types',
      description: 'Tất cả các loại đường'
    },
    { 
      value: 'Primary Roads', 
      label: 'Primary Roads',
      description: 'Đường cao tốc liên bang (Interstate highways) - I-5, I-95, v.v.',
      mtfcc: 'S1100'
    },
    { 
      value: 'Secondary Roads', 
      label: 'Secondary Roads',
      description: 'Đường quốc lộ/tỉnh lộ (US/State highways) - US-101, State Route 1, v.v.',
      mtfcc: 'S1200'
    },
    { 
      value: 'Local Streets', 
      label: 'Local Streets',
      description: 'Đường phố trong thành phố, khu dân cư - Main St, Broadway, v.v.',
      mtfcc: 'S1400'
    },
    { 
      value: 'Special Roads', 
      label: 'Special Roads',
      description: 'Đường nhánh, đường dịch vụ, đường vào bãi đỗ xe, v.v.',
      mtfcc: 'S1500-S1780'
    }
  ];

  useEffect(() => {
    loadStatesSummary();
  }, []);

  useEffect(() => {
    if (selectedState) {
      loadCountiesForState(selectedState);
    }
  }, [selectedState]);

  const loadRoads = async () => {
    try {
      // TODO: Update API to fetch roads by state/county/type
      const data = await fetchUnprocessedRoads(1000); // Get more roads
      setAllRoads(data.roads || []);
      
      // Load crawl status from database
      if (searchKeyword) {
        const statusData = await fetchCrawlStatus(selectedState, selectedCounty, searchKeyword);
        // Convert to simple format for display
        const simpleStatus = {};
        Object.keys(statusData).forEach(roadId => {
          if (statusData[roadId][searchKeyword]) {
            simpleStatus[roadId] = statusData[roadId][searchKeyword];
          }
        });
        setCrawlStatus(simpleStatus);
      }
    } catch (error) {
      console.error('Failed to load roads:', error);
    }
  };

  const loadCountiesForState = async (stateCode) => {
    try {
      const data = await fetchCountiesByState(stateCode);
      console.log('Counties data:', data); // Debug log
      setCounties(data.counties || data || []); // Check both formats
    } catch (error) {
      console.error('Failed to load counties:', error);
      setCounties([]);
    }
  };

  const loadStatesSummary = async () => {
    try {
      const data = await fetchStatesSummary();
      // Could use this to show actual road counts
    } catch (error) {
      console.error('Failed to load states summary:', error);
    }
  };

  const handleSearch = async () => {
    // Load roads based on filters
    await loadRoads();
    setCurrentPage(1);
  };

  const handleCrawlSingleRoad = async (road) => {
    const roadId = road.linearid;
    
    // Add to crawling set
    setCrawlingRoads(prev => new Set([...prev, roadId]));
    
    try {
      // Call API to crawl this specific road with keyword
      const result = await crawlSingleRoad(roadId, searchKeyword);
      
      // Update status locally (will be refreshed from DB)
      const newStatus = { ...crawlStatus };
      newStatus[roadId] = 'processing';
      setCrawlStatus(newStatus);
      
      setMessage(`Started crawling ${road.fullname} for "${searchKeyword}"`);
      
      // Poll for status updates after a delay
      setTimeout(async () => {
        await loadRoads(); // Refresh status from database
      }, 3000);
      
    } catch (error) {
      // Update status to failed
      const newStatus = { ...crawlStatus };
      newStatus[roadId] = 'failed';
      setCrawlStatus(newStatus);
      
      setMessage(`Error crawling ${road.fullname}: ${error.message}`);
    } finally {
      // Remove from crawling set
      setCrawlingRoads(prev => {
        const newSet = new Set(prev);
        newSet.delete(roadId);
        return newSet;
      });
    }
  };

  // Filter roads based on criteria
  const filteredRoads = allRoads.filter(road => {
    // Filter by state
    if (selectedState && road.state_code !== selectedState) return false;
    
    // Filter by county
    if (selectedCounty && road.county_fips !== selectedCounty) return false;
    
    // Filter by road type
    if (selectedRoadType !== 'all' && road.road_category !== selectedRoadType) return false;
    
    // Filter by crawl status
    if (showOnlyUncrawled && crawlStatus[road.linearid]) return false;
    
    return true;
  });

  // Pagination
  const totalPages = Math.ceil(filteredRoads.length / roadsPerPage);
  const paginatedRoads = filteredRoads.slice(
    (currentPage - 1) * roadsPerPage,
    currentPage * roadsPerPage
  );


  return (
    <div className="space-y-6">
      {/* Search and Filter Section */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">Google Maps Business Crawler</h2>
        <p className="text-sm text-gray-600 mb-4">
          Search businesses along US roads using Google Maps Places API
        </p>
        
        {/* Keyword Input First */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            1. Business Keyword <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            placeholder="e.g. clothing store, restaurant, grocery..."
            className="w-full px-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg"
          />
          <p className="mt-1 text-xs text-gray-500">
            This keyword will be combined with road names for Google Maps search
          </p>
        </div>
        
        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* State Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              2. State
            </label>
            <select
              value={selectedState}
              onChange={(e) => {
                setSelectedState(e.target.value);
                setSelectedCounty('');
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All States</option>
              {states.map(state => (
                <option key={state.code} value={state.code}>
                  {state.name}
                </option>
              ))}
            </select>
          </div>
          
          {/* County Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              3. County
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
          
          {/* Road Type Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              4. Road Type
              <span className="ml-1 text-gray-400 cursor-help" title="Chọn loại đường để lọc">ⓘ</span>
            </label>
            <select
              value={selectedRoadType}
              onChange={(e) => setSelectedRoadType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {roadTypes.map(type => (
                <option key={type.value} value={type.value} title={type.description}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>
          
          {/* Search Button */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">&nbsp;</label>
            <button
              onClick={handleSearch}
              disabled={!searchKeyword}
              className="w-full px-6 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:bg-gray-400"
            >
              View Roads
            </button>
          </div>
        </div>
        
        {message && (
          <div className={`mt-4 p-3 rounded ${message.includes('Error') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
            {message}
          </div>
        )}
      </div>


      {/* Road Statistics by State */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Road Distribution by State</h3>
        <p className="text-sm text-gray-600 mb-4">
          Top states in database (323 counties with cities >100k population)
        </p>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StateCard state="California" counties={29} roads={839769} />
          <StateCard state="Texas" counties={28} roads={522254} />
          <StateCard state="Florida" counties={22} roads={417898} />
          <StateCard state="New York" counties={14} roads={155581} />
          <StateCard state="Pennsylvania" counties={9} roads={136702} />
          <StateCard state="Illinois" counties={8} roads={154774} />
          <StateCard state="Ohio" counties={10} roads={119056} />
          <StateCard state="Georgia" counties={12} roads={120226} />
        </div>
      </div>

      {/* Roads List with Pagination */}
      {searchKeyword && (
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">
              {filteredRoads.length} Roads Found
              {selectedState && ` in ${states.find(s => s.code === selectedState)?.name}`}
              {selectedCounty && `, ${getCountyName(selectedCounty)}`}
            </h3>
            <div className="flex items-center space-x-4">
              <label className="flex items-center text-sm">
                <input
                  type="checkbox"
                  checked={showOnlyUncrawled}
                  onChange={(e) => setShowOnlyUncrawled(e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded mr-2"
                />
                Show only uncrawled roads
              </label>
              <span className="text-sm text-gray-500">
                Keyword: <strong>{searchKeyword}</strong>
              </span>
            </div>
          </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Road Name</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">MTFCC</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">State</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">County</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Action</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {paginatedRoads.map((road) => {
                const status = crawlStatus[road.linearid];
                const isCrawling = crawlingRoads.has(road.linearid);
                
                return (
                  <tr key={road.linearid} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium">{road.fullname || 'Unnamed'}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-1 text-xs rounded ${
                        road.road_category === 'Primary Roads' ? 'bg-red-100 text-red-800' :
                        road.road_category === 'Secondary Roads' ? 'bg-yellow-100 text-yellow-800' :
                        road.road_category === 'Local Streets' ? 'bg-green-100 text-green-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {road.road_category}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">{road.mtfcc}</td>
                    <td className="px-4 py-3 text-sm">{road.state_code}</td>
                    <td className="px-4 py-3 text-sm">{getCountyName(road.county_fips)}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 text-xs rounded ${
                        isCrawling ? 'bg-yellow-100 text-yellow-800' :
                        status === 'completed' ? 'bg-green-100 text-green-800' :
                        status === 'failed' ? 'bg-red-100 text-red-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {isCrawling ? 'Processing...' : status || 'Not Crawled'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      {!status && !isCrawling && (
                        <button
                          onClick={() => handleCrawlSingleRoad(road)}
                          className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600"
                        >
                          Crawl
                        </button>
                      )}
                      {status === 'completed' && (
                        <span className="text-sm text-green-600">✓ Done</span>
                      )}
                      {status === 'failed' && (
                        <button
                          onClick={() => handleCrawlSingleRoad(road)}
                          className="px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600"
                        >
                          Retry
                        </button>
                      )}
                      {isCrawling && (
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
              Showing {(currentPage - 1) * roadsPerPage + 1} to {Math.min(currentPage * roadsPerPage, filteredRoads.length)} of {filteredRoads.length} roads
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
        
        {/* Statistics */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Total Roads:</span>
              <span className="ml-2 font-semibold">{filteredRoads.length}</span>
            </div>
            <div>
              <span className="text-gray-500">Crawled:</span>
              <span className="ml-2 font-semibold text-green-600">
                {Object.values(crawlStatus).filter(s => s === 'completed').length}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Not Crawled:</span>
              <span className="ml-2 font-semibold text-blue-600">
                {filteredRoads.length - Object.values(crawlStatus).filter(s => s).length}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Failed:</span>
              <span className="ml-2 font-semibold text-red-600">
                {Object.values(crawlStatus).filter(s => s === 'failed').length}
              </span>
            </div>
          </div>
        </div>
      </div>
      )}
    </div>
  );
};

const StateCard = ({ state, counties, roads }) => {
  return (
    <div className="p-4 bg-gray-50 rounded-lg">
      <h4 className="font-semibold text-sm">{state}</h4>
      <p className="text-xs text-gray-600 mt-1">{counties} counties</p>
      <p className="text-lg font-bold text-blue-600">{roads.toLocaleString()}</p>
      <p className="text-xs text-gray-500">roads</p>
    </div>
  );
};

export default CrawlControl;