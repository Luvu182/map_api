import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { t } from '../translations/translations';

const BusinessPotentialCard = ({ lat, lon, roadName }) => {
  const { language } = useLanguage();
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (lat && lon) {
      fetchAnalysis();
    }
  }, [lat, lon]);

  const fetchAnalysis = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`http://localhost:8000/api/analyze-location?lat=${lat}&lon=${lon}`);
      if (!response.ok) {
        throw new Error(language === 'vi' 
          ? 'Không thể phân tích khu vực. Vui lòng đảm bảo backend API đang chạy.'
          : 'Failed to analyze location. Please ensure the backend API is running.');
      }
      
      const data = await response.json();
      setAnalysis(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!lat || !lon) return null;
  if (loading) return <div className="p-4 text-center">{t('loading', language)}</div>;
  if (error) return <div className="p-4 text-red-600">Error: {error}</div>;
  if (!analysis) return null;

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 65) return 'text-blue-600';
    if (score >= 50) return 'text-yellow-600';
    if (score >= 35) return 'text-orange-600';
    return 'text-red-600';
  };

  const getRatingBadgeColor = (rating) => {
    const colors = {
      'Excellent': 'bg-green-100 text-green-800',
      'Very Good': 'bg-blue-100 text-blue-800',
      'Good': 'bg-yellow-100 text-yellow-800',
      'Fair': 'bg-orange-100 text-orange-800',
      'Poor': 'bg-red-100 text-red-800',
      'Very Poor': 'bg-gray-100 text-gray-800'
    };
    return colors[rating] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mb-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          {t('businessPotential', language)}
        </h3>
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${getRatingBadgeColor(analysis.rating)}`}>
          {language === 'vi' ? t(analysis.rating.toLowerCase().replace(' ', ''), language) : analysis.rating}
        </div>
      </div>

      {/* Score Display */}
      <div className="mb-6">
        <div className="flex items-end space-x-2">
          <span className={`text-3xl font-bold ${getScoreColor(analysis.score)}`}>
            {analysis.score}
          </span>
          <span className="text-gray-500 text-lg">/ 100</span>
        </div>
        <p className="text-sm text-gray-600 mt-1">{roadName}</p>
      </div>

      {/* Recommendation */}
      <div className="mb-6 p-4 bg-blue-50 rounded-lg">
        <h4 className="font-medium text-gray-900 mb-2">
          {language === 'vi' ? 'Đánh giá' : 'Recommendation'}
        </h4>
        <p className="text-sm text-gray-700">{analysis.recommendation}</p>
      </div>

      {/* Best Business Types */}
      <div className="mb-6">
        <h4 className="font-medium text-gray-900 mb-2">
          {language === 'vi' ? 'Phù hợp với' : 'Best for'}
        </h4>
        <div className="flex flex-wrap gap-2">
          {analysis.business_insights?.best_for?.map((type, index) => (
            <span key={index} className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
              {type}
            </span>
          ))}
        </div>
      </div>

      {/* Challenges */}
      {analysis.business_insights?.challenges?.length > 0 && (
        <div className="mb-6">
          <h4 className="font-medium text-gray-900 mb-2">
            {language === 'vi' ? 'Thách thức' : 'Challenges'}
          </h4>
          <ul className="list-disc list-inside space-y-1">
            {analysis.business_insights.challenges.map((challenge, index) => (
              <li key={index} className="text-sm text-gray-600">{challenge}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Score Breakdown */}
      <details className="mt-4">
        <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
          {language === 'vi' ? 'Chi tiết điểm số' : 'Score breakdown'}
        </summary>
        <div className="mt-3 space-y-2">
          {Object.entries(analysis.score_breakdown || {}).map(([key, value]) => {
            const labels = {
              density_score: language === 'vi' ? 'Mật độ' : 'Density',
              accessibility_score: language === 'vi' ? 'Khả năng tiếp cận' : 'Accessibility',
              road_quality_score: language === 'vi' ? 'Chất lượng đường' : 'Road Quality',
              area_type_score: language === 'vi' ? 'Loại khu vực' : 'Area Type',
              traffic_score: language === 'vi' ? 'Lưu lượng' : 'Traffic Flow'
            };
            const maxScores = {
              density_score: 30,
              accessibility_score: 30,
              road_quality_score: 20,
              area_type_score: 20,
              traffic_score: 10
            };
            
            return (
              <div key={key} className="flex justify-between items-center">
                <span className="text-sm text-gray-600">{labels[key] || key}</span>
                <div className="flex items-center space-x-2">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full" 
                      style={{width: `${(value / maxScores[key]) * 100}%`}}
                    />
                  </div>
                  <span className="text-sm text-gray-700 w-12 text-right">
                    {value}/{maxScores[key]}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </details>
    </div>
  );
};

export default BusinessPotentialCard;