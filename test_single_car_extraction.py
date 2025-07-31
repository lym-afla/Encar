#!/usr/bin/env python3
"""
Test Single Car Extraction
Test the get_views_and_registration_efficient method with a single car ID
"""

import asyncio
import logging
import yaml
from encar_scraper_api import EncarScraperAPI

async def test_single_car_extraction():
    """Test extraction for a single car ID"""
    
    # Set up logging
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')
    
    # Load config
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Test with a specific car ID
    test_car_id = "39940079"  # GLE-클래스 W167 AMG GLE53 4MATIC+
    test_url = f"https://fem.encar.com/cars/detail/{test_car_id}"
    
    print(f"🧪 Testing single car extraction for ID: {test_car_id}")
    print(f"   URL: {test_url}")
    print("=" * 60)
    
    async with EncarScraperAPI(config) as scraper:
        # Create a test listing
        test_listing = {
            'car_id': test_car_id,
            'title': 'GLE-클래스 W167 AMG GLE53 4MATIC+',
            'listing_url': test_url,
            'is_lease': False
        }
        
        print("🔍 Testing get_views_and_registration_efficient...")
        
        try:
            # Test the extraction method
            views, registration_date, lease_info = await scraper.get_views_and_registration_efficient(
                test_url, test_listing
            )
            
            print(f"\n📊 Results:")
            print(f"   Views: {views}")
            print(f"   Registration Date: {registration_date or 'Not found'}")
            print(f"   Lease Info: {lease_info or 'Not a lease'}")
            
            if views > 0:
                print(f"   ✅ Views extraction: SUCCESS ({views} views)")
            else:
                print(f"   ❌ Views extraction: FAILED")
                
            if registration_date:
                print(f"   ✅ Registration extraction: SUCCESS ({registration_date})")
            else:
                print(f"   ❌ Registration extraction: FAILED")
                
            if lease_info:
                print(f"   ✅ Lease extraction: SUCCESS")
            else:
                print(f"   ℹ️ Lease extraction: Not applicable")
                
        except Exception as e:
            print(f"❌ Error during extraction: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n✅ Single car extraction test completed!")

if __name__ == "__main__":
    asyncio.run(test_single_car_extraction()) 