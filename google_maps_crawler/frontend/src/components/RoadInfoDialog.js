import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Chip,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Alert
} from '@mui/material';
import {
  Business,
  Phone,
  Language,
  Schedule,
  Info
} from '@mui/icons-material';

const RoadInfoDialog = ({ open, onClose, roadId, roadName, onCrawl }) => {
  const [loading, setLoading] = useState(true);
  const [poiInfo, setPoiInfo] = useState(null);

  useEffect(() => {
    if (open && roadId) {
      fetchPoiInfo();
    }
  }, [open, roadId]);

  const fetchPoiInfo = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/roads/${roadId}/poi-info`);
      const data = await response.json();
      setPoiInfo(data);
    } catch (error) {
      console.error('Error fetching POI info:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCrawl = () => {
    onClose();
    onCrawl(roadId);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <Info />
          Road Information
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {loading ? (
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        ) : poiInfo ? (
          <Box>
            {/* Road Name */}
            <Typography variant="h6" gutterBottom>
              {roadName}
            </Typography>
            
            {/* POI Statistics */}
            <Box mb={3}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                OpenStreetMap Data:
              </Typography>
              
              {poiInfo.poi_stats.total > 0 ? (
                <>
                  <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
                    <Chip
                      icon={<Business />}
                      label={`${poiInfo.poi_stats.total} businesses`}
                      size="small"
                    />
                    <Chip
                      icon={<Phone />}
                      label={`${poiInfo.poi_stats.with_phone} have phone`}
                      size="small"
                      color={poiInfo.poi_stats.with_phone < poiInfo.poi_stats.total * 0.5 ? 'warning' : 'default'}
                    />
                    <Chip
                      icon={<Language />}
                      label={`${poiInfo.poi_stats.with_website} have website`}
                      size="small"
                    />
                    <Chip
                      icon={<Schedule />}
                      label={`${poiInfo.poi_stats.with_hours} have hours`}
                      size="small"
                    />
                  </Box>
                  
                  <Alert 
                    severity={poiInfo.poi_stats.data_quality === 'Good' ? 'success' : 'warning'}
                    sx={{ mb: 2 }}
                  >
                    Data Quality: {poiInfo.poi_stats.data_quality}
                    {poiInfo.poi_stats.data_quality === 'Needs Update' && 
                      ` - Only ${poiInfo.poi_stats.phone_coverage} have phone numbers`
                    }
                  </Alert>
                  
                  {/* Top Businesses */}
                  {poiInfo.top_businesses.length > 0 && (
                    <>
                      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                        Sample businesses on this road:
                      </Typography>
                      <List dense sx={{ bgcolor: 'background.paper' }}>
                        {poiInfo.top_businesses.slice(0, 5).map((biz, index) => (
                          <ListItem key={index}>
                            <ListItemText
                              primary={biz.name}
                              secondary={
                                <Box component="span" display="flex" gap={1}>
                                  <Typography variant="caption">{biz.type}</Typography>
                                  {biz.has_phone === 'No' && 
                                    <Typography variant="caption" color="warning.main">• No phone</Typography>
                                  }
                                </Box>
                              }
                            />
                          </ListItem>
                        ))}
                      </List>
                    </>
                  )}
                </>
              ) : (
                <Alert severity="info">
                  No existing business data for this road
                </Alert>
              )}
            </Box>
          </Box>
        ) : (
          <Alert severity="error">
            Failed to load road information
          </Alert>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Close</Button>
        <Button 
          variant="contained" 
          onClick={handleCrawl}
          color="primary"
        >
          Crawl with Google Maps
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default RoadInfoDialog;