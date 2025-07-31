#!/usr/bin/env python3
"""
Debug Views and Registration Extraction
Test with specific car IDs to identify the timeout issues.
"""

import asyncio
import logging
import yaml
from playwright.async_api import async_playwright
import re
from typing import Optional

async def debug_single_car(car_id: str, listing_url: str):
    """Debug views and registration extraction for a single car"""
    print(f"🔍 Debugging car ID: {car_id}")
    print(f"   URL: {listing_url}")
    
    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Set to False for debugging
            page = await browser.new_page()
            
            # Set longer timeout and more flexible navigation
            page.set_default_timeout(60000)  # 60 seconds
            
            print("   🌐 Navigating to page...")
            try:
                await page.goto(listing_url, wait_until='domcontentloaded', timeout=60000)
                await page.wait_for_timeout(5000)  # Wait longer for page to load
                print("   📄 Page loaded successfully")
            except Exception as e:
                print(f"   ⚠️ Navigation timeout, but continuing: {e}")
            
            # Take initial screenshot
            screenshot_path = f"debug_{car_id}_initial.png"
            await page.screenshot(path=screenshot_path)
            print(f"   📸 Initial screenshot saved: {screenshot_path}")
            
            # Try multiple approaches to find views and registration
            print("   🔍 Attempting multiple extraction methods...")
            
            # Method 1: Look for any element with 조회수 (views)
            print("   📊 Method 1: Searching for views...")
            try:
                # Search for any element containing 조회수
                views_elements = await page.query_selector_all('*:has-text("조회수")')
                print(f"   📋 Found {len(views_elements)} elements with 조회수")
                
                for i, elem in enumerate(views_elements[:3]):  # Check first 3
                    try:
                        text = await elem.inner_text()
                        print(f"   📝 Element {i+1}: {text}")
                        
                        # Try to extract views number
                        views_match = re.search(r'조회수\s*([\d,]+)', text)
                        if views_match:
                            views_str = views_match.group(1).replace(',', '')
                            views = int(views_str)
                            print(f"   👁️ Found views: {views}")
                            break
                    except Exception as e:
                        print(f"   ⚠️ Error reading element {i+1}: {e}")
            except Exception as e:
                print(f"   ❌ Method 1 failed: {e}")
            
            # Method 2: Look for detail button with more flexible selector
            print("   📋 Method 2: Looking for detail button...")
            try:
                # Try multiple possible selectors for detail button
                detail_selectors = [
                    '.DetailSummary_btn_detail__msm-h',
                    'button:has-text("상세보기")',
                    'button:has-text("detail")',
                    '[class*="btn_detail"]',
                    '[class*="DetailSummary"]'
                ]
                
                detail_button = None
                for selector in detail_selectors:
                    try:
                        detail_button = await page.wait_for_selector(selector, timeout=5000)
                        if detail_button:
                            print(f"   ✅ Found detail button with selector: {selector}")
                            break
                    except:
                        continue
                
                if detail_button:
                    await detail_button.click()
                    await page.wait_for_timeout(3000)
                    print("   📋 Detail modal opened")
                    
                    # Take screenshot after modal opens
                    modal_screenshot = f"debug_{car_id}_modal.png"
                    await page.screenshot(path=modal_screenshot)
                    print(f"   📸 Modal screenshot saved: {modal_screenshot}")
                    
                    # Look for registration date in modal
                    print("   📅 Looking for registration date...")
                    try:
                        # Try to find registration date in modal content
                        reg_elements = await page.query_selector_all('*:has-text("최초등록일")')
                        print(f"   📋 Found {len(reg_elements)} elements with 최초등록일")
                        
                        if len(reg_elements) == 0:
                            # Try alternative approach - look for registration date in the modal text
                            modal_text = await page.inner_text('body')
                            print(f"   📄 Modal text length: {len(modal_text)} characters")
                            
                            # Look for registration date patterns
                            reg_patterns = [
                                r'최초등록일\s*(\d{4}/\d{2}/\d{2})',
                                r'등록일\s*(\d{4}/\d{2}/\d{2})',
                                r'최초\s*(\d{4}/\d{2}/\d{2})',
                                r'(\d{4}/\d{2}/\d{2})'
                            ]
                            
                            for pattern in reg_patterns:
                                date_match = re.search(pattern, modal_text)
                                if date_match:
                                    registration_date = date_match.group(1)
                                    print(f"   📅 Found registration date with pattern '{pattern}': {registration_date}")
                                    break
                            else:
                                print("   ❌ Registration date not found with any pattern")
                        else:
                            for i, elem in enumerate(reg_elements):
                                try:
                                    text = await elem.inner_text()
                                    print(f"   📝 Registration element {i+1}: {text}")
                                    
                                    date_match = re.search(r'최초등록일\s*(\d{4}/\d{2}/\d{2})', text)
                                    if date_match:
                                        registration_date = date_match.group(1)
                                        print(f"   📅 Found registration date: {registration_date}")
                                        break
                                except Exception as e:
                                    print(f"   ⚠️ Error reading registration element {i+1}: {e}")
                    except Exception as e:
                        print(f"   ❌ Error looking for registration date: {e}")
                else:
                    print("   ❌ Detail button not found with any selector")
            except Exception as e:
                print(f"   ❌ Method 2 failed: {e}")
            
            # Method 3: Try to find any information about the car
            print("   🔍 Method 3: Looking for any car information...")
            try:
                # Look for any text that might contain car details
                page_text = await page.inner_text('body')
                print(f"   📄 Page text length: {len(page_text)} characters")
                
                # Look for specific patterns
                if "조회수" in page_text:
                    print("   ✅ Found 조회수 in page text")
                if "최초등록일" in page_text:
                    print("   ✅ Found 최초등록일 in page text")
                if "GLE" in page_text:
                    print("   ✅ Found GLE in page text")
                    
            except Exception as e:
                print(f"   ❌ Method 3 failed: {e}")
            
    except Exception as e:
        print(f"   ❌ Error during debugging: {e}")
    finally:
        if browser:
            await browser.close()

async def test_with_api_cars():
    """Test with real car IDs from the API"""
    
    # Load config
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    from encar_api_client import EncarAPIClient
    
    try:
        async with EncarAPIClient(config) as api_client:
            print("🧪 DEBUGGING VIEWS AND REGISTRATION EXTRACTION")
            print("=" * 60)
            
            # Get some real listings from API
            print("📊 Getting real car listings from API...")
            listings, _ = await api_client.get_listings(limit=3)
            
            if not listings:
                print("❌ No listings found from API")
                return
            
            print(f"📊 Found {len(listings)} cars to test")
            
            for i, listing in enumerate(listings):
                car_id = listing.get('car_id', f'API_{i}')
                listing_url = listing.get('listing_url', '')
                
                if not listing_url:
                    print(f"⚠️ Skipping {car_id} - no URL")
                    continue
                
                print(f"\n🚗 Testing car: {car_id}")
                print(f"   Title: {listing.get('title', 'N/A')}")
                print(f"   URL: {listing_url}")
                await debug_single_car(car_id, listing_url)
                await asyncio.sleep(2)  # Brief pause between tests
            
            print("\n✅ Debug testing completed!")
            
    except Exception as e:
        print(f"❌ Error accessing API: {e}")

if __name__ == "__main__":
    asyncio.run(test_with_api_cars()) 