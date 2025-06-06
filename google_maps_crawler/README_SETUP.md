# Setup Instructions

## 1. Install Dependencies
```bash
cd google_maps_crawler
pip install -r requirements.txt
```

## 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials:
# - SUPABASE_KEY (from your Supabase project)
# - GOOGLE_MAPS_API_KEY (from Google Cloud Console)
```

## 3. Setup Database Tables
Run the SQL in Supabase SQL Editor:
```bash
# Copy content from app/database/schemas.sql
# Run in https://supabase.com/dashboard/project/zutlqkirprynkzfddnlt/sql
```

## 4. Google Maps API Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create new project or select existing
3. Enable APIs:
   - Places API
   - Geocoding API
4. Create API Key with restrictions:
   - Application restrictions: HTTP referrers or IP addresses
   - API restrictions: Only enabled APIs
5. Copy API key to .env file

## 5. Run the Application
```bash
# Start FastAPI server
uvicorn app.main:app --reload

# API will be available at http://localhost:8000
# Documentation at http://localhost:8000/docs
```

## 6. Start Crawling
```bash
# In another terminal
python scripts/start_crawl.py
```

## API Endpoints

### GET /stats
Get crawling statistics

### GET /roads/unprocessed
List roads that haven't been crawled

### POST /crawl/start
Start crawling process
- Parameters:
  - state_code (optional): State to crawl (e.g., "CA")
  - limit: Number of roads to process

## Rate Limits & Costs

### Google Maps API Pricing (as of 2024)
- **Places Nearby Search**: $32 per 1,000 requests
- **Place Details**: $17 per 1,000 requests
- **Geocoding**: $5 per 1,000 requests

### Free Tier
- $200 monthly credit = ~6,250 nearby searches
- Approximately 1,250 roads with 5 sample points each

### Recommendations
1. Start with high-traffic roads (Primary/Secondary)
2. Focus on specific cities/areas
3. Use caching to avoid duplicate searches
4. Monitor usage in Google Cloud Console

## Next Steps
1. Implement actual road geometry sampling (currently using dummy coordinates)
2. Add Redis/Celery for distributed crawling
3. Create dashboard for monitoring progress
4. Add data validation and deduplication
5. Implement incremental updates