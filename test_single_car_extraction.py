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

async def debug_page_content():
    """Debug function to see what's actually on the page"""
    import yaml
    from playwright.async_api import async_playwright
    
    # Load config
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    test_car_id = "39940079"
    test_url = f"https://fem.encar.com/cars/detail/{test_car_id}"
    
    print(f"🔍 Debugging page content for: {test_url}")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set to False to see the browser
        page = await browser.new_page()
        
        try:
            # Navigate to the page
            print("🌐 Navigating to page...")
            await page.goto(test_url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(5000)  # Wait longer
            
            print("📄 Page loaded, checking for selectors...")
            
            # Check if the detail button exists
            detail_button = await page.query_selector('.DetailSummary_btn_detail__msm-h')
            if detail_button:
                print("✅ Found .DetailSummary_btn_detail__msm-h")
                button_text = await detail_button.inner_text()
                print(f"   Button text: '{button_text}'")
            else:
                print("❌ .DetailSummary_btn_detail__msm-h NOT FOUND")
                
                # Let's see what buttons are available
                all_buttons = await page.query_selector_all('button')
                print(f"🔍 Found {len(all_buttons)} buttons on page:")
                for i, btn in enumerate(all_buttons[:10]):  # Show first 10
                    try:
                        btn_text = await btn.inner_text()
                        btn_class = await btn.get_attribute('class')
                        print(f"   Button {i+1}: '{btn_text}' (class: {btn_class})")
                    except:
                        print(f"   Button {i+1}: [error reading]")
            
            # Take a screenshot for debugging
            await page.screenshot(path="debug_page.png")
            print("\n📸 Screenshot saved as 'debug_page.png'")
            
            # Wait for user to see the browser
            print("\n⏳ Browser will close in 10 seconds...")
            await asyncio.sleep(10)
            
        except Exception as e:
            print(f"❌ Error during debugging: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    # # Run the debug version first
    # print("🔧 Running debug version to see what's on the page...")
    # asyncio.run(debug_page_content())
    
    print("\n" + "="*60)
    print("🧪 Now running the actual test...")
    asyncio.run(test_single_car_extraction()) 