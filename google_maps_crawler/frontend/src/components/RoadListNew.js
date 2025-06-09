import React from 'react';
import {
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Box,
  Chip,
  Typography,
  Button
} from '@mui/material';
import { Search } from '@mui/icons-material';
import { useLanguage } from '../contexts/LanguageContext';

// Road type translations
const roadTypeTranslations = {
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
    'track': 'Đường đất'
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
    'track': 'Track'
  }
};

const RoadListNew = ({ roads, onCrawlClick }) => {
  const { language } = useLanguage();
  
  const getTranslatedType = (type) => {
    return roadTypeTranslations[language]?.[type] || roadTypeTranslations['en'][type] || type;
  };

  const formatLocation = (road) => {
    const parts = [];
    if (road.city_name) parts.push(road.city_name);
    if (road.state_code) parts.push(road.state_code);
    if (road.county_fips) parts.push(`County ${road.county_fips}`);
    return parts.join(', ');
  };

  return (
    <List>
      {roads.map((road) => (
        <ListItem key={road.osm_id || road.id}>
          <ListItemText
            primary={
              <Box display="flex" alignItems="center" gap={2}>
                <Typography variant="subtitle1" sx={{ minWidth: '300px' }}>
                  {road.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {formatLocation(road)}
                </Typography>
              </Box>
            }
            secondary={
              <Box display="flex" alignItems="center" gap={1} mt={0.5}>
                <Chip
                  size="small"
                  label={getTranslatedType(road.highway)}
                  variant="outlined"
                />
                {road.ref && (
                  <Chip
                    size="small"
                    label={road.ref}
                    color="primary"
                    variant="outlined"
                  />
                )}
                <Typography variant="caption" color="text.secondary">
                  {road.crawl_status === 'completed' ? 'Đã crawl' : 'Chưa crawl'}
                </Typography>
              </Box>
            }
          />
          
          <ListItemSecondaryAction>
            <Button
              size="small"
              variant="contained"
              startIcon={<Search />}
              onClick={() => onCrawlClick(road)}
            >
              Crawl
            </Button>
          </ListItemSecondaryAction>
        </ListItem>
      ))}
    </List>
  );
};

export default RoadListNew;