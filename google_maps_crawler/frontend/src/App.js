import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import MapView from './components/MapView';
import CrawlControl from './components/CrawlControl';
import BusinessList from './components/BusinessList';
import { fetchStats } from './api/crawler';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [selectedRoad, setSelectedRoad] = useState(null);

  useEffect(() => {
    // Only load stats on initial mount if dashboard is active
    if (activeTab === 'dashboard') {
      loadStats();
    }
  }, []);

  const loadStats = async () => {
    try {
      const data = await fetchStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <h1 className="text-3xl font-bold text-gray-900">
              Google Maps Business Crawler
            </h1>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">
                Database: 5.15M roads | 3.4M with names
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {['dashboard', 'crawl', 'map', 'businesses'].map((tab) => (
              <button
                key={tab}
                onClick={() => {
                  setActiveTab(tab);
                  // Load stats when switching to dashboard tab
                  if (tab === 'dashboard' && !stats) {
                    loadStats();
                  }
                }}
                className={`py-4 px-3 text-sm font-medium capitalize ${
                  activeTab === tab
                    ? 'text-white border-b-2 border-blue-500'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && (
          <Dashboard stats={stats} onRefresh={loadStats} />
        )}
        {activeTab === 'crawl' && (
          <CrawlControl onCrawlStart={loadStats} />
        )}
        {activeTab === 'map' && (
          <MapView 
            onRoadSelect={setSelectedRoad}
            selectedRoad={selectedRoad}
          />
        )}
        {activeTab === 'businesses' && (
          <BusinessList selectedRoad={selectedRoad} />
        )}
      </main>
    </div>
  );
}

export default App;