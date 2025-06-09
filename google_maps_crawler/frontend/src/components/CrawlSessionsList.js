import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { t } from '../translations/translations';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const CrawlSessionsList = () => {
  const { language } = useLanguage();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('all'); // all, completed, failed, crawling
  const [sortBy, setSortBy] = useState('created_at'); // created_at, businesses_found
  const [sortOrder, setSortOrder] = useState('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const sessionsPerPage = 20;

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/crawl-sessions/`);
      setSessions(response.data.sessions || []);
    } catch (error) {
      console.error('Failed to load sessions:', error);
      setSessions([]);
    } finally {
      setLoading(false);
    }
  };

  // Filter sessions
  const filteredSessions = sessions.filter(session => {
    if (filter === 'all') return true;
    return session.status === filter;
  });

  // Sort sessions
  const sortedSessions = [...filteredSessions].sort((a, b) => {
    let compareValue = 0;
    if (sortBy === 'created_at') {
      compareValue = new Date(a.created_at) - new Date(b.created_at);
    } else if (sortBy === 'businesses_found') {
      compareValue = (a.businesses_found || 0) - (b.businesses_found || 0);
    }
    return sortOrder === 'asc' ? compareValue : -compareValue;
  });

  // Pagination
  const totalPages = Math.ceil(sortedSessions.length / sessionsPerPage);
  const paginatedSessions = sortedSessions.slice(
    (currentPage - 1) * sessionsPerPage,
    currentPage * sessionsPerPage
  );

  const handleViewSession = (sessionId) => {
    navigate(`/session/${sessionId}`);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'crawling':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-2xl font-bold mb-2">
          {language === 'vi' ? 'Quản lý Crawl Sessions' : 'Crawl Sessions Management'}
        </h2>
        <p className="text-gray-600">
          {language === 'vi' 
            ? 'Xem và quản lý các phiên crawl đã thực hiện' 
            : 'View and manage crawl sessions'}
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Trạng thái' : 'Status'}
            </label>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="all">{language === 'vi' ? 'Tất cả' : 'All'}</option>
              <option value="completed">{language === 'vi' ? 'Hoàn thành' : 'Completed'}</option>
              <option value="failed">{language === 'vi' ? 'Thất bại' : 'Failed'}</option>
              <option value="crawling">{language === 'vi' ? 'Đang crawl' : 'Crawling'}</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Sắp xếp theo' : 'Sort by'}
            </label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="created_at">{language === 'vi' ? 'Thời gian' : 'Time'}</option>
              <option value="businesses_found">{language === 'vi' ? 'Số businesses' : 'Businesses found'}</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {language === 'vi' ? 'Thứ tự' : 'Order'}
            </label>
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="desc">{language === 'vi' ? 'Mới nhất' : 'Newest first'}</option>
              <option value="asc">{language === 'vi' ? 'Cũ nhất' : 'Oldest first'}</option>
            </select>
          </div>
        </div>
      </div>

      {/* Sessions List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-500">{t('loading', language)}</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {language === 'vi' ? 'Thời gian' : 'Time'}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {language === 'vi' ? 'Đường' : 'Road'}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {language === 'vi' ? 'Thành phố' : 'City'}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {language === 'vi' ? 'Từ khóa' : 'Keyword'}
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  {language === 'vi' ? 'Kết quả' : 'Results'}
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  {language === 'vi' ? 'Trạng thái' : 'Status'}
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  {language === 'vi' ? 'Hành động' : 'Actions'}
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {paginatedSessions.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-4 text-center text-gray-500">
                    {language === 'vi' ? 'Không có session nào' : 'No sessions found'}
                  </td>
                </tr>
              ) : (
                paginatedSessions.map((session) => (
                  <tr key={session.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDate(session.started_at || session.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {session.road_name || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {session.city_name ? `${session.city_name}, ${session.state_code}` : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {session.keyword || 'all'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <span className="text-sm font-medium text-gray-900">
                        {session.businesses_found || 0}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getStatusColor(session.status)}`}>
                        {session.status === 'completed' ? (language === 'vi' ? 'Hoàn thành' : 'Completed') :
                         session.status === 'failed' ? (language === 'vi' ? 'Thất bại' : 'Failed') :
                         session.status === 'crawling' ? (language === 'vi' ? 'Đang crawl' : 'Crawling') :
                         session.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <button
                        onClick={() => handleViewSession(session.id)}
                        className="text-blue-600 hover:text-blue-900 text-sm font-medium"
                      >
                        {language === 'vi' ? 'Xem chi tiết' : 'View Details'}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="bg-gray-50 px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
              <div className="flex-1 flex justify-between sm:hidden">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  {t('previous', language)}
                </button>
                <button
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  {t('next', language)}
                </button>
              </div>
              <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm text-gray-700">
                    {language === 'vi' ? 'Hiển thị' : 'Showing'} {' '}
                    <span className="font-medium">{(currentPage - 1) * sessionsPerPage + 1}</span>
                    {' '} {language === 'vi' ? 'đến' : 'to'} {' '}
                    <span className="font-medium">
                      {Math.min(currentPage * sessionsPerPage, filteredSessions.length)}
                    </span>
                    {' '} {language === 'vi' ? 'trong' : 'of'} {' '}
                    <span className="font-medium">{filteredSessions.length}</span>
                    {' '} {language === 'vi' ? 'kết quả' : 'results'}
                  </p>
                </div>
                <div>
                  <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                    <button
                      onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                      disabled={currentPage === 1}
                      className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                    >
                      {t('previous', language)}
                    </button>
                    <button
                      onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                      disabled={currentPage === totalPages}
                      className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                    >
                      {t('next', language)}
                    </button>
                  </nav>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CrawlSessionsList;