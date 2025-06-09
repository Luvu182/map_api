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
import {
  Business,
  Search,
  Restaurant,
  LocalGasStation,
  ShoppingCart
} from '@mui/icons-material';

const RoadListSimple = ({ roads, onCrawlClick }) => {
  
  const getCategoryIcon = (category) => {
    if (category.includes('restaurant') || category.includes('food')) return <Restaurant fontSize="small" />;
    if (category.includes('fuel') || category.includes('gas')) return <LocalGasStation fontSize="small" />;
    if (category.includes('shop') || category.includes('store')) return <ShoppingCart fontSize="small" />;
    return <Business fontSize="small" />;
  };

  return (
    <List>
      {roads.map((road) => (
        <ListItem key={road.id}>
          <ListItemText
            primary={
              <Box display="flex" alignItems="center" gap={1}>
                <Typography variant="subtitle1">{road.name}</Typography>
                {road.poi_stats?.count > 0 && (
                  <Chip
                    size="small"
                    icon={<Business fontSize="small" />}
                    label={`${road.poi_stats.count} businesses`}
                    color="primary"
                    variant="outlined"
                  />
                )}
              </Box>
            }
            secondary={
              <Box>
                <Typography variant="caption" color="text.secondary">
                  {road.state_code} • County: {road.county_fips}
                </Typography>
                {road.poi_stats?.top_brands && (
                  <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                    {road.poi_stats.top_brands}
                  </Typography>
                )}
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

export default RoadListSimple;