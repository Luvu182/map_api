#!/usr/bin/env python3
"""
Script to start crawling process
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
import asyncio
from typing import Optional

API_BASE_URL = "http://localhost:8000"

async def start_crawl(state_code: Optional[str] = None, limit: int = 10):
    """Start crawling process"""
    async with httpx.AsyncClient() as client:
        # Check API health
        health = await client.get(f"{API_BASE_URL}/health")
        if health.status_code != 200:
            print("API is not healthy!")
            return
        
        # Get current stats
        stats = await client.get(f"{API_BASE_URL}/stats")
        print("Current stats:")
        print(stats.json())
        
        # Start crawling
        params = {"limit": limit}
        if state_code:
            params["state_code"] = state_code
        
        response = await client.post(
            f"{API_BASE_URL}/crawl/start",
            params=params
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n{result['message']}")
            print(f"Job IDs: {result['job_ids']}")
        else:
            print(f"Error: {response.text}")

async def main():
    """Main function"""
    print("Google Maps Business Crawler")
    print("-" * 50)
    
    # Example: Start crawling for California roads
    await start_crawl(state_code="CA", limit=5)
    
    # Or crawl any unprocessed roads
    # await start_crawl(limit=10)

if __name__ == "__main__":
    asyncio.run(main())