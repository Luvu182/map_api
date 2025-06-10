#!/usr/bin/env python3
"""
Analyze POI distribution in Alabama and California to determine optimal Business Potential scoring formula
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import execute_query
import pandas as pd
import numpy as np

def analyze_poi_distribution():
    """Analyze POI distribution for AL and CA"""
    
    print("POI Distribution Analysis for Alabama (AL) and California (CA)")
    print("=" * 80)
    
    # 1. Overall POI counts by state
    print("\n1. OVERALL POI COUNTS BY STATE")
    query = """
        SELECT 
            state_code,
            COUNT(DISTINCT osm_id) as total_roads,
            COUNT(DISTINCT poi_osm_id) as total_pois,
            ROUND(COUNT(DISTINCT poi_osm_id)::numeric / NULLIF(COUNT(DISTINCT osm_id), 0), 2) as avg_pois_per_road
        FROM osm_roads_main r
        LEFT JOIN osm_business_pois p ON ST_DWithin(r.geometry, p.geometry, 50)
        WHERE state_code IN ('AL', 'CA')
        GROUP BY state_code
        ORDER BY state_code;
    """
    results = execute_query(query)
    for row in results:
        print(f"{row['state_code']}: {row['total_roads']:,} roads, {row['total_pois']:,} POIs, {row['avg_pois_per_road']} avg POIs/road")
    
    # 2. Distribution of POI counts per road
    print("\n2. DISTRIBUTION OF POI COUNTS PER ROAD")
    query = """
        WITH road_poi_counts AS (
            SELECT 
                r.state_code,
                r.osm_id,
                r.name,
                r.highway,
                COUNT(DISTINCT p.osm_id) as poi_count
            FROM osm_roads_main r
            LEFT JOIN osm_business_pois p ON ST_DWithin(r.geometry, p.geometry, 50)
            WHERE r.state_code IN ('AL', 'CA')
            GROUP BY r.state_code, r.osm_id, r.name, r.highway
        )
        SELECT 
            state_code,
            COUNT(*) as total_roads,
            SUM(CASE WHEN poi_count = 0 THEN 1 ELSE 0 END) as roads_with_0_pois,
            SUM(CASE WHEN poi_count BETWEEN 1 AND 5 THEN 1 ELSE 0 END) as roads_with_1_5_pois,
            SUM(CASE WHEN poi_count BETWEEN 6 AND 10 THEN 1 ELSE 0 END) as roads_with_6_10_pois,
            SUM(CASE WHEN poi_count BETWEEN 11 AND 20 THEN 1 ELSE 0 END) as roads_with_11_20_pois,
            SUM(CASE WHEN poi_count > 20 THEN 1 ELSE 0 END) as roads_with_20plus_pois,
            MAX(poi_count) as max_pois_on_road,
            ROUND(AVG(poi_count), 2) as avg_pois_per_road,
            ROUND(STDDEV(poi_count), 2) as stddev_pois
        FROM road_poi_counts
        GROUP BY state_code
        ORDER BY state_code;
    """
    results = execute_query(query)
    for row in results:
        print(f"\n{row['state_code']} Distribution:")
        print(f"  Total roads: {row['total_roads']:,}")
        print(f"  Roads with 0 POIs: {row['roads_with_0_pois']:,} ({row['roads_with_0_pois']/row['total_roads']*100:.1f}%)")
        print(f"  Roads with 1-5 POIs: {row['roads_with_1_5_pois']:,} ({row['roads_with_1_5_pois']/row['total_roads']*100:.1f}%)")
        print(f"  Roads with 6-10 POIs: {row['roads_with_6_10_pois']:,} ({row['roads_with_6_10_pois']/row['total_roads']*100:.1f}%)")
        print(f"  Roads with 11-20 POIs: {row['roads_with_11_20_pois']:,} ({row['roads_with_11_20_pois']/row['total_roads']*100:.1f}%)")
        print(f"  Roads with 20+ POIs: {row['roads_with_20plus_pois']:,} ({row['roads_with_20plus_pois']/row['total_roads']*100:.1f}%)")
        print(f"  Max POIs on a single road: {row['max_pois_on_road']}")
        print(f"  Average POIs per road: {row['avg_pois_per_road']}")
        print(f"  Standard deviation: {row['stddev_pois']}")
    
    # 3. Percentile analysis
    print("\n3. PERCENTILE ANALYSIS OF POI COUNTS")
    query = """
        WITH road_poi_counts AS (
            SELECT 
                r.state_code,
                r.osm_id,
                COUNT(DISTINCT p.osm_id) as poi_count
            FROM osm_roads_main r
            LEFT JOIN osm_business_pois p ON ST_DWithin(r.geometry, p.geometry, 50)
            WHERE r.state_code IN ('AL', 'CA')
            GROUP BY r.state_code, r.osm_id
        )
        SELECT 
            state_code,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY poi_count) as p50_median,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY poi_count) as p75,
            PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY poi_count) as p90,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY poi_count) as p95,
            PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY poi_count) as p99
        FROM road_poi_counts
        GROUP BY state_code
        ORDER BY state_code;
    """
    results = execute_query(query)
    for row in results:
        print(f"\n{row['state_code']} Percentiles:")
        print(f"  50th percentile (median): {row['p50_median']:.0f} POIs")
        print(f"  75th percentile: {row['p75']:.0f} POIs")
        print(f"  90th percentile: {row['p90']:.0f} POIs")
        print(f"  95th percentile: {row['p95']:.0f} POIs")
        print(f"  99th percentile: {row['p99']:.0f} POIs")
    
    # 4. POI distribution by highway type
    print("\n4. POI DISTRIBUTION BY HIGHWAY TYPE")
    query = """
        WITH road_poi_counts AS (
            SELECT 
                r.state_code,
                r.highway,
                r.osm_id,
                COUNT(DISTINCT p.osm_id) as poi_count
            FROM osm_roads_main r
            LEFT JOIN osm_business_pois p ON ST_DWithin(r.geometry, p.geometry, 50)
            WHERE r.state_code IN ('AL', 'CA')
            GROUP BY r.state_code, r.highway, r.osm_id
        )
        SELECT 
            state_code,
            highway,
            COUNT(*) as road_count,
            ROUND(AVG(poi_count), 2) as avg_pois,
            MAX(poi_count) as max_pois,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY poi_count) as median_pois,
            PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY poi_count) as p90_pois
        FROM road_poi_counts
        GROUP BY state_code, highway
        HAVING COUNT(*) > 10  -- Only show highway types with more than 10 roads
        ORDER BY state_code, avg_pois DESC;
    """
    results = execute_query(query)
    
    current_state = None
    for row in results:
        if current_state != row['state_code']:
            print(f"\n{row['state_code']} - POIs by Highway Type:")
            print(f"{'Highway Type':<20} {'Roads':<10} {'Avg POIs':<10} {'Median':<10} {'90th %ile':<10} {'Max POIs':<10}")
            print("-" * 70)
            current_state = row['state_code']
        
        print(f"{row['highway']:<20} {row['road_count']:<10} {row['avg_pois']:<10} {row['median_pois']:<10.0f} {row['p90_pois']:<10.0f} {row['max_pois']:<10}")
    
    # 5. Analyze current scoring formula effectiveness
    print("\n5. CURRENT SCORING FORMULA ANALYSIS")
    print("\nCurrent formula:")
    print("  20+ POIs: Score 10")
    print("  10-19 POIs: Score 8")
    print("  <10 POIs: Count * 0.5")
    
    query = """
        WITH road_scores AS (
            SELECT 
                r.state_code,
                r.osm_id,
                COUNT(DISTINCT p.osm_id) as poi_count,
                CASE 
                    WHEN COUNT(DISTINCT p.osm_id) >= 20 THEN 10
                    WHEN COUNT(DISTINCT p.osm_id) >= 10 THEN 8
                    ELSE COUNT(DISTINCT p.osm_id) * 0.5
                END as current_score
            FROM osm_roads_main r
            LEFT JOIN osm_business_pois p ON ST_DWithin(r.geometry, p.geometry, 50)
            WHERE r.state_code IN ('AL', 'CA')
            GROUP BY r.state_code, r.osm_id
        )
        SELECT 
            state_code,
            COUNT(*) as total_roads,
            SUM(CASE WHEN current_score = 10 THEN 1 ELSE 0 END) as score_10_roads,
            SUM(CASE WHEN current_score = 8 THEN 1 ELSE 0 END) as score_8_roads,
            SUM(CASE WHEN current_score < 8 THEN 1 ELSE 0 END) as score_low_roads,
            ROUND(AVG(current_score), 2) as avg_score,
            ROUND(AVG(CASE WHEN poi_count > 0 THEN current_score END), 2) as avg_score_with_pois
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
        print(f"  Average score (roads with POIs): {row['avg_score_with_pois']}")
    
    # 6. Proposed formula analysis based on percentiles
    print("\n6. RECOMMENDED SCORING FORMULA")
    print("\nBased on the percentile analysis, here's a recommended formula:")
    print("  95th percentile and above (exceptional): Score 10")
    print("  90th-95th percentile (excellent): Score 9")
    print("  75th-90th percentile (very good): Score 8")
    print("  50th-75th percentile (good): Score 6-7")
    print("  Below 50th percentile: Scaled 0-5")
    
    # Get the actual percentile values for recommendations
    query = """
        WITH road_poi_counts AS (
            SELECT 
                r.state_code,
                COUNT(DISTINCT p.osm_id) as poi_count
            FROM osm_roads_main r
            LEFT JOIN osm_business_pois p ON ST_DWithin(r.geometry, p.geometry, 50)
            WHERE r.state_code IN ('AL', 'CA')
            GROUP BY r.state_code, r.osm_id
        ),
        percentiles AS (
            SELECT 
                state_code,
                PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY poi_count) as p50,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY poi_count) as p75,
                PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY poi_count) as p90,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY poi_count) as p95
            FROM road_poi_counts
            GROUP BY state_code
        )
        SELECT * FROM percentiles
        ORDER BY state_code;
    """
    results = execute_query(query)
    
    print("\nRecommended thresholds by state:")
    for row in results:
        print(f"\n{row['state_code']} Thresholds:")
        print(f"  Score 10: {row['p95']:.0f}+ POIs (top 5%)")
        print(f"  Score 9: {row['p90']:.0f}-{row['p95']:.0f} POIs (top 5-10%)")
        print(f"  Score 8: {row['p75']:.0f}-{row['p90']:.0f} POIs (top 10-25%)")
        print(f"  Score 6-7: {row['p50']:.0f}-{row['p75']:.0f} POIs (top 25-50%)")
        print(f"  Score 0-5: 0-{row['p50']:.0f} POIs (bottom 50%, scaled)")

if __name__ == "__main__":
    analyze_poi_distribution()