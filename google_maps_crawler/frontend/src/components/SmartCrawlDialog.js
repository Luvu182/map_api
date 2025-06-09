import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  LinearProgress,
  Chip,
  Alert,
  List,
  ListItem,
  ListItemText,
  CircularProgress
} from '@mui/material';
import {
  Business,
  Phone,
  Schedule,
  Language,
  Search,
  CheckCircle,
  Warning
} from '@mui/icons-material';

const SmartCrawlDialog = ({ open, onClose, roadId, roadName }) => {
  const [loading, setLoading] = useState(true);
  const [crawlPlan, setCrawlPlan] = useState(null);
  const [crawling, setCrawling] = useState(false);
  const [results, setResults] = useState(null);

  useEffect(() => {
    if (open && roadId) {
      fetchCrawlPlan();
    }
  }, [open, roadId]);

  const fetchCrawlPlan = async () => {
    try {
      const response = await fetch(`/api/smart-crawl/road/${roadId}`, {
        method: 'POST'
      });
      const data = await response.json();
      setCrawlPlan(data);
    } catch (error) {
      console.error('Error fetching crawl plan:', error);
    } finally {
      setLoading(false);
    }
  };

  const executeCrawl = async () => {
    setCrawling(true);
    try {
      const response = await fetch('/api/smart-crawl/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          road_id: roadId,
          crawl_points: crawlPlan.crawl_points
        })
      });
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Error executing crawl:', error);
    } finally {
      setCrawling(false);
    }
  };

  const getStrategyIcon = (mode) => {
    switch (mode) {
      case 'targeted': return <Phone color="primary" />;
      case 'discovery': return <Search color="secondary" />;
      case 'verification': return <CheckCircle color="success" />;
      default: return <Business />;
    }
  };

  const getStrategyColor = (mode) => {
    switch (mode) {
      case 'targeted': return 'primary';
      case 'discovery': return 'secondary';
      case 'verification': return 'success';
      default: return 'default';
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Smart Crawl Analysis: {roadName}
      </DialogTitle>
      
      <DialogContent>
        {loading ? (
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        ) : crawlPlan ? (
          <Box>
            {/* OSM Data Overview */}
            <Box mb={3}>
              <Typography variant="h6" gutterBottom>
                Existing OSM Data
              </Typography>
              <Box display="flex" gap={2} flexWrap="wrap">
                <Chip
                  icon={<Business />}
                  label={`${crawlPlan.osm_stats.total_pois} POIs`}
                  variant="outlined"
                />
                <Chip
                  icon={<Phone />}
                  label={`${crawlPlan.osm_stats.with_phone} with phone`}
                  color={crawlPlan.osm_stats.with_phone < crawlPlan.osm_stats.total_pois * 0.5 ? 'warning' : 'success'}
                />
                <Chip
                  icon={<Language />}
                  label={`${crawlPlan.osm_stats.with_website} with website`}
                />
                <Chip
                  icon={<Schedule />}
                  label={`${crawlPlan.osm_stats.with_hours} with hours`}
                />
              </Box>
            </Box>

            {/* Crawl Strategy */}
            <Alert 
              severity={crawlPlan.crawl_strategy.priority === 'high' ? 'warning' : 'info'}
              icon={getStrategyIcon(crawlPlan.crawl_strategy.mode)}
              sx={{ mb: 3 }}
            >
              <Typography variant="subtitle1">
                <strong>Strategy: {crawlPlan.crawl_strategy.mode.toUpperCase()}</strong>
              </Typography>
              <Typography variant="body2">
                {crawlPlan.crawl_strategy.reason}
              </Typography>
            </Alert>

            {/* Crawl Points Preview */}
            <Box mb={3}>
              <Typography variant="h6" gutterBottom>
                Crawl Plan ({crawlPlan.crawl_points.length} points)
              </Typography>
              <List dense sx={{ maxHeight: 200, overflow: 'auto', bgcolor: 'background.paper' }}>
                {crawlPlan.crawl_points.slice(0, 10).map((point, index) => (
                  <ListItem key={index}>
                    <ListItemText
                      primary={point.target_name || `Discovery Point ${index + 1}`}
                      secondary={
                        point.target_name 
                          ? `Update ${point.target_brand ? 'chain' : 'business'} data`
                          : `Search radius: ${point.radius}m`
                      }
                    />
                    {point.priority && (
                      <Chip size="small" label={`Priority: ${point.priority}`} />
                    )}
                  </ListItem>
                ))}
                {crawlPlan.crawl_points.length > 10 && (
                  <ListItem>
                    <ListItemText 
                      primary={`... and ${crawlPlan.crawl_points.length - 10} more points`}
                    />
                  </ListItem>
                )}
              </List>
            </Box>

            {/* API Calls Estimate */}
            <Alert severity="info">
              Estimated Google API calls: <strong>{crawlPlan.estimated_api_calls}</strong>
              {crawlPlan.estimated_api_calls > 50 && (
                <Typography variant="caption" display="block">
                  Consider crawling in batches to manage API costs
                </Typography>
              )}
            </Alert>

            {/* Results */}
            {results && (
              <Box mt={3}>
                <Typography variant="h6" gutterBottom>
                  Crawl Results
                </Typography>
                <Box display="flex" gap={2} mb={2}>
                  <Chip 
                    label={`${results.crawl_summary.businesses_found} businesses found`}
                    color="primary"
                  />
                  <Chip 
                    label={`${results.crawl_summary.updated} updated`}
                    color="success"
                  />
                  <Chip 
                    label={`${results.crawl_summary.created} new`}
                    color="secondary"
                  />
                </Box>
              </Box>
            )}
          </Box>
        ) : (
          <Alert severity="error">
            Failed to load crawl plan
          </Alert>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={executeCrawl}
          disabled={!crawlPlan || crawling}
          startIcon={crawling ? <CircularProgress size={20} /> : <Search />}
        >
          {crawling ? 'Crawling...' : `Start Smart Crawl (${crawlPlan?.estimated_api_calls || 0} calls)`}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SmartCrawlDialog;