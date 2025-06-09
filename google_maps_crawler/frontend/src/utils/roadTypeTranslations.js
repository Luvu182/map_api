// Road type translations for display
export const getRoadTypeLabel = (type, language = 'en') => {
  const translations = {
    vi: {
      'motorway': 'Cao tốc',
      'trunk': 'Quốc lộ', 
      'primary': 'Đường chính',
      'secondary': 'Đường phụ',
      'tertiary': 'Đường nhánh',
      'residential': 'Khu dân cư',
      'living_street': 'Đường nội bộ',
      'service': 'Đường dịch vụ',
      'unclassified': 'Chưa phân loại',
      'footway': 'Đường đi bộ',
      'cycleway': 'Đường xe đạp', 
      'path': 'Đường mòn',
      'track': 'Đường đất',
      'pedestrian': 'Phố đi bộ',
      'steps': 'Cầu thang',
      'corridor': 'Hành lang',
      'bridleway': 'Đường cưỡi ngựa'
    },
    en: {
      'motorway': 'Motorway',
      'trunk': 'Trunk Road',
      'primary': 'Primary Road', 
      'secondary': 'Secondary Road',
      'tertiary': 'Tertiary Road',
      'residential': 'Residential',
      'living_street': 'Living Street',
      'service': 'Service Road',
      'unclassified': 'Unclassified',
      'footway': 'Footway',
      'cycleway': 'Cycleway',
      'path': 'Path',
      'track': 'Track',
      'pedestrian': 'Pedestrian',
      'steps': 'Steps',
      'corridor': 'Corridor',
      'bridleway': 'Bridleway'
    }
  };

  return translations[language]?.[type] || translations['en'][type] || type;
};