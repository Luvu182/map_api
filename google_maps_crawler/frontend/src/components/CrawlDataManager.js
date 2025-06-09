import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { t } from '../translations/translations';
import { 
  LocationOn, 
  Phone, 
  Star, 
  Language, 
  Search,
  FilterList,
  Download,
  Delete,
  Refresh
} from '@mui/icons-material';

const CrawlDataManager = () => {
  const { language } = useLanguage();
  const [businesses, setBusinesses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    city: '',
    road: '',
    type: '',
    rating: 0,
    hasPhone: false
  });
  const [stats, setStats] = useState({
    total: 0,
    withPhone: 0,
    withWebsite: 0,
    avgRating: 0
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const itemsPerPage = 50;

  useEffect(() => {
    fetchBusinesses();
  }, [currentPage, filters]);

  const fetchBusinesses = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: currentPage,
        limit: itemsPerPage,
        ...filters
      });
      
      const response = await fetch(`http://localhost:8000/api/businesses?${params}`);
      const data = await response.json();
      
      setBusinesses(data.businesses || []);
      setStats(data.stats || {});
      setTotalPages(Math.ceil(data.total / itemsPerPage));
    } catch (error) {
      console.error('Error fetching businesses:', error);
    }
    setLoading(false);
  };

  const handleExport = async (format = 'csv') => {
    try {
      const params = new URLSearchParams({
        format,
        ...filters
      });
      
      const response = await fetch(`http://localhost:8000/api/businesses/export?${params}`);
      const blob = await response.blob();
      
      // Download file
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `businesses_${new Date().toISOString().split('T')[0]}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (error) {
      console.error('Error exporting data:', error);
    }
  };

  const handleDelete = async (placeId) => {
    if (!window.confirm('Are you sure you want to delete this business?')) {
      return;
    }
    
    try {
      await fetch(`http://localhost:8000/api/businesses/${placeId}`, {
        method: 'DELETE'
      });
      fetchBusinesses();
    } catch (error) {
      console.error('Error deleting business:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold text-gray-900">
            {language === 'vi' ? 'Quản lý dữ liệu Crawl' : 'Crawl Data Management'}
          </h2>
          <div className="flex space-x-2">
            <button
              onClick={() => fetchBusinesses()}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center"
            >
              <Refresh className="mr-2" />
              {language === 'vi' ? 'Làm mới' : 'Refresh'}
            </button>
            <button
              onClick={() => handleExport('csv')}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 flex items-center"
            >
              <Download className="mr-2" />
              Export CSV
            </button>
            <button
              onClick={() => handleExport('json')}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 flex items-center"
            >
              <Download className="mr-2" />
              Export JSON
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-gray-50 p-4 rounded">
            <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
            <div className="text-sm text-gray-600">
              {language === 'vi' ? 'Tổng businesses' : 'Total Businesses'}
            </div>
          </div>
          <div className="bg-gray-50 p-4 rounded">
            <div className="text-2xl font-bold text-blue-600">{stats.withPhone}</div>
            <div className="text-sm text-gray-600">
              {language === 'vi' ? 'Có số điện thoại' : 'With Phone'}
            </div>
          </div>
          <div className="bg-gray-50 p-4 rounded">
            <div className="text-2xl font-bold text-green-600">{stats.withWebsite}</div>
            <div className="text-sm text-gray-600">
              {language === 'vi' ? 'Có website' : 'With Website'}
            </div>
          </div>
          <div className="bg-gray-50 p-4 rounded">
            <div className="text-2xl font-bold text-yellow-600">{stats.avgRating?.toFixed(1)}</div>
            <div className="text-sm text-gray-600">
              {language === 'vi' ? 'Rating TB' : 'Avg Rating'}
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <FilterList className="mr-2" />
          {language === 'vi' ? 'Bộ lọc' : 'Filters'}
        </h3>
        <div className="grid grid-cols-5 gap-4">
          <input
            type="text"
            placeholder={language === 'vi' ? 'Thành phố...' : 'City...'}
            value={filters.city}
            onChange={(e) => setFilters({...filters, city: e.target.value})}
            className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="text"
            placeholder={language === 'vi' ? 'Tên đường...' : 'Road name...'}
            value={filters.road}
            onChange={(e) => setFilters({...filters, road: e.target.value})}
            className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={filters.type}
            onChange={(e) => setFilters({...filters, type: e.target.value})}
            className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">{language === 'vi' ? 'Tất cả loại' : 'All Types'}</option>
            <option value="restaurant">Restaurant</option>
            <option value="store">Store</option>
            <option value="bank">Bank</option>
            <option value="gas_station">Gas Station</option>
            <option value="hotel">Hotel</option>
          </select>
          <select
            value={filters.rating}
            onChange={(e) => setFilters({...filters, rating: parseFloat(e.target.value)})}
            className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="0">{language === 'vi' ? 'Mọi rating' : 'Any Rating'}</option>
            <option value="4">4+ ⭐</option>
            <option value="4.5">4.5+ ⭐</option>
          </select>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={filters.hasPhone}
              onChange={(e) => setFilters({...filters, hasPhone: e.target.checked})}
              className="mr-2"
            />
            {language === 'vi' ? 'Có SĐT' : 'Has Phone'}
          </label>
        </div>
      </div>

      {/* Business List */}
      <div className="bg-white rounded-lg shadow">
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">
              {language === 'vi' ? 'Đang tải...' : 'Loading...'}
            </p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {language === 'vi' ? 'Tên' : 'Name'}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {language === 'vi' ? 'Địa chỉ' : 'Address'}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {language === 'vi' ? 'Loại' : 'Type'}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {language === 'vi' ? 'SĐT' : 'Phone'}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Rating
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {language === 'vi' ? 'Đường' : 'Road'}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {language === 'vi' ? 'Ngày crawl' : 'Crawled'}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {language === 'vi' ? 'Thao tác' : 'Actions'}
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {businesses.map((business) => (
                    <tr key={business.place_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{business.name}</div>
                        {business.website && (
                          <a href={business.website} target="_blank" rel="noopener noreferrer" 
                             className="text-xs text-blue-600 hover:underline">
                            {language === 'vi' ? 'Xem website' : 'Visit website'}
                          </a>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900">{business.formatted_address}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                          {business.types?.[0] || 'N/A'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {business.phone_number ? (
                          <div className="flex items-center text-sm text-gray-900">
                            <Phone className="h-4 w-4 mr-1 text-gray-400" />
                            {business.phone_number}
                          </div>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {business.rating && (
                          <div className="flex items-center">
                            <Star className="h-4 w-4 text-yellow-400 mr-1" />
                            <span className="text-sm text-gray-900">{business.rating}</span>
                            <span className="text-xs text-gray-500 ml-1">({business.user_ratings_total})</span>
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {business.road_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(business.crawled_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button
                          onClick={() => handleDelete(business.place_id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          <Delete className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="px-6 py-4 border-t flex items-center justify-between">
              <div className="text-sm text-gray-700">
                {language === 'vi' 
                  ? `Hiển thị ${(currentPage-1)*itemsPerPage + 1} - ${Math.min(currentPage*itemsPerPage, stats.total)} / ${stats.total}`
                  : `Showing ${(currentPage-1)*itemsPerPage + 1} - ${Math.min(currentPage*itemsPerPage, stats.total)} of ${stats.total}`
                }
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => setCurrentPage(p => Math.max(1, p-1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1 border rounded text-sm disabled:opacity-50"
                >
                  {language === 'vi' ? 'Trước' : 'Previous'}
                </button>
                <span className="px-3 py-1 text-sm">
                  {currentPage} / {totalPages}
                </span>
                <button
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p+1))}
                  disabled={currentPage === totalPages}
                  className="px-3 py-1 border rounded text-sm disabled:opacity-50"
                >
                  {language === 'vi' ? 'Sau' : 'Next'}
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default CrawlDataManager;