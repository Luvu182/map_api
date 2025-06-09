import React, { useState, useEffect } from 'react';
import { fetchTargetCities } from '../api/crawler';
import { getStateName } from '../data/stateNames';
import { useLanguage } from '../contexts/LanguageContext';
import { t } from '../translations/translations';

const CitySelector = ({ selectedState, onCitySelect, className = '' }) => {
  const { language } = useLanguage();
  const [cities, setCities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedCity, setSelectedCity] = useState('');

  useEffect(() => {
    if (selectedState) {
      loadCitiesForState();
    } else {
      setCities([]);
      setSelectedCity('');
    }
  }, [selectedState]);

  const loadCitiesForState = async () => {
    setLoading(true);
    try {
      const data = await fetchTargetCities(selectedState);
      setCities(data.cities || []);
    } catch (error) {
      console.error('Failed to load cities:', error);
      setCities([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCityChange = (e) => {
    const cityData = e.target.value;
    setSelectedCity(cityData);
    
    if (cityData) {
      const [cityName, stateCode] = cityData.split('|');
      onCitySelect({ city_name: cityName, state_code: stateCode });
    } else {
      onCitySelect(null);
    }
  };

  return (
    <div className={className}>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        3. {t('targetCity', language)} <span className="text-red-500">*</span> ({cities.length} {t('cities', language)})
      </label>
      <select
        value={selectedCity}
        onChange={handleCityChange}
        disabled={!selectedState || loading}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
      >
        <option value="">
          {loading ? t('loading', language) : t('selectTargetCity', language)}
        </option>
        {cities.map(city => (
          <option 
            key={`${city.city_name}|${city.state_code}`} 
            value={`${city.city_name}|${city.state_code}`}
          >
            {city.city_name} ({city.road_count} roads)
          </option>
        ))}
      </select>
      {selectedState && cities.length === 0 && !loading && (
        <p className="mt-1 text-sm text-red-500">
          No target cities found for {getStateName(selectedState, language)}
        </p>
      )}
    </div>
  );
};

export default CitySelector;