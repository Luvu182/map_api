# New York City - TIGER Data Crawl Plan

## 1. Nguồn Data
- **Website**: https://www2.census.gov/geo/tiger/TIGER2024/ROADS/
- **Loại data**: TIGER/Line Shapefiles (dữ liệu địa lý đường phố)
- **Năm**: 2024 (phiên bản mới nhất)

## 2. NYC gồm 5 Boroughs = 5 Counties

| Borough | County Name | FIPS Code | File cần download |
|---------|------------|-----------|-------------------|
| Manhattan | New York County | 36061 | tl_2024_36061_roads.zip |
| Brooklyn | Kings County | 36047 | tl_2024_36047_roads.zip |
| Queens | Queens County | 36081 | tl_2024_36081_roads.zip |
| Bronx | Bronx County | 36005 | tl_2024_36005_roads.zip |
| Staten Island | Richmond County | 36085 | tl_2024_36085_roads.zip |

## 3. URL đầy đủ cho mỗi file
```
https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_36061_roads.zip
https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_36047_roads.zip
https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_36081_roads.zip
https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_36005_roads.zip
https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_36085_roads.zip
```

## 4. Mỗi file ZIP chứa gì?
Sau khi giải nén, mỗi file ZIP sẽ có:
- `.shp` - File chính chứa geometry của đường
- `.dbf` - Database chứa attributes (tên đường, loại đường...)
- `.shx` - Index file
- `.prj` - Projection information
- `.cpg` - Character encoding
- `.xml` - Metadata

## 5. Cấu trúc thư mục sau khi download
```
Data_US_100k_pop/
└── raw_data/
    └── shapefiles/
        ├── tl_2024_36061_roads.zip
        ├── tl_2024_36061_roads/
        │   ├── tl_2024_36061_roads.shp
        │   ├── tl_2024_36061_roads.dbf
        │   ├── tl_2024_36061_roads.shx
        │   └── ...
        ├── tl_2024_36047_roads.zip
        ├── tl_2024_36047_roads/
        │   └── ...
        └── ... (tương tự cho 3 counties còn lại)
```

## 6. Dung lượng ước tính
- Manhattan: ~10-20 MB
- Brooklyn: ~20-30 MB  
- Queens: ~30-40 MB
- Bronx: ~15-25 MB
- Staten Island: ~10-15 MB
- **Tổng**: ~85-130 MB cho NYC

## 7. Các trường dữ liệu quan trọng trong DBF
- `LINEARID`: ID duy nhất của đường
- `FULLNAME`: Tên đầy đủ (ví dụ: "5th Ave", "Broadway")
- `RTTYP`: Route type (I, U, S, C, M, O)
- `MTFCC`: Feature class code
  - S1100: Primary Road
  - S1200: Secondary Road
  - S1400: Local Street
  - ...

## 8. Process Flow
1. Download 5 file ZIP từ Census.gov
2. Giải nén mỗi file vào thư mục riêng
3. Verify tính toàn vẹn của data
4. Sau đó sẽ xử lý bằng GeoPandas để:
   - Đọc shapefile
   - Filter theo loại đường
   - Merge data của 5 boroughs
   - Export sang format phù hợp cho Google Maps

## Bạn muốn tôi bắt đầu download không?