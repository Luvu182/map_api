import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import MapView from './components/MapView';
import CrawlControl from './components/CrawlControl';
import BusinessList from './components/BusinessList';
import CrawlDataManager from './components/CrawlDataManager';
import CrawlSessionView from './components/CrawlSessionView';
import CrawlSessionsList from './components/CrawlSessionsList';
import LanguageSelector from './components/LanguageSelector';
import Login from './components/Login';
import { fetchStats } from './api/crawler';
import { LanguageProvider, useLanguage } from './contexts/LanguageContext';
import { t } from './translations/translations';
import { Button } from '@mui/material';
import { Logout } from '@mui/icons-material';
import axios from 'axios';

// Protected Route component
function ProtectedRoute({ children }) {
  const isAuthenticated = localStorage.getItem('token');
  const location = useLocation();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  
  return children;
}

function AppContent() {
  const { language } = useLanguage();
  const navigate = useNavigate();
  const location = useLocation();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [selectedRoad, setSelectedRoad] = useState(null);
  const [user, setUser] = useState(null);
  
  // Check authentication status
  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      setUser(JSON.parse(userData));
      // Set default axios header
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }, []);
  
  // Determine active tab from route
  useEffect(() => {
    const path = location.pathname;
    if (path.startsWith('/session/')) {
      setActiveTab('session');
    } else if (path === '/crawl') {
      setActiveTab('crawl');
    } else if (path === '/data') {
      setActiveTab('data');
    } else if (path === '/map') {
      setActiveTab('map');
    } else if (path === '/sessions') {
      setActiveTab('sessions');
    } else {
      setActiveTab('dashboard');
    }
  }, [location]);

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

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
    navigate('/login');
  };

  // Redirect to login if not authenticated
  if (location.pathname !== '/login' && !localStorage.getItem('token')) {
    return <Navigate to="/login" replace />;
  }

  // Don't show header/nav on login page
  if (location.pathname === '/login') {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
      </Routes>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <h1 className="text-3xl font-bold text-gray-900">
              {t('title', language)}
            </h1>
            <div className="flex items-center space-x-4">
              {user && (
                <span className="text-sm text-gray-600">
                  {user.username}
                </span>
              )}
              <span className="text-sm text-gray-500">
                Database: 27.2M roads
              </span>
              <LanguageSelector />
              <Button
                startIcon={<Logout />}
                onClick={handleLogout}
                size="small"
                variant="outlined"
              >
                {t('login.logout', language)}
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {['dashboard', 'crawl', 'sessions', 'data', 'map'].map((tab) => (
              <button
                key={tab}
                onClick={() => {
                  setActiveTab(tab);
                  // Navigate to appropriate route
                  if (tab === 'dashboard') {
                    navigate('/');
                    if (!stats) loadStats();
                  } else {
                    navigate(`/${tab}`);
                  }
                }}
                className={`py-4 px-3 text-sm font-medium ${
                  activeTab === tab
                    ? 'text-white border-b-2 border-blue-500'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                {tab === 'dashboard' ? t('statistics', language) :
                 tab === 'crawl' ? t('crawlControl', language) :
                 tab === 'sessions' ? (language === 'vi' ? 'Lịch sử Crawl' : 'Crawl History') :
                 tab === 'data' ? (language === 'vi' ? 'Quản lý Data' : 'Data Management') :
                 tab === 'map' ? 'Map' : tab}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          <Route path="/" element={
            <ProtectedRoute>
              <Dashboard stats={stats} onRefresh={loadStats} />
            </ProtectedRoute>
          } />
          <Route path="/crawl" element={
            <ProtectedRoute>
              <CrawlControl onCrawlStart={loadStats} />
            </ProtectedRoute>
          } />
          <Route path="/sessions" element={
            <ProtectedRoute>
              <CrawlSessionsList />
            </ProtectedRoute>
          } />
          <Route path="/data" element={
            <ProtectedRoute>
              <CrawlDataManager />
            </ProtectedRoute>
          } />
          <Route path="/map" element={
            <ProtectedRoute>
              <MapView onRoadSelect={setSelectedRoad} selectedRoad={selectedRoad} />
            </ProtectedRoute>
          } />
          <Route path="/session/:sessionId" element={
            <ProtectedRoute>
              <CrawlSessionView />
            </ProtectedRoute>
          } />
          <Route path="/login" element={<Login />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <LanguageProvider>
      <AppContent />
    </LanguageProvider>
  );
}

export default App;