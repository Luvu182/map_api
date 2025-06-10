"""
Optimized enhanced search using materialized view
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
    
    return list(set(variants))[:10]  # Limit to 10 variants max

def build_search_query_optimized(search_term: str, state_code: Optional[str] = None, 
                                county_fips: Optional[str] = None, limit: int = 50) -> tuple:
    """
    Build an optimized search query using materialized view
    """
    variants = generate_road_variants(search_term)
    
    # Build WHERE conditions
    where_conditions = []
    params = []
    
    # Add state filter
    if state_code:
        where_conditions.append("state_code = %s")
        params.append(state_code)
    
    # Add county filter
    if county_fips:
        where_conditions.append("county_fips = %s")
        params.append(county_fips)
    
    # Use simple ILIKE for search - let Postgres use the GIN index
    where_conditions.append("road_name ILIKE %s")
    params.append(f"%{search_term}%")
    
    # Build the query using materialized view
    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
    
    query = f"""
        WITH ranked_roads AS (
            SELECT DISTINCT ON (road_name, city_name, state_code)
                osm_id,
                road_name,
                highway,
                ref,
                city_name,
                state_code,
                county_fips,
                -- Simple scoring based on match quality
                CASE 
                    WHEN road_name = %s THEN 1
                    WHEN LOWER(road_name) = LOWER(%s) THEN 2
                    WHEN road_name ILIKE %s THEN 3
                    ELSE 4
                END as match_score
            FROM city_roads_simple
            WHERE {where_clause}
            ORDER BY road_name, city_name, state_code
        )
        SELECT 
            osm_id,
            road_name as name,
            highway,
            ref,
            city_name,
            state_code,
            county_fips,
            match_score
        FROM ranked_roads
        ORDER BY match_score, road_name
        LIMIT %s
    """
    
    # Add scoring params at the beginning
    params = [search_term, search_term, f"{search_term}%"] + params + [limit]
    
    return query, params

def search_roads_enhanced(conn, search_term: str, state_code: Optional[str] = None,
                         county_fips: Optional[str] = None, limit: int = 50) -> List[Dict]:
    """
    Optimized road search using materialized view
    """
    from ..database.postgres_client import execute_query
    
    query, params = build_search_query_optimized(search_term, state_code, county_fips, limit)
    
    results = execute_query(query, params)
    
    # Format results to match frontend expectations
    formatted_results = []
    for row in results:
        formatted_results.append({
            'osm_id': row['osm_id'],
            'name': row['name'],
            'highway': row['highway'],
            'ref': row.get('ref'),
            'city_name': row.get('city_name', ''),
            'state_code': row['state_code'],
            'county_fips': row.get('county_fips', ''),
            'county_name': '',  # Not in view, but frontend might expect it
            'state_name': row['state_code'],  # Use state code as fallback
            'segment_count': 1,  # Default
            'total_length_km': 0  # Default
        })
    
    return formatted_results