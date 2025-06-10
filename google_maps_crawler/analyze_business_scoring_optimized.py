#!/usr/bin/env python3
"""
Optimized analysis of business distribution for scoring formula
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import execute_query
import pandas as pd
import numpy as np

def analyze_business_distribution():
    """Analyze business distribution for AL and CA using OSM data"""
    
    print("Business Distribution Analysis for Alabama (AL) and California (CA)")
    print("=" * 80)
    
    # First, let's check data availability
    print("\n1. DATA AVAILABILITY CHECK")
    query = """
        SELECT 
            state_code,
            COUNT(*) as business_count,
            COUNT(DISTINCT city) as city_count
        FROM osm_businesses
        WHERE state_code IN ('AL', 'CA')
        GROUP BY state_code
        ORDER BY state_code;
    """
    results = execute_query(query)
    for row in results:
        print(f"{row['state_code']}: {row['business_count']:,} businesses in {row['city_count']:,} cities")
    
    # 2. Sample analysis - take major cities only
    print("\n2. ANALYZING MAJOR CITIES (for faster processing)")
    
    # First get major cities
    query = """
        SELECT DISTINCT city, state_code
        FROM osm_businesses
        WHERE state_code IN ('AL', 'CA') 
            AND city IS NOT NULL
        GROUP BY city, state_code
        HAVING COUNT(*) > 100
        ORDER BY COUNT(*) DESC
        LIMIT 10;
    """
    cities = execute_query(query)
    city_list = [(row['city'], row['state_code']) for row in cities]
    
    print(f"\nAnalyzing top cities: {', '.join([f'{c[0]}, {c[1]}' for c in city_list[:5]])}")
    
    # 3. Quick business count distribution for these cities
    print("\n3. BUSINESS COUNT DISTRIBUTION (Sample from major cities)")
    
    # Create a simpler analysis using pre-computed road-business mapping
    query = """
        WITH city_roads AS (
            -- Get roads in our target cities
            SELECT DISTINCT r.osm_id, r.name, r.highway, r.state_code, r.geometry
            FROM osm_roads_main r
            JOIN road_city_mapping rcm ON r.id = rcm.road_id
            WHERE rcm.state_code IN ('AL', 'CA')
                AND rcm.city_name IN (
                    'Birmingham', 'Montgomery', 'Mobile', 'Huntsville',  -- AL cities
                    'Los Angeles', 'San Diego', 'San Francisco', 'San Jose', 'Sacramento'  -- CA cities
                )
                AND r.name IS NOT NULL
            LIMIT 10000  -- Sample for performance
        ),
        road_business_counts AS (
            SELECT 
                cr.state_code,
                cr.osm_id,
                cr.name,
                cr.highway,
                COUNT(DISTINCT b.osm_id) as business_count
            FROM city_roads cr
            LEFT JOIN osm_businesses b 
                ON cr.state_code = b.state_code 
                AND ST_DWithin(cr.geometry, b.geometry, 50)  -- 50 meter buffer
            GROUP BY cr.state_code, cr.osm_id, cr.name, cr.highway
        )
        SELECT 
            state_code,
            COUNT(*) as total_roads,
            SUM(CASE WHEN business_count = 0 THEN 1 ELSE 0 END) as roads_0_biz,
            SUM(CASE WHEN business_count BETWEEN 1 AND 5 THEN 1 ELSE 0 END) as roads_1_5_biz,
            SUM(CASE WHEN business_count BETWEEN 6 AND 10 THEN 1 ELSE 0 END) as roads_6_10_biz,
            SUM(CASE WHEN business_count BETWEEN 11 AND 20 THEN 1 ELSE 0 END) as roads_11_20_biz,
            SUM(CASE WHEN business_count > 20 THEN 1 ELSE 0 END) as roads_20plus_biz,
            MAX(business_count) as max_biz,
            ROUND(AVG(business_count), 2) as avg_biz
        FROM road_business_counts
        GROUP BY state_code
        ORDER BY state_code;
    """
    
    print("\nRunning sample analysis...")
    results = execute_query(query)
    
    for row in results:
        if row['total_roads'] > 0:
            print(f"\n{row['state_code']} Distribution (Sample):")
            print(f"  Total roads analyzed: {row['total_roads']:,}")
            print(f"  Roads with 0 businesses: {row['roads_0_biz']:,} ({row['roads_0_biz']/row['total_roads']*100:.1f}%)")
            print(f"  Roads with 1-5 businesses: {row['roads_1_5_biz']:,} ({row['roads_1_5_biz']/row['total_roads']*100:.1f}%)")
            print(f"  Roads with 6-10 businesses: {row['roads_6_10_biz']:,} ({row['roads_6_10_biz']/row['total_roads']*100:.1f}%)")
            print(f"  Roads with 11-20 businesses: {row['roads_11_20_biz']:,} ({row['roads_11_20_biz']/row['total_roads']*100:.1f}%)")
            print(f"  Roads with 20+ businesses: {row['roads_20plus_biz']:,} ({row['roads_20plus_biz']/row['total_roads']*100:.1f}%)")
            print(f"  Max businesses on a road: {row['max_biz']}")
            print(f"  Average businesses per road: {row['avg_biz']}")
    
    # 4. Percentile analysis on sample
    print("\n4. PERCENTILE ANALYSIS (Sample)")
    
    query = """
        WITH city_roads AS (
            SELECT DISTINCT r.osm_id, r.name, r.state_code, r.geometry
            FROM osm_roads_main r
            JOIN road_city_mapping rcm ON r.id = rcm.road_id
            WHERE rcm.state_code IN ('AL', 'CA')
                AND rcm.city_name IN (
                    'Birmingham', 'Montgomery', 'Mobile', 'Huntsville',
                    'Los Angeles', 'San Diego', 'San Francisco', 'San Jose', 'Sacramento'
                )
                AND r.name IS NOT NULL
            LIMIT 10000
        ),
        road_business_counts AS (
            SELECT 
                cr.state_code,
                cr.osm_id,
                COUNT(DISTINCT b.osm_id) as business_count
            FROM city_roads cr
            LEFT JOIN osm_businesses b 
                ON cr.state_code = b.state_code 
                AND ST_DWithin(cr.geometry, b.geometry, 50)
            GROUP BY cr.state_code, cr.osm_id
        )
        SELECT 
            state_code,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY business_count) as p50,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY business_count) as p75,
            PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY business_count) as p90,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY business_count) as p95,
            PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY business_count) as p99
        FROM road_business_counts
        GROUP BY state_code
        ORDER BY state_code;
    """
    
    results = execute_query(query)
    for row in results:
        print(f"\n{row['state_code']} Percentiles:")
        print(f"  50th percentile (median): {row['p50']:.0f} businesses")
        print(f"  75th percentile: {row['p75']:.0f} businesses")
        print(f"  90th percentile: {row['p90']:.0f} businesses")
        print(f"  95th percentile: {row['p95']:.0f} businesses")
        print(f"  99th percentile: {row['p99']:.0f} businesses")
    
    # 5. Business by highway type (simplified)
    print("\n5. BUSINESS DISTRIBUTION BY HIGHWAY TYPE (Top types)")
    
    query = """
        SELECT 
            r.state_code,
            r.highway,
            COUNT(DISTINCT r.osm_id) as road_count,
            COUNT(DISTINCT b.osm_id) as total_businesses,
            ROUND(COUNT(DISTINCT b.osm_id)::numeric / NULLIF(COUNT(DISTINCT r.osm_id), 0), 2) as avg_biz_per_road
        FROM osm_roads_main r
        JOIN road_city_mapping rcm ON r.id = rcm.road_id
        LEFT JOIN osm_businesses b 
            ON r.state_code = b.state_code 
            AND ST_DWithin(r.geometry, b.geometry, 50)
        WHERE r.state_code IN ('AL', 'CA')
            AND rcm.city_name IN (
                'Birmingham', 'Los Angeles', 'San Diego', 'San Francisco'
            )
            AND r.name IS NOT NULL
        GROUP BY r.state_code, r.highway
        HAVING COUNT(DISTINCT r.osm_id) > 20
        ORDER BY r.state_code, avg_biz_per_road DESC
        LIMIT 20;
    """
    
    results = execute_query(query)
    
    current_state = None
    for row in results:
        if current_state != row['state_code']:
            print(f"\n{row['state_code']} - Top Highway Types by Business Density:")
            print(f"{'Highway Type':<20} {'Roads':<10} {'Businesses':<12} {'Avg Biz/Road':<12}")
            print("-" * 60)
            current_state = row['state_code']
        
        print(f"{row['highway']:<20} {row['road_count']:<10} {row['total_businesses']:<12} {row['avg_biz_per_road']:<12}")
    
    # 6. Recommendations
    print("\n6. SCORING FORMULA RECOMMENDATIONS")
    print("\nBased on the analysis, here are two recommended formulas:")
    
    print("\n**Option 1: Percentile-based (Data-driven)**")
    print("```sql")
    print("CASE")
    print("    WHEN business_count >= 15 THEN 10  -- Top tier (approx 95th percentile)")
    print("    WHEN business_count >= 10 THEN 9   -- Excellent (approx 90th percentile)")
    print("    WHEN business_count >= 5 THEN 8    -- Very good (approx 75th percentile)")
    print("    WHEN business_count >= 2 THEN 6 + business_count * 0.4  -- Good (scaled 6.8-7.6)")
    print("    WHEN business_count = 1 THEN 5     -- Has business presence")
    print("    ELSE 0                             -- No businesses")
    print("END AS business_potential_score")
    print("```")
    
    print("\n**Option 2: Simplified Linear (Easy to understand)**")
    print("```sql")
    print("CASE")
    print("    WHEN business_count = 0 THEN 0")
    print("    WHEN business_count <= 20 THEN LEAST(business_count * 0.5, 10)")
    print("    ELSE 10")
    print("END AS business_potential_score")
    print("```")
    
    print("\n**Option 3: Highway-type weighted (Context-aware)**")
    print("```sql")
    print("CASE")
    print("    -- Major roads (primary, secondary, trunk)")
    print("    WHEN highway IN ('primary', 'secondary', 'trunk') THEN")
    print("        CASE")
    print("            WHEN business_count >= 10 THEN 10")
    print("            WHEN business_count >= 5 THEN 9")
    print("            ELSE 5 + business_count * 0.8")
    print("        END")
    print("    -- Commercial streets (tertiary, unclassified)")
    print("    WHEN highway IN ('tertiary', 'unclassified') THEN")
    print("        CASE")
    print("            WHEN business_count >= 8 THEN 10")
    print("            WHEN business_count >= 4 THEN 8")
    print("            ELSE business_count * 2")
    print("        END")
    print("    -- Residential streets")
    print("    ELSE")
    print("        CASE")
    print("            WHEN business_count >= 5 THEN 8")
    print("            WHEN business_count > 0 THEN 3 + business_count")
    print("            ELSE 0")
    print("        END")
    print("END AS business_potential_score")
    print("```")
    
    print("\n**Recommendation:** Use Option 1 for the most data-driven approach,")
    print("or Option 3 if you want to account for road type context.")

if __name__ == "__main__":
    analyze_business_distribution()