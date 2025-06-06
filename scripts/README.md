# Scripts để Import Dữ liệu Roads vào Supabase

## Các file quan trọng:

### 1. **resume_import.py** - CHẠY FILE NÀY ĐỂ TIẾP TỤC IMPORT
```bash
python resume_import.py
```
- Tiếp tục import từ county chưa import
- Tự động skip duplicate linearid
- Hiển thị progress

### 2. **check_import_progress.py** - Kiểm tra tiến độ
```bash
python check_import_progress.py
```
- Xem đã import bao nhiêu roads
- Xem còn bao nhiêu counties chưa import

### 3. **test_supabase_connection.py** - Test kết nối
```bash
python test_supabase_connection.py
```

## Các file khác (có thể bỏ qua):
- `import_to_supabase.py` - Script import chính (resume_import.py sẽ gọi file này)
- `process_all_counties.py` - Đã chạy xong để tạo hierarchy
- `extract_city_roads.py` - Đã chạy xong để extract road names

## SQL files:
- `supabase_schema.sql` - Schema database (đã chạy)
- `fix_rls_policies.sql` - Fix RLS (đã chạy)