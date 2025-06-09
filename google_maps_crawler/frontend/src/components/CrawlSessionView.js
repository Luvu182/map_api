import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowBack,
  Download,
  Phone,
  Language as WebIcon,
  Star,
  AttachMoney,
  LocationOn,
  AccessTime,
  CheckCircle,
  Error,
  HourglassEmpty
} from '@mui/icons-material';
import { useLanguage } from '../contexts/LanguageContext';

const CrawlSessionView = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { language } = useLanguage();
  const [session, setSession] = useState(null);
  const [businesses, setBusinesses] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (sessionId) {
      fetchSessionData();
    }
  }, [sessionId]);

  const fetchSessionData = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/crawl-sessions/${sessionId}`);
      const data = await response.json();
      
      setSession(data.session);
      setBusinesses(data.businesses || []);
      setStats(data.stats);
    } catch (error) {
      console.error('Error fetching session:', error);
    }
    setLoading(false);
  };

  const handleExport = async (format) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/crawl-sessions/${sessionId}/export?format=${format}`,
        { method: 'POST' }
      );
      const blob = await response.blob();
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `crawl_session_${sessionId}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (error) {
      console.error('Error exporting:', error);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="text-green-600" />;
      case 'failed':
        return <Error className="text-red-600" />;
      case 'crawling':
        return <HourglassEmpty className="text-yellow-600 animate-spin" />;
      default:
        return null;
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen bg-gray-100 p-8">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Session not found</h2>
          <button 
            onClick={() => navigate(-1)}
            className="text-blue-600 hover:underline"
          >
            Go back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <button
                onClick={() => navigate(-1)}
                className="mr-4 p-2 hover:bg-gray-100 rounded"
              >
                <ArrowBack />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  {session.road_name || 'Unknown Road'}
                </h1>
                <p className="text-gray-600">
                  {session.city_name}, {session.state_code}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {getStatusIcon(session.status)}
              <span className="text-lg font-medium">
                {session.status.charAt(0).toUpperCase() + session.status.slice(1)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Session Info */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="grid grid-cols-5 gap-4">
            <div>
              <div className="text-sm text-gray-600">
                {language === 'vi' ? 'Thời gian bắt đầu' : 'Started At'}
              </div>
              <div className="font-medium">
                {new Date(session.started_at).toLocaleString()}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600">
                {language === 'vi' ? 'Thời lượng' : 'Duration'}
              </div>
              <div className="font-medium flex items-center">
                <AccessTime className="mr-1 h-4 w-4" />
                {formatDuration(session.duration_seconds)}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600">
                {language === 'vi' ? 'Từ khóa' : 'Keyword'}
              </div>
              <div className="font-medium">{session.keyword || 'all'}</div>
            </div>
            <div>
              <div className="text-sm text-gray-600">
                {language === 'vi' ? 'Tìm thấy' : 'Found'}
              </div>
              <div className="font-medium text-2xl text-blue-600">
                {session.businesses_found || 0}
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleExport('csv')}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 flex items-center"
              >
                <Download className="mr-2 h-4 w-4" />
                CSV
              </button>
              <button
                onClick={() => handleExport('json')}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 flex items-center"
              >
                <Download className="mr-2 h-4 w-4" />
                JSON
              </button>
            </div>
          </div>

          {/* Stats */}
          {stats && (
            <div className="grid grid-cols-4 gap-4 mt-6 pt-6 border-t">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {((stats.with_phone / stats.total) * 100).toFixed(0)}%
                </div>
                <div className="text-sm text-gray-600">
                  {language === 'vi' ? 'Có SĐT' : 'Have Phone'}
                </div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {((stats.with_website / stats.total) * 100).toFixed(0)}%
                </div>
                <div className="text-sm text-gray-600">
                  {language === 'vi' ? 'Có Website' : 'Have Website'}
                </div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">
                  {stats.avg_rating?.toFixed(1) || 'N/A'}
                </div>
                <div className="text-sm text-gray-600">
                  {language === 'vi' ? 'Rating TB' : 'Avg Rating'}
                </div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {stats.unique_types || 0}
                </div>
                <div className="text-sm text-gray-600">
                  {language === 'vi' ? 'Loại hình' : 'Business Types'}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Business List - Table View */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b flex justify-between items-center">
            <h2 className="text-lg font-semibold">
              {language === 'vi' ? 'Danh sách Business' : 'Business List'} 
              ({businesses.length})
            </h2>
            <div className="flex gap-2">
              <button
                onClick={() => handleExport('csv')}
                className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 flex items-center"
              >
                <Download className="mr-1 h-4 w-4" />
                Export CSV
              </button>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-10">
                    #
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {language === 'vi' ? 'Tên' : 'Name'}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {language === 'vi' ? 'Địa chỉ' : 'Address'}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {language === 'vi' ? 'Điện thoại' : 'Phone'}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Website
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rating
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {language === 'vi' ? 'Loại hình' : 'Type'}
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {businesses.map((business, index) => (
                  <tr key={business.place_id} className="hover:bg-gray-50">
                    <td className="px-3 py-2 text-xs text-gray-500">
                      {index + 1}
                    </td>
                    <td className="px-3 py-2">
                      <div className="text-xs font-medium text-gray-900">
                        {business.name}
                      </div>
                    </td>
                    <td className="px-3 py-2">
                      <div className="text-xs text-gray-500 max-w-sm">
                        {business.formatted_address}
                      </div>
                    </td>
                    <td className="px-3 py-2">
                      {business.phone_number ? (
                        <a 
                          href={`tel:${business.phone_number}`} 
                          className="text-xs text-blue-600 hover:underline"
                        >
                          {business.phone_number}
                        </a>
                      ) : (
                        <span className="text-xs text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-3 py-2">
                      {business.website ? (
                        <a 
                          href={business.website} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-xs text-blue-600 hover:underline flex items-center"
                        >
                          <WebIcon className="h-3 w-3 mr-1" />
                          View
                        </a>
                      ) : (
                        <span className="text-xs text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-center">
                      {business.rating ? (
                        <div className="flex items-center justify-center">
                          <Star className="h-3 w-3 text-yellow-400 mr-1" />
                          <span className="text-xs font-medium">{business.rating}</span>
                          <span className="text-xs text-gray-500 ml-1">({business.user_ratings_total})</span>
                        </div>
                      ) : (
                        <span className="text-xs text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-3 py-2">
                      {business.types && business.types.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {business.types.slice(0, 2).map(type => (
                            <span key={type} className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                              {type.replace(/_/g, ' ')}
                            </span>
                          ))}
                          {business.types.length > 2 && (
                            <span className="text-xs text-gray-500">+{business.types.length - 2}</span>
                          )}
                        </div>
                      ) : (
                        <span className="text-xs text-gray-400">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CrawlSessionView;