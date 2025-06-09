import React, { useState, useEffect } from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement } from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';
import { useLanguage } from '../contexts/LanguageContext';
import { t } from '../translations/translations';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement);

const Dashboard = ({ stats, onRefresh }) => {
  const { language } = useLanguage();
  const [apiUsage, setApiUsage] = useState(null);
  
  useEffect(() => {
    fetchApiUsage();
  }, []);
  
  const fetchApiUsage = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/usage');
      const data = await response.json();
      setApiUsage(data);
    } catch (error) {
      console.error('Failed to fetch API usage:', error);
    }
  };
  
  if (!stats) {
    return <div className="text-center py-8">{t('loading', language)}</div>;
  }

  const gmapsConnected = true; // You have API key configured

  const coverageData = {
    labels: ['Processed', 'Unprocessed'],
    datasets: [{
      data: [stats.roads_processed, stats.roads_with_names - stats.roads_processed],
      backgroundColor: ['#10B981', '#EF4444'],
      borderWidth: 0
    }]
  };

  // Road category distribution - OSM data (actual from database)
  const roadCategoryData = {
    labels: ['Service', 'Footway', 'Residential', 'Secondary', 'Tertiary'],
    datasets: [{
      label: 'Segments',
      data: [12171695, 6033307, 4574991, 765251, 651438],
      backgroundColor: ['#F59E0B', '#94A3B8', '#10B981', '#3B82F6', '#8B5CF6']
    }]
  };

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard
          title="Target Cities"
          value="340"
          subtitle="Cities mapped (98.3% of 346 target cities)"
          color="blue"
        />
        <StatCard
          title="Unique Roads with Names"
          value={stats.roads_with_names?.toLocaleString() || '0'}
          subtitle="Available for crawling (in target cities)"
          color="green"
        />
        <StatCard
          title="Roads Crawled" 
          value={stats.roads_processed?.toLocaleString() || '0'}
          subtitle="Businesses searched on these roads"
          color="yellow"
        />
        <StatCard
          title="Businesses Found"
          value={stats.businesses_found?.toLocaleString() || '0'}
          subtitle={`Avg ${stats.avg_businesses_per_road?.toFixed(1)} per road`}
          color="purple"
        />
      </div>

      {/* System Status & API Usage Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">Database Status</h3>
            <button
              onClick={onRefresh}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Refresh
            </button>
          </div>
          
          <div className="space-y-3">
            <StatusItem label="Database" value="Self-hosted PostgreSQL" status="online" />
            <StatusItem label="Total Size" value="18 GB (15GB roads + 2.4GB mappings)" />
            <StatusItem label="Main Tables" value="osm_roads_main (10.48M), road_city_mapping (10.57M)" />
            <StatusItem label="Coverage" value="340 cities mapped (98.3%)" />
            <StatusItem label="Query Performance" value="<50ms city-based" status="online" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">API Usage</h3>
          
          {apiUsage && !apiUsage.error ? (
            <div className="space-y-4">
              {/* Main stats in grid */}
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="bg-gray-50 p-3 rounded">
                  <div className="text-2xl font-bold text-blue-600">{apiUsage.total_requests || 0}</div>
                  <div className="text-xs text-gray-600">API Requests</div>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <div className="text-2xl font-bold text-green-600">{apiUsage.total_crawls || 0}</div>
                  <div className="text-xs text-gray-600">Crawl Sessions</div>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <div className="text-2xl font-bold text-purple-600">{apiUsage.total_results || 0}</div>
                  <div className="text-xs text-gray-600">Businesses</div>
                </div>
              </div>
              
              {/* Today and Cost in compact format */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-blue-50 p-3 rounded">
                  <div className="text-xs font-medium text-blue-700 mb-1">Today</div>
                  <div className="text-sm">
                    <span className="font-bold">{apiUsage.today?.crawls || 0}</span> crawls · 
                    <span className="font-bold"> {apiUsage.today?.estimated_api_calls || 0}</span> calls
                  </div>
                </div>
                <div className="bg-yellow-50 p-3 rounded">
                  <div className="text-xs font-medium text-yellow-700 mb-1">Cost</div>
                  <div className="text-sm font-bold text-yellow-800">
                    {apiUsage.notes?.estimated_cost || '$0.00'}
                  </div>
                </div>
              </div>
              
              {/* Top keywords - compact */}
              {apiUsage.by_keyword && apiUsage.by_keyword.length > 0 && (
                <div className="text-xs">
                  <span className="font-medium text-gray-700">Top Keywords: </span>
                  {apiUsage.by_keyword.slice(0, 3).map((item, idx) => (
                    <span key={item.keyword} className="text-gray-600">
                      {idx > 0 && ' · '}
                      {item.keyword} ({item.crawl_count})
                    </span>
                  ))}
                </div>
              )}
              
              {/* Pricing info - very compact */}
              <div className="text-xs text-gray-500 border-t pt-2">
                <div>Text Search: $32/1k requests · Each crawl = 3 requests</div>
              </div>
            </div>
          ) : (
            <div className="text-sm text-gray-500 text-center py-4">
              {apiUsage?.error ? "Loading..." : "Loading API usage..."}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ title, value, subtitle, color }) => {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    purple: 'bg-purple-50 text-purple-600'
  };

  return (
    <div className={`p-6 rounded-lg ${colorClasses[color]}`}>
      <h3 className="text-sm font-medium">{title}</h3>
      <p className="text-2xl font-bold mt-2">{value}</p>
      <p className="text-sm mt-1 opacity-75">{subtitle}</p>
    </div>
  );
};

const ProgressBar = ({ label, current, total }) => {
  const percentage = (current / total) * 100;
  
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-sm font-medium">{label}</span>
        <span className="text-sm text-gray-600">{percentage.toFixed(1)}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

const estimateTimeRemaining = (processed, total) => {
  const remaining = total - processed;
  const hoursRemaining = remaining / 50; // 50 roads per hour estimate
  
  if (hoursRemaining < 1) return `${Math.round(hoursRemaining * 60)} minutes`;
  if (hoursRemaining < 24) return `${Math.round(hoursRemaining)} hours`;
  return `${Math.round(hoursRemaining / 24)} days`;
};

const StatusItem = ({ label, value, status }) => {
  const statusColors = {
    online: 'bg-green-100 text-green-800',
    offline: 'bg-red-100 text-red-800',
    warning: 'bg-yellow-100 text-yellow-800'
  };

  return (
    <div className="flex justify-between items-center py-2">
      <span className="text-sm text-gray-600">{label}:</span>
      <span className={`text-sm font-medium ${status ? `px-2 py-1 rounded ${statusColors[status]}` : ''}`}>
        {value}
      </span>
    </div>
  );
};

export default Dashboard;