"""
Enhanced search functionality with road name normalization
"""
from typing import List, Dict, Optional
import re

def generate_road_variants(search_term: str) -> List[str]:
    """
    Generate variants of a road name for better matching
    """
    variants = [search_term]
    
    # Common abbreviations
    abbreviations = {
        'Street': ['St', 'St.'],
        'Avenue': ['Ave', 'Ave.'],
        'Boulevard': ['Blvd', 'Blvd.'],
        'Drive': ['Dr', 'Dr.'],
        'Road': ['Rd', 'Rd.'],
        'Lane': ['Ln', 'Ln.'],
        'Court': ['Ct', 'Ct.'],
        'Place': ['Pl', 'Pl.'],
        'Highway': ['Hwy', 'Hwy.'],
        'Parkway': ['Pkwy', 'Pky'],
        'North': ['N', 'N.'],
        'South': ['S', 'S.'],
        'East': ['E', 'E.'],
        'West': ['W', 'W.']
    }
    
    # Generate variants with abbreviations
    for full_form, abbrevs in abbreviations.items():
        if full_form.lower() in search_term.lower():
            for abbrev in abbrevs:
                variant = re.sub(full_form, abbrev, search_term, flags=re.IGNORECASE)
                if variant not in variants:
                    variants.append(variant)
        
        # Also check reverse (abbreviation to full form)
        for abbrev in abbrevs:
            if abbrev.lower() in search_term.lower():
                variant = re.sub(r'\b' + re.escape(abbrev) + r'\b', full_form, search_term, flags=re.IGNORECASE)
                if variant not in variants:
                    variants.append(variant)
    
    # Special case: Avenue ↔ Street (common Google Maps difference)
    if 'Avenue' in search_term or 'Ave' in search_term:
        variants.append(re.sub(r'Avenue|Ave', 'Street', search_term, flags=re.IGNORECASE))
        variants.append(re.sub(r'Avenue|Ave', 'St', search_term, flags=re.IGNORECASE))
    
    if 'Street' in search_term or 'St' in search_term:
        variants.append(re.sub(r'Street|St\b', 'Avenue', search_term, flags=re.IGNORECASE))
        variants.append(re.sub(r'Street|St\b', 'Ave', search_term, flags=re.IGNORECASE))
    
    # Add directional variants
    if not any(dir in search_term for dir in ['North', 'South', 'East', 'West', 'N ', 'S ', 'E ', 'W ']):
        # Add common directional prefixes
        for direction in ['N', 'S', 'E', 'W', 'North', 'South', 'East', 'West']:
            variants.append(f"{direction} {search_term}")
    
    return list(set(variants))  # Remove duplicates

def build_search_query(search_term: str, state_code: Optional[str] = None, 
                      county_fips: Optional[str] = None, limit: int = 50) -> tuple:
    """
    Build an enhanced search query with normalization
    """
    variants = generate_road_variants(search_term)
    
    # Build the WHERE clause
    where_conditions = ["r.name IS NOT NULL"]
    params = []
    
    # Add state filter
    if state_code:
        where_conditions.append("r.state_code = %s")
        params.append(state_code)
    
    # Add county filter
    if county_fips:
        where_conditions.append("r.county_fips = %s")
        params.append(county_fips)
    
    # Add name conditions (exact match first, then variants, then partial)
    name_conditions = []
    
    # Exact match
    name_conditions.append("r.name = %s")
    params.append(search_term)
    
    # Case insensitive match
    name_conditions.append("LOWER(r.name) = LOWER(%s)")
    params.append(search_term)
    
    # Variant matches
    if len(variants) > 1:
        placeholders = ', '.join(['%s'] * len(variants))
        name_conditions.append(f"r.name = ANY(ARRAY[{placeholders}])")
        params.extend(variants)
    
    # Partial match
    name_conditions.append("r.name ILIKE %s")
    params.append(f"%{search_term}%")
    
    # Combine name conditions with OR
    where_conditions.append(f"({' OR '.join(name_conditions)})")
    
    # Build the final query
    query = f"""
        WITH matches AS (
            SELECT DISTINCT
                r.osm_id,
                r.name as road_name,
                r.highway,
                r.state_code,
                r.county_fips,
                c.county_name,
                s.state_name,
                COUNT(*) OVER (PARTITION BY r.name, r.state_code, r.county_fips) as segment_count,
                SUM(ST_Length(geography(r.geometry))) OVER (PARTITION BY r.name, r.state_code, r.county_fips) / 1000.0 as total_length_km,
                CASE 
                    WHEN r.name = %s THEN 1
                    WHEN LOWER(r.name) = LOWER(%s) THEN 2
                    WHEN r.name = ANY(ARRAY[{placeholders if len(variants) > 1 else "'dummy'"}]) THEN 3
                    WHEN r.name ILIKE %s THEN 4
                    ELSE 5
                END as match_score
            FROM osm_roads_main r
            LEFT JOIN counties c ON r.county_fips = c.county_fips
            LEFT JOIN states s ON r.state_code = s.state_code
            WHERE {' AND '.join(where_conditions)}
        )
        SELECT DISTINCT ON (road_name, state_code, county_fips)
            MIN(osm_id) as osm_id,
            road_name,
            MIN(highway) as highway,
            state_code,
            county_fips,
            county_name,
            state_name,
            segment_count,
            total_length_km
        FROM matches
        GROUP BY road_name, state_code, county_fips, county_name, state_name, segment_count, total_length_km, match_score
        ORDER BY 
            road_name, state_code, county_fips,
            match_score ASC,
            segment_count DESC
        LIMIT %s
    """
    
    # Add match score params
    params.extend([search_term, search_term])
    if len(variants) > 1:
        params.extend(variants)
    params.extend([f"%{search_term}%", limit])
    
    return query, params

def search_roads_enhanced(conn, search_term: str, state_code: Optional[str] = None,
                         county_fips: Optional[str] = None, limit: int = 50) -> List[Dict]:
    """
    Enhanced road search with name normalization
    """
    query, params = build_search_query(search_term, state_code, county_fips, limit)
    
    cur = conn.cursor()
    cur.execute(query, params)
    
    results = []
    for row in cur.fetchall():
        results.append({
            'osm_id': row[0],
            'name': row[1],  # Changed from road_name to name to match frontend
            'highway': row[2],
            'state_code': row[3],
            'county_fips': row[4],
            'county_name': row[5],
            'state_name': row[6],
            'segment_count': row[7],
            'total_length_km': row[8]
        })
    
    cur.close()
    return results