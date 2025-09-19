#!/usr/bin/env python3
"""
Test script for the updated API query with specific GLE Coupe targeting
"""

import asyncio
import logging
import yaml
import sys
import os
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from encar_api_client import EncarAPIClient

async def test_api_query():
    """Test the updated API query"""
    print("🧪 Testing Updated API Query")
    print("=" * 50)
    
    # Load config
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Test the query building
    print("1️⃣ Testing Query Building")
    print("-" * 30)
    
    client = EncarAPIClient(config)
    
    # Test base query (no filters)
    base_query = client.build_api_query()
    print(f"Base query (no filters):")
    print(f"  {base_query}")
    print()
    
    # Test with filters
    test_filters = {
        'year_min': 2021,
        'price_max': 90.0
    }
    filtered_query = client.build_api_query(test_filters)
    print(f"Filtered query (year >= 2021, price <= 90M):")
    print(f"  {filtered_query}")
    print()
    
    # Test API call
    print("2️⃣ Testing API Call")
    print("-" * 30)
    
    try:
        async with client:
            # Test basic API call using the proper method
            print("Testing basic API call...")
            listings, total_count = await client.get_listings(offset=0, limit=5)
            
            print(f"✅ API call successful!")
            print(f"📊 Total GLE Coupe listings found: {total_count}")
            print(f"📋 Sample listings ({len(listings)}):")
            
            for i, listing in enumerate(listings[:3], 1):
                car_id = listing.get('car_id', 'N/A')
                title = listing.get('title', 'N/A')
                year = listing.get('year', 'N/A')
                price = listing.get('price', 'N/A')
                mileage = listing.get('mileage', 'N/A')
                
                print(f"  {i}. ID: {car_id}")
                print(f"     Title: {title}")
                print(f"     Year: {year}, Price: {price}, Mileage: {mileage}")
                print()
            
            # Test filtered query
            print("Testing filtered query...")
            filtered_listings, filtered_count = await client.get_listings_with_filters(
                filters=test_filters, 
                offset=0, 
                limit=5
            )
            
            print(f"✅ Filtered API call successful!")
            print(f"📊 Filtered GLE Coupe listings: {filtered_count}")
            print(f"📋 Sample filtered listings ({len(filtered_listings)}):")
            
            for i, listing in enumerate(filtered_listings[:3], 1):
                car_id = listing.get('car_id', 'N/A')
                title = listing.get('title', 'N/A')
                year = listing.get('year', 'N/A')
                price = listing.get('price', 'N/A')
                
                print(f"  {i}. ID: {car_id}")
                print(f"     Title: {title}")
                print(f"     Year: {year}, Price: {price}")
                print()
                
    except Exception as e:
        print(f"❌ Error during API test: {e}")
        import traceback
        traceback.print_exc()
    
    print("✅ API query test completed!")

if __name__ == "__main__":
    asyncio.run(test_api_query())
