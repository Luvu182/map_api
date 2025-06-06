"""
Supabase client and database operations
"""
from supabase import create_client, Client
from typing import List, Optional, Dict
import logging
from ..config import SUPABASE_URL, SUPABASE_KEY
from ..models import Road, Business, CrawlJob

logger = logging.getLogger(__name__)

class SupabaseClient:
    def __init__(self):
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Road operations
    def get_roads_with_names(self, state_code: str, limit: int = 100, offset: int = 0) -> List[Road]:
        """Get roads with names for a specific state"""
        try:
            response = self.client.table('roads') \
                .select('*') \
                .eq('state_code', state_code) \
                .not_.is_('fullname', 'null') \
                .range(offset, offset + limit - 1) \
                .execute()
            
            return [Road(**road) for road in response.data]
        except Exception as e:
            logger.error(f"Error fetching roads: {e}")
            return []
    
    def get_unprocessed_roads(self, limit: int = 100) -> List[Road]:
        """Get roads that haven't been crawled yet"""
        try:
            # First get all processed road IDs
            processed_response = self.client.table('crawl_jobs') \
                .select('road_linearid') \
                .eq('status', 'completed') \
                .execute()
            
            processed_ids = [r['road_linearid'] for r in processed_response.data]
            
            # Then get roads not in that list
            query = self.client.table('roads') \
                .select('*') \
                .not_.is_('fullname', 'null') \
                .limit(limit)
            
            # If we have processed roads, exclude them
            if processed_ids:
                # Supabase doesn't support NOT IN directly, so we'll filter in Python
                all_roads = query.execute()
                unprocessed = [r for r in all_roads.data if r['linearid'] not in processed_ids]
                return [Road(**road) for road in unprocessed[:limit]]
            else:
                response = query.execute()
                return [Road(**road) for road in response.data]
        except Exception as e:
            logger.error(f"Error fetching unprocessed roads: {e}")
            return []
    
    # Business operations
    def save_business(self, business: Business) -> bool:
        """Save a business to database"""
        try:
            self.client.table('businesses').upsert(
                business.model_dump(),
                on_conflict='place_id'
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Error saving business: {e}")
            return False
    
    def save_businesses_batch(self, businesses: List[Business]) -> int:
        """Save multiple businesses"""
        if not businesses:
            return 0
        
        try:
            data = [b.model_dump() for b in businesses]
            self.client.table('businesses').upsert(
                data,
                on_conflict='place_id'
            ).execute()
            return len(businesses)
        except Exception as e:
            logger.error(f"Error saving businesses batch: {e}")
            return 0
    
    # Crawl job operations
    def create_crawl_job(self, road: Road) -> Optional[str]:
        """Create a new crawl job"""
        try:
            job_data = {
                'road_linearid': road.linearid,
                'road_name': road.fullname,
                'county_fips': road.county_fips,
                'state_code': road.state_code,
                'status': 'pending'
            }
            
            response = self.client.table('crawl_jobs').insert(job_data).execute()
            return response.data[0]['job_id'] if response.data else None
        except Exception as e:
            logger.error(f"Error creating crawl job: {e}")
            return None
    
    def update_crawl_job(self, job_id: str, status: str, businesses_found: int = 0, error: str = None):
        """Update crawl job status"""
        try:
            update_data = {
                'status': status,
                'businesses_found': businesses_found
            }
            
            if status == 'processing':
                update_data['started_at'] = 'now()'
            elif status in ['completed', 'failed']:
                update_data['completed_at'] = 'now()'
                if error:
                    update_data['error_message'] = error
            
            self.client.table('crawl_jobs').update(update_data).eq('job_id', job_id).execute()
        except Exception as e:
            logger.error(f"Error updating crawl job: {e}")
    
    # County operations
    def get_counties_by_state(self, state_code: str) -> List[Dict]:
        """Get all counties for a specific state"""
        try:
            response = self.client.table('counties') \
                .select('county_fips, county_name') \
                .eq('state_code', state_code) \
                .order('county_name') \
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching counties: {e}")
            return []
    
    def get_states_summary(self) -> Dict:
        """Get summary of all states"""
        try:
            response = self.client.table('states') \
                .select('state_code, state_name, total_roads') \
                .order('state_name') \
                .execute()
            
            # Also get county counts
            counties_response = self.client.table('counties') \
                .select('state_code') \
                .execute()
            
            county_counts = {}
            for county in counties_response.data:
                state = county['state_code']
                county_counts[state] = county_counts.get(state, 0) + 1
            
            # Combine data
            for state in response.data:
                state['county_count'] = county_counts.get(state['state_code'], 0)
            
            return {
                'states': response.data,
                'total_states': len(response.data),
                'total_counties': len(counties_response.data)
            }
        except Exception as e:
            logger.error(f"Error fetching states summary: {e}")
            return {'states': [], 'total_states': 0, 'total_counties': 0}
    
    # Crawl Status Operations
    def get_crawl_status(self, state_code: str = None, county_fips: str = None, keyword: str = None) -> List[Dict]:
        """Get crawl status for roads"""
        try:
            query = self.client.table('crawl_status').select('*')
            
            if keyword:
                query = query.eq('keyword', keyword)
            
            # If filtering by location, need to join with roads table
            if state_code or county_fips:
                # Get road IDs first
                road_query = self.client.table('roads').select('linearid')
                if state_code:
                    road_query = road_query.eq('state_code', state_code)
                if county_fips:
                    road_query = road_query.eq('county_fips', county_fips)
                
                road_ids = [r['linearid'] for r in road_query.execute().data]
                if road_ids:
                    query = query.in_('road_linearid', road_ids)
            
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching crawl status: {e}")
            return []
    
    def update_crawl_status(self, road_linearid: str, keyword: str, status: str, 
                           businesses_found: int = 0, error_message: str = None) -> bool:
        """Update or create crawl status for a road-keyword combination"""
        try:
            data = {
                'road_linearid': road_linearid,
                'keyword': keyword,
                'status': status,
                'businesses_found': businesses_found
            }
            
            if error_message:
                data['error_message'] = error_message
            
            # Upsert - insert or update if exists
            self.client.table('crawl_status').upsert(
                data,
                on_conflict='road_linearid,keyword'
            ).execute()
            
            return True
        except Exception as e:
            logger.error(f"Error updating crawl status: {e}")
            return False
    
    # Statistics
    def get_crawl_stats(self) -> Dict:
        """Get crawling statistics - only queries dynamic data"""
        try:
            stats = {}
            
            # Skip static queries - these are hardcoded in API
            # stats['total_roads'] = 5155787  # Static
            # stats['roads_with_names'] = 3428598  # Static
            
            # Only query dynamic data
            # Roads processed
            roads_processed = self.client.table('crawl_jobs').select('count', count='exact') \
                .eq('status', 'completed').execute().count
            stats['roads_processed'] = roads_processed
            
            # Total businesses
            businesses_found = self.client.table('businesses').select('count', count='exact').execute().count
            stats['businesses_found'] = businesses_found
            
            stats['avg_businesses_per_road'] = businesses_found / roads_processed if roads_processed > 0 else 0
            
            return stats
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}