# Google Maps Business Crawler

App crawl thông tin businesses từ Google Maps dựa trên database 5.15M roads.

## Mục đích
- Crawl thông tin cửa hàng, nhà hàng, dịch vụ dọc theo các con đường
- Sử dụng Google Maps Text Search API với keyword + road name
- Lưu vào database để phân tích thương mại
- Ưu tiên đường có tên (3.4M roads)

## Tech Stack
- **Backend**: Python/FastAPI
- **Frontend**: React.js với Tailwind CSS
- **Database**: PostgreSQL (Supabase hoặc self-hosted)
- **APIs**: Google Maps Places Text Search API
- **State Management**: LocalStorage cho crawl status (tạm thời)

## Cấu trúc dự án
```
google_maps_crawler/
├── README.md
├── README_UI.md            # UI setup guide
├── requirements.txt
├── app/
│   ├── main.py             # FastAPI endpoints
│   ├── config.py           # Config & credentials
│   ├── models.py           # Pydantic models
│   ├── crawler/
│   │   ├── google_maps.py  # Google Maps API wrapper
│   │   └── road_sampler.py # Sample points along roads
│   └── database/
│       ├── supabase_client.py      # Database operations
│       ├── schemas.sql             # Main database schema
│       └── schemas_crawl_status.sql # Crawl tracking schema
└── frontend/
    ├── package.json
    ├── src/
    │   ├── App.js          # Main React app
    │   ├── api/
    │   │   └── crawler.js  # API client
    │   ├── components/
    │   │   ├── Dashboard.js     # Statistics view
    │   │   ├── CrawlControl.js  # Main crawl interface
    │   │   ├── MapView.js       # Google Maps integration
    │   │   └── BusinessList.js  # Results display
    │   └── data/
    │       └── countyNames.js   # County FIPS mapping
    └── public/
```

## New Features (Latest Update)

### 1. Keyword-First Search Flow
- Nhập business keyword đầu tiên (clothing store, restaurant, etc.)
- Filter theo State → County → Road Type
- Hiển thị danh sách roads với pagination (50 roads/page)

### 2. Individual Road Crawling
- Mỗi road có nút "Crawl" riêng
- API search với query: `"{keyword}" near {road_name}, {city}, {state}"`
- Real-time status updates: Not Crawled → Processing → Completed/Failed

### 3. Crawl Status Tracking
- Database schema cho persistent storage (khi có database)
- Tạm thời dùng localStorage cho browser
- Filter "Show only uncrawled roads"
- Statistics: Total, Crawled, Not Crawled, Failed

### 4. UI Improvements
- County names hiển thị đầy đủ (323 counties)
- Road type tooltips với giải thích chi tiết
- Responsive design với Tailwind CSS
- Loading states và error handling