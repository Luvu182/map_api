#!/usr/bin/env python3
"""
Query the 5 most recent crawl sessions from the database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from scripts.database_config import execute_query
from datetime import datetime

def get_recent_crawl_sessions():
    """Fetch the 5 most recent crawl sessions"""
    query = """
        SELECT 
            id,
            road_name,
            status,
            businesses_found,
            city_name,
            state_code,
            keyword,
            started_at,
            completed_at,
            error_message
        FROM crawl_sessions
        ORDER BY started_at DESC
        LIMIT 5
    """
    
    try:
        results = execute_query(query)
        
        if not results:
            print("No crawl sessions found in the database.")
            return
        
        print(f"\n{'='*120}")
        print("5 MOST RECENT CRAWL SESSIONS")
        print(f"{'='*120}\n")
        
        for i, session in enumerate(results, 1):
            print(f"Session {i}:")
            print(f"  ID: {session['id']}")
            print(f"  Road Name: {session['road_name'] or 'N/A'}")
            print(f"  Status: {session['status']}")
            print(f"  Businesses Found: {session['businesses_found']}")
            print(f"  Location: {session['city_name'] or 'N/A'}, {session['state_code'] or 'N/A'}")
            print(f"  Keyword: {session['keyword'] or 'N/A'}")
            print(f"  Started: {session['started_at']}")
            print(f"  Completed: {session['completed_at'] or 'Not completed'}")
            if session['error_message']:
                print(f"  Error: {session['error_message']}")
            print(f"{'-'*80}")
        
        # Also show a summary
        print(f"\n{'='*120}")
        print("SUMMARY STATISTICS")
        print(f"{'='*120}\n")
        
        summary_query = """
            SELECT 
                status,
                COUNT(*) as count,
                SUM(businesses_found) as total_businesses
            FROM crawl_sessions
            GROUP BY status
            ORDER BY count DESC
        """
        
        summary_results = execute_query(summary_query)
        
        total_sessions = sum(row['count'] for row in summary_results)
        total_businesses = sum(row['total_businesses'] or 0 for row in summary_results)
        
        print(f"Total crawl sessions: {total_sessions}")
        print(f"Total businesses found: {total_businesses}")
        print(f"\nBreakdown by status:")
        for row in summary_results:
            print(f"  {row['status']}: {row['count']} sessions ({row['total_businesses'] or 0} businesses)")
            
    except Exception as e:
        print(f"Error querying database: {e}")
        return

if __name__ == "__main__":
    get_recent_crawl_sessions()