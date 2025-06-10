#!/usr/bin/env python3
"""
Analyze business distribution to determine optimal Business Potential scoring formula
Using OSM business data for Alabama and California
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
    
    # First, let's understand what data we have
    print("\n1. DATA AVAILABILITY CHECK")
    query = """
        SELECT 
            state_code,
            COUNT(*) as business_count,
            COUNT(DISTINCT city) as city_count,
            COUNT(DISTINCT business_type) as business_type_count
        FROM osm_businesses
        WHERE state_code IN ('AL', 'CA')
        GROUP BY state_code
        ORDER BY state_code;
    """
    results = execute_query(query)
    for row in results:
        print(f"{row['state_code']}: {row['business_count']:,} businesses in {row['city_count']:,} cities, {row['business_type_count']} business types")
    
    # 2. Business distribution by road
    print("\n2. BUSINESS DISTRIBUTION BY ROAD")
    print("\nNote: Using 50-meter buffer to associate businesses with nearby roads")
    
    query = """
        WITH road_business_counts AS (
            SELECT 
                r.state_code,
                r.osm_id,
                r.name,
                r.highway,
                COUNT(DISTINCT b.osm_id) as business_count
            FROM osm_roads_main r
            LEFT JOIN osm_businesses b 
                ON r.state_code = b.state_code 
                AND ST_DWithin(r.geometry, b.geometry, 50)  -- 50 meter buffer
            WHERE r.state_code IN ('AL', 'CA')
                AND r.name IS NOT NULL
            GROUP BY r.state_code, r.osm_id, r.name, r.highway
        )
        SELECT 
            state_code,
            COUNT(*) as total_roads,
            SUM(CASE WHEN business_count = 0 THEN 1 ELSE 0 END) as roads_with_0_businesses,
            SUM(CASE WHEN business_count BETWEEN 1 AND 5 THEN 1 ELSE 0 END) as roads_with_1_5_businesses,
            SUM(CASE WHEN business_count BETWEEN 6 AND 10 THEN 1 ELSE 0 END) as roads_with_6_10_businesses,
            SUM(CASE WHEN business_count BETWEEN 11 AND 20 THEN 1 ELSE 0 END) as roads_with_11_20_businesses,
            SUM(CASE WHEN business_count > 20 THEN 1 ELSE 0 END) as roads_with_20plus_businesses,
            MAX(business_count) as max_businesses_on_road,
            ROUND(AVG(business_count), 2) as avg_businesses_per_road,
            ROUND(STDDEV(business_count), 2) as stddev_businesses
        FROM road_business_counts
        GROUP BY state_code
        ORDER BY state_code;
    """
    results = execute_query(query)
    for row in results:
        print(f"\n{row['state_code']} Distribution:")
        print(f"  Total roads with names: {row['total_roads']:,}")
        print(f"  Roads with 0 businesses: {row['roads_with_0_businesses']:,} ({row['roads_with_0_businesses']/row['total_roads']*100:.1f}%)")
        print(f"  Roads with 1-5 businesses: {row['roads_with_1_5_businesses']:,} ({row['roads_with_1_5_businesses']/row['total_roads']*100:.1f}%)")
        print(f"  Roads with 6-10 businesses: {row['roads_with_6_10_businesses']:,} ({row['roads_with_6_10_businesses']/row['total_roads']*100:.1f}%)")
        print(f"  Roads with 11-20 businesses: {row['roads_with_11_20_businesses']:,} ({row['roads_with_11_20_businesses']/row['total_roads']*100:.1f}%)")
        print(f"  Roads with 20+ businesses: {row['roads_with_20plus_businesses']:,} ({row['roads_with_20plus_businesses']/row['total_roads']*100:.1f}%)")
        print(f"  Max businesses on a single road: {row['max_businesses_on_road']}")
        print(f"  Average businesses per road: {row['avg_businesses_per_road']}")
        print(f"  Standard deviation: {row['stddev_businesses']}")
    
    # 3. Percentile analysis
    print("\n3. PERCENTILE ANALYSIS OF BUSINESS COUNTS")
    query = """
        WITH road_business_counts AS (
            SELECT 
                r.state_code,
                r.osm_id,
                COUNT(DISTINCT b.osm_id) as business_count
            FROM osm_roads_main r
            LEFT JOIN osm_businesses b 
                ON r.state_code = b.state_code 
                AND ST_DWithin(r.geometry, b.geometry, 50)
            WHERE r.state_code IN ('AL', 'CA')
                AND r.name IS NOT NULL
            GROUP BY r.state_code, r.osm_id
        )
        SELECT 
            state_code,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY business_count) as p50_median,
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
        print(f"  50th percentile (median): {row['p50_median']:.0f} businesses")
        print(f"  75th percentile: {row['p75']:.0f} businesses")
        print(f"  90th percentile: {row['p90']:.0f} businesses")
        print(f"  95th percentile: {row['p95']:.0f} businesses")
        print(f"  99th percentile: {row['p99']:.0f} businesses")
    
    # 4. Business distribution by highway type
    print("\n4. BUSINESS DISTRIBUTION BY HIGHWAY TYPE")
    query = """
        WITH road_business_counts AS (
            SELECT 
                r.state_code,
                r.highway,
                r.osm_id,
                COUNT(DISTINCT b.osm_id) as business_count
            FROM osm_roads_main r
            LEFT JOIN osm_businesses b 
                ON r.state_code = b.state_code 
                AND ST_DWithin(r.geometry, b.geometry, 50)
            WHERE r.state_code IN ('AL', 'CA')
                AND r.name IS NOT NULL
            GROUP BY r.state_code, r.highway, r.osm_id
        )
        SELECT 
            state_code,
            highway,
            COUNT(*) as road_count,
            ROUND(AVG(business_count), 2) as avg_businesses,
            MAX(business_count) as max_businesses,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY business_count) as median_businesses,
            PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY business_count) as p90_businesses
        FROM road_business_counts
        GROUP BY state_code, highway
        HAVING COUNT(*) > 50  -- Only show highway types with more than 50 roads
        ORDER BY state_code, avg_businesses DESC;
    """
    results = execute_query(query)
    
    current_state = None
    for row in results:
        if current_state != row['state_code']:
            print(f"\n{row['state_code']} - Businesses by Highway Type:")
            print(f"{'Highway Type':<20} {'Roads':<10} {'Avg Biz':<10} {'Median':<10} {'90th %ile':<10} {'Max Biz':<10}")
            print("-" * 70)
            current_state = row['state_code']
        
        print(f"{row['highway']:<20} {row['road_count']:<10} {row['avg_businesses']:<10} {row['median_businesses']:<10.0f} {row['p90_businesses']:<10.0f} {row['max_businesses']:<10}")
    
    # 5. Analyze current scoring formula effectiveness
    print("\n5. CURRENT SCORING FORMULA ANALYSIS")
    print("\nCurrent formula:")
    print("  20+ businesses: Score 10")
    print("  10-19 businesses: Score 8")
    print("  <10 businesses: Count * 0.5")
    
    query = """
        WITH road_scores AS (
            SELECT 
                r.state_code,
                r.osm_id,
                COUNT(DISTINCT b.osm_id) as business_count,
                CASE 
                    WHEN COUNT(DISTINCT b.osm_id) >= 20 THEN 10
                    WHEN COUNT(DISTINCT b.osm_id) >= 10 THEN 8
                    ELSE COUNT(DISTINCT b.osm_id) * 0.5
                END as current_score
            FROM osm_roads_main r
            LEFT JOIN osm_businesses b 
                ON r.state_code = b.state_code 
                AND ST_DWithin(r.geometry, b.geometry, 50)
            WHERE r.state_code IN ('AL', 'CA')
                AND r.name IS NOT NULL
            GROUP BY r.state_code, r.osm_id
        )
        SELECT 
            state_code,
            COUNT(*) as total_roads,
            SUM(CASE WHEN current_score = 10 THEN 1 ELSE 0 END) as score_10_roads,
            SUM(CASE WHEN current_score = 8 THEN 1 ELSE 0 END) as score_8_roads,
            SUM(CASE WHEN current_score < 8 THEN 1 ELSE 0 END) as score_low_roads,
            ROUND(AVG(current_score), 2) as avg_score,
            ROUND(AVG(CASE WHEN business_count > 0 THEN current_score END), 2) as avg_score_with_businesses
        FROM road_scores
        GROUP BY state_code
        ORDER BY state_code;
    """
    results = execute_query(query)
    for row in results:
        print(f"\n{row['state_code']} Current Scoring Distribution:")
        print(f"  Roads with score 10: {row['score_10_roads']:,} ({row['score_10_roads']/row['total_roads']*100:.1f}%)")
        print(f"  Roads with score 8: {row['score_8_roads']:,} ({row['score_8_roads']/row['total_roads']*100:.1f}%)")
        print(f"  Roads with score <8: {row['score_low_roads']:,} ({row['score_low_roads']/row['total_roads']*100:.1f}%)")
        print(f"  Average score (all roads): {row['avg_score']}")
        if row['avg_score_with_businesses']:
            print(f"  Average score (roads with businesses): {row['avg_score_with_businesses']}")
    
    # 6. Recommendation based on analysis
    print("\n6. SCORING FORMULA RECOMMENDATIONS")
    print("\nBased on the percentile analysis:")
    
    # Get the percentile values for the recommendation
    query = """
        WITH road_business_counts AS (
            SELECT 
                r.state_code,
                COUNT(DISTINCT b.osm_id) as business_count
            FROM osm_roads_main r
            LEFT JOIN osm_businesses b 
                ON r.state_code = b.state_code 
                AND ST_DWithin(r.geometry, b.geometry, 50)
            WHERE r.state_code IN ('AL', 'CA')
                AND r.name IS NOT NULL
            GROUP BY r.state_code, r.osm_id
        ),
        percentiles AS (
            SELECT 
                state_code,
                PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY business_count) as p50,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY business_count) as p75,
                PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY business_count) as p90,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY business_count) as p95
            FROM road_business_counts
            GROUP BY state_code
        )
        SELECT * FROM percentiles
        ORDER BY state_code;
    """
    results = execute_query(query)
    
    print("\nRecommended scoring thresholds:")
    
    # Calculate average thresholds
    p95_vals = []
    p90_vals = []
    p75_vals = []
    p50_vals = []
    
    for row in results:
        p95_vals.append(row['p95'])
        p90_vals.append(row['p90'])
        p75_vals.append(row['p75'])
        p50_vals.append(row['p50'])
        
        print(f"\n{row['state_code']} Specific Thresholds:")
        print(f"  Score 10: {row['p95']:.0f}+ businesses (top 5%)")
        print(f"  Score 9: {row['p90']:.0f}-{row['p95']-1:.0f} businesses (top 5-10%)")
        print(f"  Score 8: {row['p75']:.0f}-{row['p90']-1:.0f} businesses (top 10-25%)")
        print(f"  Score 6-7: {row['p50']:.0f}-{row['p75']-1:.0f} businesses (top 25-50%)")
        print(f"  Score 0-5: 0-{row['p50']-1:.0f} businesses (bottom 50%, scaled)")
    
    # Provide a universal formula recommendation
    avg_p95 = np.mean(p95_vals)
    avg_p90 = np.mean(p90_vals)
    avg_p75 = np.mean(p75_vals)
    avg_p50 = np.mean(p50_vals)
    
    print("\n\nRECOMMENDED UNIVERSAL FORMULA:")
    print("```sql")
    print("CASE")
    print(f"    WHEN business_count >= {avg_p95:.0f} THEN 10  -- Top 5% (exceptional)")
    print(f"    WHEN business_count >= {avg_p90:.0f} THEN 9   -- Top 10% (excellent)")
    print(f"    WHEN business_count >= {avg_p75:.0f} THEN 8   -- Top 25% (very good)")
    print(f"    WHEN business_count >= {avg_p50:.0f} THEN 6 + (business_count - {avg_p50:.0f}) * 2.0 / ({avg_p75:.0f} - {avg_p50:.0f})  -- Scaled 6-8")
    print(f"    WHEN business_count > 0 THEN business_count * 6.0 / {avg_p50:.0f}  -- Scaled 0-6")
    print("    ELSE 0")
    print("END AS business_potential_score")
    print("```")
    
    print("\nAlternative simplified formula:")
    print("```sql")
    print("CASE")
    print(f"    WHEN business_count >= 15 THEN 10")
    print(f"    WHEN business_count >= 10 THEN 9")
    print(f"    WHEN business_count >= 5 THEN 8")
    print(f"    WHEN business_count >= 3 THEN 7")
    print(f"    WHEN business_count >= 1 THEN 5 + business_count")
    print("    ELSE 0")
    print("END AS business_potential_score")
    print("```")

if __name__ == "__main__":
    analyze_business_distribution()