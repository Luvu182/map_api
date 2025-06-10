#!/usr/bin/env python3
"""
Simple analysis of business distribution for scoring formula
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.database_config import execute_query

def analyze_business_distribution():
    """Analyze business distribution for AL and CA"""
    
    print("Business Distribution Analysis for Alabama (AL) and California (CA)")
    print("=" * 80)
    
    # 1. Check data availability
    print("\n1. DATA AVAILABILITY")
    query = """
        SELECT 
            state_code,
            COUNT(*) as business_count
        FROM osm_businesses
        WHERE state_code IN ('AL', 'CA')
        GROUP BY state_code
        ORDER BY state_code;
    """
    results = execute_query(query)
    for row in results:
        print(f"{row['state_code']}: {row['business_count']:,} businesses")
    
    # 2. Look at pre-computed road_poi_stats tables if available
    print("\n2. CHECKING PRE-COMPUTED STATISTICS")
    
    # Check road_poi_stats_al
    query = """
        SELECT 
            COUNT(*) as total_roads,
            SUM(poi_count) as total_pois,
            AVG(poi_count) as avg_pois,
            MAX(poi_count) as max_pois,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY poi_count) as median,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY poi_count) as p75,
            PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY poi_count) as p90,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY poi_count) as p95
        FROM road_poi_stats_al;
    """
    try:
        results = execute_query(query)
        if results and results[0]['total_roads'] > 0:
            row = results[0]
            print(f"\nAlabama Road Statistics (from road_poi_stats_al):")
            print(f"  Total roads: {row['total_roads']:,}")
            print(f"  Total POIs: {int(row['total_pois']) if row['total_pois'] else 0:,}")
            print(f"  Average POIs per road: {row['avg_pois']:.2f}")
            print(f"  Max POIs on a road: {row['max_pois']}")
            print(f"  Median: {row['median']:.0f}")
            print(f"  75th percentile: {row['p75']:.0f}")
            print(f"  90th percentile: {row['p90']:.0f}")
            print(f"  95th percentile: {row['p95']:.0f}")
    except:
        print("  No pre-computed AL statistics available")
    
    # 3. Sample analysis - just take 1000 roads from each state
    print("\n3. SAMPLE ANALYSIS (1000 roads per state)")
    
    for state in ['AL', 'CA']:
        query = f"""
            WITH sampled_roads AS (
                SELECT osm_id, name, highway, geometry
                FROM osm_roads_main
                WHERE state_code = '{state}' 
                    AND name IS NOT NULL
                ORDER BY RANDOM()
                LIMIT 1000
            ),
            road_business_counts AS (
                SELECT 
                    sr.osm_id,
                    sr.highway,
                    COUNT(DISTINCT b.osm_id) as business_count
                FROM sampled_roads sr
                LEFT JOIN osm_businesses b 
                    ON ST_DWithin(sr.geometry, b.geometry, 50)
                    AND b.state_code = '{state}'
                GROUP BY sr.osm_id, sr.highway
            )
            SELECT 
                COUNT(*) as total_roads,
                SUM(CASE WHEN business_count = 0 THEN 1 ELSE 0 END) as roads_0,
                SUM(CASE WHEN business_count BETWEEN 1 AND 5 THEN 1 ELSE 0 END) as roads_1_5,
                SUM(CASE WHEN business_count BETWEEN 6 AND 10 THEN 1 ELSE 0 END) as roads_6_10,
                SUM(CASE WHEN business_count > 10 THEN 1 ELSE 0 END) as roads_10plus,
                MAX(business_count) as max_biz,
                AVG(business_count) as avg_biz,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY business_count) as median,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY business_count) as p75,
                PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY business_count) as p90,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY business_count) as p95
            FROM road_business_counts;
        """
        
        print(f"\n{state} Sample Results (1000 random roads):")
        try:
            results = execute_query(query)
            if results:
                row = results[0]
                print(f"  Roads with 0 businesses: {row['roads_0']} ({row['roads_0']/10:.1f}%)")
                print(f"  Roads with 1-5 businesses: {row['roads_1_5']} ({row['roads_1_5']/10:.1f}%)")
                print(f"  Roads with 6-10 businesses: {row['roads_6_10']} ({row['roads_6_10']/10:.1f}%)")
                print(f"  Roads with 10+ businesses: {row['roads_10plus']} ({row['roads_10plus']/10:.1f}%)")
                print(f"  Max businesses: {row['max_biz']}")
                print(f"  Average: {row['avg_biz']:.2f}")
                print(f"  Median: {row['median']:.0f}")
                print(f"  75th percentile: {row['p75']:.0f}")
                print(f"  90th percentile: {row['p90']:.0f}")
                print(f"  95th percentile: {row['p95']:.0f}")
        except Exception as e:
            print(f"  Error: {e}")
    
    # 4. Current formula analysis
    print("\n4. CURRENT FORMULA vs. RECOMMENDED")
    
    print("\nCurrent Formula:")
    print("  20+ businesses: Score 10")
    print("  10-19 businesses: Score 8")
    print("  <10 businesses: Count * 0.5")
    
    print("\n\nRECOMMENDED FORMULAS:")
    
    print("\n**Option 1: Simple Linear Scale**")
    print("```sql")
    print("-- This gives a smooth 0-10 scale")
    print("CASE")
    print("    WHEN business_count = 0 THEN 0")
    print("    WHEN business_count >= 20 THEN 10")
    print("    ELSE business_count * 0.5")
    print("END AS business_potential_score")
    print("```")
    
    print("\n**Option 2: Stepped Scale (Based on typical distributions)**")
    print("```sql")
    print("-- Based on the analysis, most roads have 0-5 businesses")
    print("CASE")
    print("    WHEN business_count = 0 THEN 0")
    print("    WHEN business_count = 1 THEN 3    -- Has some business activity")
    print("    WHEN business_count = 2 THEN 5    -- Multiple businesses")
    print("    WHEN business_count <= 5 THEN 6   -- Good business density")
    print("    WHEN business_count <= 10 THEN 8  -- High business density")
    print("    ELSE 10                           -- Exceptional business density")
    print("END AS business_potential_score")
    print("```")
    
    print("\n**Option 3: Logarithmic Scale (Diminishing returns)**")
    print("```sql")
    print("-- Recognizes that the difference between 0 and 5 businesses")
    print("-- is more significant than between 15 and 20")
    print("CASE")
    print("    WHEN business_count = 0 THEN 0")
    print("    ELSE LEAST(10, 3 + LN(business_count + 1) * 2.5)")
    print("END AS business_potential_score")
    print("```")
    
    print("\n**RECOMMENDATION:** Use Option 2 for most intuitive scoring,")
    print("as it recognizes that even 1 business indicates commercial viability,")
    print("and the jump from 0 to 1 business is significant.")

if __name__ == "__main__":
    analyze_business_distribution()