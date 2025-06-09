import React, { useState } from 'react';
import {
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Collapse,
  Box,
  Chip,
  Typography,
  Button,
  Tooltip,
  LinearProgress
} from '@mui/material';
import {
  ExpandMore,
  ExpandLess,
  Info,
  Search,
  Business,
  Phone,
  CheckCircle,
  Warning,
  Error
} from '@mui/icons-material';

const RoadListWithPOI = ({ roads, onCrawlClick }) => {
  const [expandedRoads, setExpandedRoads] = useState({});

  const toggleExpand = (roadId) => {
    setExpandedRoads(prev => ({
      ...prev,
      [roadId]: !prev[roadId]
    }));
  };

  const getQualityColor = (quality) => {
    switch (quality) {
      case 'Good': return 'success';
      case 'Fair': return 'warning';
      case 'Poor': return 'error';
      default: return 'default';
    }
  };

  const getQualityIcon = (quality) => {
    switch (quality) {
      case 'Good': return <CheckCircle fontSize="small" />;
      case 'Fair': return <Warning fontSize="small" />;
      case 'Poor': return <Error fontSize="small" />;
      default: return <Info fontSize="small" />;
    }
  };

  return (
    <List>
      {roads.map((road) => (
        <Box key={road.id}>
          <ListItem>
            <ListItemText
              primary={
                <Box display="flex" alignItems="center" gap={1}>
                  <Typography variant="subtitle1">{road.name}</Typography>
                  {road.poi_stats.count > 0 && (
                    <>
                      <Chip
                        size="small"
                        icon={<Business fontSize="small" />}
                        label={road.poi_stats.count}
                        variant="outlined"
                      />
                      <Chip
                        size="small"
                        icon={getQualityIcon(road.poi_stats.quality)}
                        label={road.poi_stats.quality}
                        color={getQualityColor(road.poi_stats.quality)}
                        variant="outlined"
                      />
                    </>
                  )}
                </Box>
              }
              secondary={
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    {road.state_code} • County: {road.county_fips}
                  </Typography>
                  {road.poi_stats.count > 0 && road.poi_stats.top_brands && (
                    <Typography variant="caption" display="block" color="text.secondary">
                      Brands: {road.poi_stats.top_brands}
                    </Typography>
                  )}
                </Box>
              }
            />
            
            <ListItemSecondaryAction>
              <Box display="flex" alignItems="center">
                {road.poi_stats.count > 0 && (
                  <Tooltip title="View POI details">
                    <IconButton 
                      size="small" 
                      onClick={() => toggleExpand(road.id)}
                    >
                      {expandedRoads[road.id] ? <ExpandLess /> : <ExpandMore />}
                    </IconButton>
                  </Tooltip>
                )}
                <Button
                  size="small"
                  variant="contained"
                  startIcon={<Search />}
                  onClick={() => onCrawlClick(road)}
                  sx={{ ml: 1 }}
                >
                  Crawl
                </Button>
              </Box>
            </ListItemSecondaryAction>
          </ListItem>

          {/* Expandable POI Details */}
          <Collapse in={expandedRoads[road.id]} timeout="auto" unmountOnExit>
            <Box sx={{ pl: 4, pr: 4, pb: 2, bgcolor: 'background.paper' }}>
              <Typography variant="subtitle2" gutterBottom>
                POI Data Summary
              </Typography>
              
              <Box display="flex" gap={1} flexWrap="wrap" mb={1}>
                <Chip
                  size="small"
                  icon={<Phone fontSize="small" />}
                  label={`${road.poi_stats.with_phone}/${road.poi_stats.count} have phone (${road.poi_stats.phone_coverage})`}
                  color={road.poi_stats.with_phone < road.poi_stats.count * 0.5 ? 'warning' : 'default'}
                  variant="outlined"
                />
                <Chip
                  size="small"
                  label={`${road.poi_stats.with_website} have website`}
                  variant="outlined"
                />
                <Chip
                  size="small"
                  label={`${road.poi_stats.with_hours} have hours`}
                  variant="outlined"
                />
                {road.poi_stats.brands > 0 && (
                  <Chip
                    size="small"
                    label={`${road.poi_stats.brands} chain brands`}
                    color="primary"
                    variant="outlined"
                  />
                )}
              </Box>

              {/* Data Quality Bar */}
              <Box mt={1}>
                <Typography variant="caption" color="text.secondary">
                  Phone coverage: {road.poi_stats.phone_coverage}
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={parseInt(road.poi_stats.phone_coverage) || 0}
                  color={getQualityColor(road.poi_stats.quality)}
                  sx={{ height: 6, borderRadius: 1 }}
                />
              </Box>
            </Box>
          </Collapse>
        </Box>
      ))}
    </List>
  );
};

export default RoadListWithPOI;