#!/usr/bin/env python3
"""
Test business analyzer with the new scoring system
"""
import sys
sys.path.append('/Users/luvu/Data_US_100k_pop/google_maps_crawler')

from app.database.postgres_client import PostgresClient
from app.crawler.business_analyzer import BusinessAnalyzer
import json

def test_locations():
    """Test various location types"""
    
    # Initialize
    db = PostgresClient()
    analyzer = BusinessAnalyzer(db)
    
    # Test locations
    test_cases = [
        ("Downtown LA", 34.0522, -118.2437),
        ("Suburban Pasadena", 34.1478, -118.1445),
        ("Rural Mojave", 34.8526, -117.0870),
        ("Santa Monica Beach", 34.0195, -118.4912),
        ("Beverly Hills", 34.0736, -118.4004)
    ]
    
    print("=" * 80)
    print("BUSINESS LOCATION ANALYSIS")
    print("=" * 80)
    
    for name, lat, lon in test_cases:
        print(f"\n{name} ({lat}, {lon})")
        print("-" * 40)
        
        # Get full analysis
        analysis = analyzer.analyze_location(lat, lon)
        
        # Display results
        print(f"Score: {analysis['score']}/100 ({analysis['rating']})")
        print(f"Recommendation: {analysis['recommendation']}")
        
        # Business insights
        insights = analysis['business_insights']
        print(f"\nBest for: {', '.join(insights['best_for'])}")
        if insights['challenges']:
            print(f"Challenges: {', '.join(insights['challenges'])}")
        
        # Score breakdown
        breakdown = analysis['score_breakdown']
        print(f"\nScore breakdown:")
        print(f"  - Density: {breakdown['density_score']}/30")
        print(f"  - Accessibility: {breakdown['accessibility_score']}/30")
        print(f"  - Road Quality: {breakdown['road_quality_score']}/20")
        print(f"  - Area Type: {breakdown['area_type_score']}/20")
        print(f"  - Traffic Flow: {breakdown['traffic_score']}/10")
        
        # Key metrics
        if 'area_analysis' in analysis:
            metrics = analysis['area_analysis']
            print(f"\nKey metrics:")
            print(f"  - Road density: {metrics['basic_metrics']['road_density_per_sqkm']} roads/km²")
            print(f"  - Nearest major road: {metrics['accessibility']['nearest_major_road_m']}m")
            print(f"  - Average lanes: {metrics['road_quality']['avg_lanes']}")
            print(f"  - Residential %: {metrics['road_composition']['residential_pct']}%")
        
        # Should crawl?
        should_crawl = analyzer.should_crawl_location(lat, lon, min_score=35)
        print(f"\nShould crawl this location? {'YES' if should_crawl else 'NO'}")
        
        # Get area classification
        classification = analyzer.get_area_classification(lat, lon)
        print(f"Area type: {classification['area_type']}")
        print(f"Business suitability: {classification['business_suitability']}")
        
        # Recommended search radius
        radius = analyzer.get_recommended_search_radius(classification['area_type'])
        print(f"Recommended search radius: {radius}m")
        
    print("\n" + "=" * 80)
    
    # Close connection
    db.close()

if __name__ == "__main__":
    test_locations()