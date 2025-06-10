# Project Cleanup Guide & Common Errors

## 🧹 Files to Remove/Archive

### Root Directory Scripts (Move to scripts/)
- `generate_password_hash.py` → scripts/utilities/
- `setup_auth.sh` → scripts/setup/
- `update_unified_roads_view.sql` → scripts/

### Duplicate/Temporary Documentation
**Remove these files:**
- `API_FRONTEND_CHECK.md` - Temporary check
- `DASHBOARD_POI_TODO.md` - Old todo list
- `NEXT_STEPS.md` - Temporary planning
- `TIGER_REFERENCES_REPORT.md` - Obsolete (using OSM now)
- `COMPLETE_GUIDE_FROM_SCRATCH.md` - Duplicate of README
- `DASHBOARD_STATUS.md` - Keep only `DASHBOARD_UPDATE_SUMMARY.md`
- `CITY_MAPPING.md` - Keep only `CITY_BOUNDARY_MAPPING.md`
- `DATABASE_OPTIMIZATION.md` - Merge into `OPTIMIZATION_REPORT.md`
- `FRONTEND_CITY_ONLY.md` - Merge into `UPDATE_FRONTEND_CITYMAP.md`
- `OSM_MIGRATION_STATUS.md` - Already in `OSM_IMPORT_FINAL_STATUS.md`

### Consolidate Business Field Docs
Merge these into `OSM_BUSINESS_FIELDS_GUIDE.md`:
- `OSM_ALL_BUSINESS_FIELDS_LIST.md`
- `OSM_COMPLETE_BUSINESS_FIELDS.md` 
- `OSM_BUSINESS_DATA_ANALYSIS.md`

### City Lists
Keep only: `target_cities_346.txt`
Remove:
- `cities_list_only.txt`
- `exact_cities_list.txt`
- `parsed_cities_output.txt`

### Backup Files
- `docker-compose.yml.backup` → Remove or move to backups/

## 📁 Recommended Directory Structure

```
Data_US_100k_pop/
├── README.md                    # Main documentation
├── ARCHITECTURE.md              # System design
├── DEPLOYMENT.md                # Deployment guide
├── docker-compose.yml           # Docker configuration
├── docker-compose-osm.yml       # OSM specific config
├── Dockerfile.osm               # OSM container
├── .env.example                 # Environment template
│
├── docs/                        # All documentation
│   ├── DATABASE_REPORT.md
│   ├── OSM_IMPORT_GUIDE.md
│   ├── OSM_BUSINESS_FIELDS.md
│   ├── OPTIMIZATION_GUIDE.md
│   └── MAP_VISUALIZATION.md
│
├── scripts/                     # All scripts organized
│   ├── setup/                   # Initial setup scripts
│   ├── import/                  # Import scripts
│   ├── database/                # Database scripts
│   ├── backup/                  # Backup scripts
│   └── utilities/               # Utility scripts
│
├── google_maps_crawler/         # Crawler application
├── raw_data/                    # Raw data files
├── processed_data/              # Processed outputs
└── postgres-data/               # Database files
```

## ⚠️ Common Errors & Solutions

### 1. Docker Container Path Issues
**Error:** `RuntimeError: Open failed for '/Users/luvu/...': No such file or directory`

**Cause:** Using host path instead of container path

**Solution:**
```bash
# ❌ Wrong
FILE="/Users/luvu/Data_US_100k_pop/raw_data/data_osm/file.pbf"

# ✅ Correct
FILE="/data/file.pbf"  # Container path
```

### 2. psql Variable Syntax Error
**Error:** `ERROR: syntax error at or near ':'"`

**Cause:** psql variables not supported in some contexts

**Solution:**
```bash
# ❌ Wrong
psql -v state='CA' -c "SELECT * FROM table WHERE state = :state"

# ✅ Correct - Embed variable in SQL
cat > temp.sql << EOF
SELECT * FROM table WHERE state = 'CA';
EOF
psql -f temp.sql
```

### 3. Shell Associative Array Error  
**Error:** `declare: -A: invalid option`

**Cause:** Shell doesn't support associative arrays

**Solution:**
```bash
# ❌ Wrong
declare -A STATES=(["alabama"]="AL")

# ✅ Correct - Use pairs
STATES=("alabama:AL" "alaska:AK")
IFS=':' read -r name code <<< "$state_pair"
```

### 4. Container Not Running
**Error:** `container c288e924440f is not running`

**Solution:**
```bash
docker ps -a  # Check all containers
docker start container_name  # Start if stopped
```

### 5. Multiple Script Files Created
**Issue:** Creating new scripts instead of fixing existing ones

**Best Practice:**
- Always check for existing scripts first
- Use `import_all_states_types.sh` for POI import
- Don't create `*_fixed.sh`, `*_v2.sh` versions
- Consolidate fixes into original files

## 🚀 Quick Commands

### Clean up project
```bash
# Create archive directory
mkdir -p archive/scripts archive/docs

# Move old scripts
mv fix_*.sql fix_*.py archive/scripts/
mv *_old.* *_backup.* archive/

# Move duplicate docs  
mv DASHBOARD_STATUS.md CITY_MAPPING.md archive/docs/
```

### Import all states
```bash
./scripts/import_all_states_types.sh
```

### Check import status
```bash
docker exec roads-postgres psql -U postgres -d roads_db -c "
    SELECT state_code, COUNT(*) as pois 
    FROM osm_businesses 
    GROUP BY state_code 
    ORDER BY state_code"
```