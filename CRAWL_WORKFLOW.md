# Google Maps Crawl Workflow

## Overview
Hệ thống crawl businesses dọc theo 5.15M roads trong database sử dụng Google Maps Text Search API.

## Crawl Flow

### 1. User Input
```
1. Business Keyword (Required)
   - Ví dụ: "clothing store", "restaurant", "grocery store"
   - Keyword này sẽ được combine với road name khi search

2. Filters (Optional)
   - State: Chọn từ 50 states
   - County: Chọn từ 323 counties (hiển thị tên đầy đủ)
   - Road Type: Primary/Secondary/Local/Special Roads

3. Click "View Roads"
```

### 2. Road List Display
```
- Hiển thị 50 roads/page với pagination
- Mỗi road hiển thị:
  - Road Name (hoặc "Unnamed" nếu không có tên)
  - Road Type (với color coding)
  - MTFCC Code
  - State Code
  - County Name (không phải FIPS code)
  - Crawl Status
  - Action Button
```

### 3. Crawl Process
```
1. User click "Crawl" button trên road cụ thể
2. Frontend gọi: POST /crawl/road/{road_id}?keyword={keyword}
3. Backend:
   - Update crawl_status table: status = 'processing'
   - Background task: Google Maps Text Search
   - Query format: "{keyword} near {road_name}, {county}, {state}"
   - Save results to businesses table
   - Update crawl_status: status = 'completed'
4. Frontend:
   - Show spinner while processing
   - Poll for status updates
   - Update UI when complete
```

### 4. Status Management

#### Database Schema (crawl_status table)
```sql
- road_linearid: Road ID
- keyword: Search keyword
- status: pending/processing/completed/failed
- businesses_found: Number of results
- error_message: Error detail if failed
- created_at/updated_at: Timestamps
```

#### Status Display
- **Not Crawled**: Blue badge, shows "Crawl" button
- **Processing**: Yellow badge with spinner
- **Completed**: Green badge with checkmark
- **Failed**: Red badge, shows "Retry" button

### 5. Data Storage

#### Roads Table (Existing - 5.15M records)
```sql
- linearid: Unique ID
- fullname: Road name (nullable)
- mtfcc: Road classification
- road_category: Primary/Secondary/Local/Special
- state_code: 2-letter state code
- county_fips: 5-digit FIPS code
```

#### Businesses Table (To be created)
```sql
- place_id: Google Maps Place ID
- business_name: Business name
- formatted_address: Full address
- latitude/longitude: Coordinates
- rating: Google rating
- user_ratings_total: Review count
- business_types: Array of types
- road_linearid: Associated road
- keyword_used: Search keyword
- created_at: Crawl timestamp
```

## API Endpoints

### Backend (FastAPI)
```
GET  /roads/unprocessed?limit=1000     # Get roads to display
GET  /roads/crawl-status               # Get crawl status by filters
POST /crawl/road/{road_id}?keyword=X   # Crawl single road
GET  /counties/{state_code}            # Get counties for state
```

### Frontend API Client
```javascript
fetchUnprocessedRoads(limit)           // Get roads
fetchCrawlStatus(state, county, keyword) // Get status
crawlSingleRoad(roadId, keyword)       // Start crawl
fetchCountiesByState(stateCode)        // Get counties
```

## Cost Estimation

### Google Maps Pricing
- Text Search: $32 per 1,000 requests
- Per road: ~5 searches = $0.16
- Monthly $200 credit = ~1,250 roads

### Optimization Strategies
1. Cache results by keyword + road
2. Skip roads already crawled with same keyword
3. Prioritize high-traffic roads (Primary/Secondary)
4. Batch similar searches in same area

## Error Handling

### Common Errors
1. **API Quota Exceeded**: Pause crawling, retry later
2. **No Results Found**: Mark as completed with 0 results
3. **Network Timeout**: Retry up to 3 times
4. **Invalid API Key**: Stop all crawling, alert user

### Recovery
- Failed crawls can be retried
- Progress saved in database
- Can resume from any point

## Performance Considerations

### Frontend
- Pagination (50 roads/page) to avoid large DOM
- Debounced search to reduce API calls
- LocalStorage fallback if database unavailable
- Virtual scrolling for large lists (future)

### Backend
- Background tasks for crawling
- Database connection pooling
- Rate limiting per API quotas
- Bulk inserts for businesses

## Future Enhancements

1. **Bulk Operations**
   - Select multiple roads to crawl
   - Queue management system
   - Priority crawling

2. **Advanced Filtering**
   - Filter by city boundaries
   - Distance from point
   - Road name patterns

3. **Export Features**
   - CSV/JSON export
   - Business analytics
   - Heat maps

4. **Real-time Updates**
   - WebSocket for live status
   - Progress bars
   - Notifications