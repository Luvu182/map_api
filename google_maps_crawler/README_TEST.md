# Testing New Google Maps Places API

## Setup
1. Set your API key:
   ```bash
   export GOOGLE_MAPS_API_KEY='your-api-key-here'
   ```

2. Run the test:
   ```bash
   cd /Users/luvu/Data_US_100k_pop/google_maps_crawler
   python test_new_api.py
   ```

## What it tests:
1. **Basic text search** - Simple query
2. **Road-based search** - Search businesses on specific road
3. **Enterprise tier** - All fields including phone, website, hours
4. **Real road test** - Using actual high-potential road from DB

## Expected output:
- Number of results found
- Fields received (for enterprise tier)
- Sample business details
- Comparison with OSM POI data

## If errors occur:
- Check API key is valid
- Ensure you have enabled Places API (New) in Google Cloud Console
- Check quota/billing is set up

## API Response fields:
Enterprise tier should return:
- nationalPhoneNumber / internationalPhoneNumber
- websiteUri
- rating & userRatingCount
- currentOpeningHours / regularOpeningHours
- priceLevel / priceRange