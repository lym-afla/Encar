#!/usr/bin/env python3
"""
Test Enhanced Extraction
Tests the enhanced extraction method with the fixed modal detection.
"""

import asyncio
import logging
import yaml
import sys
import os

# Add parent directory to path so we can import modules from the root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from encar_scraper_api import EncarScraperAPI

async def test_enhanced_extraction():
    """Test the enhanced extraction method"""
    print("🧪 Testing Enhanced Extraction Method")
    print("=" * 50)
    
    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('test_enhanced_extraction.log', encoding='utf-8')
        ]
    )
    
    # Load config from parent directory
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return
    
    # Test URL (same as in debug script)
    test_url = "https://fem.encar.com/cars/detail/39379103"
    test_listing = {
        'car_id': '39379103',
        'title': 'Test Vehicle',
        'is_lease': False
    }
    
    print(f"🔍 Testing extraction for: {test_url}")
    
    try:
        async with EncarScraperAPI(config) as scraper:
            # Test the enhanced extraction method
            views, registration_date, lease_info = await scraper.get_views_registration_and_lease(
                test_url, test_listing
            )
            
            print("\n📊 Results:")
            print(f"   Views: {views}")
            print(f"   Registration Date: {registration_date}")
            print(f"   Lease Info: {lease_info}")
            
            if views > 0:
                print("   ✅ Views extraction: SUCCESS")
            else:
                print("   ❌ Views extraction: FAILED")
                
            if registration_date:
                print("   ✅ Registration extraction: SUCCESS")
            else:
                print("   ❌ Registration extraction: FAILED")
                
            if lease_info:
                print("   ✅ Lease extraction: SUCCESS")
            else:
                print("   ℹ️ Lease extraction: Not applicable")
                
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        logging.error(f"Testing error: {e}")


if __name__ == "__main__":
    asyncio.run(test_enhanced_extraction()) 