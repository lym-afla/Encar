#!/usr/bin/env python3
"""
Test Lease Detection on Real Page
Test the extract_lease_terms_from_page method against the real page
"""

import sys
import os
import asyncio
import logging

# Add parent directory to path so we can import modules from the root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from encar_scraper_api import EncarScraperAPI
import yaml

async def test_lease_detection():
    """Test lease detection on the real page"""
    print("🧪 Testing Lease Detection on Real Page")
    print("=" * 50)
    
    # Load config
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Create scraper instance
    scraper = EncarScraperAPI(config)
    
    # Test URL
    test_url = "https://fem.encar.com/cars/detail/39727392"
    
    print(f"🔗 Testing URL: {test_url}")
    
    try:
        async with scraper:
            # Launch browser in non-headless mode for debugging
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)  # Non-headless for debugging
                page = await browser.new_page()
                
                print("🌐 Navigating to page...")
                
                # Navigate with better loading strategy
                await page.goto(test_url, wait_until='networkidle', timeout=60000)
                
                # Wait for the page to be fully loaded
                print("⏳ Waiting for page to fully load...")
                await page.wait_for_timeout(10000)  # Wait 10 seconds for any dynamic content
                
                # Wait for any specific elements that might indicate the page is ready
                try:
                    # Wait for the main content to be visible
                    await page.wait_for_selector('.DetailCarPhotoPc_info__0IA0t', timeout=10000)
                    print("✅ Main content loaded")
                except:
                    print("⚠️ Main content selector not found, continuing anyway...")
                
                # Check page title and content
                page_title = await page.title()
                print(f"📄 Page title: {page_title}")
                
                # Get page content after ensuring it's fully loaded
                page_content = await page.content()
                print(f"📄 Page content length: {len(page_content)} characters")
                
                # Check for lease keywords in content
                lease_keywords = ["리스", "렌트", "월 납입금", "보증금", "리스료", "월리스", "리스기간", "월 렌트비", "렌트료"]
                print("\n🔍 Checking for lease keywords:")
                for keyword in lease_keywords:
                    if keyword in page_content:
                        print(f"   ✅ Found: {keyword}")
                    else:
                        print(f"   ❌ Not found: {keyword}")
                
                # Test the extract_lease_terms_from_page method
                print("\n🧪 Testing extract_lease_terms_from_page method...")
                lease_info = await scraper.extract_lease_terms_from_page(page)
                
                if lease_info:
                    print("✅ Lease terms extracted successfully!")
                    print(f"   Is Lease: {lease_info.get('is_lease', False)}")
                    print(f"   Deposit: {lease_info.get('deposit')}만원")
                    print(f"   Monthly Payment: {lease_info.get('monthly_payment')}만원")
                    print(f"   Lease Term: {lease_info.get('lease_term_months')} months")
                    print(f"   True Price: {lease_info.get('true_price')}만원")
                    print(f"   Total Cost: {lease_info.get('total_cost')}만원")
                else:
                    print("❌ No lease terms extracted")
                
                # Let's also check the page content more specifically
                print("\n🔍 Detailed content analysis:")
                
                # Look for specific lease-related text
                lease_indicators = [
                    "인수금",
                    "차량가격", 
                    "월리스료",
                    "개월",
                    "리스",
                    "렌트"
                ]
                
                for indicator in lease_indicators:
                    if indicator in page_content:
                        print(f"   ✅ Found: {indicator}")
                        # Find the context around this indicator
                        index = page_content.find(indicator)
                        if index != -1:
                            context_start = max(0, index - 100)
                            context_end = min(len(page_content), index + 100)
                            context = page_content[context_start:context_end]
                            print(f"      Context: {context}")
                    else:
                        print(f"   ❌ Not found: {indicator}")
                
                # Try to find any lease-related elements on the page
                print("\n🔍 Looking for lease-related elements on the page...")
                
                # Look for any elements that might contain lease information
                lease_selectors = [
                    '[class*="lease"]',
                    '[class*="rent"]',
                    '[class*="리스"]',
                    '[class*="렌트"]',
                    '[class*="DetailLease"]',
                    '[class*="DetailRent"]'
                ]
                
                for selector in lease_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            print(f"   ✅ Found {len(elements)} elements with selector: {selector}")
                            for i, elem in enumerate(elements[:3]):  # Show first 3
                                try:
                                    text = await elem.inner_text()
                                    print(f"      Element {i+1}: {text[:100]}...")
                                except:
                                    print(f"      Element {i+1}: [Could not get text]")
                    except Exception as e:
                        print(f"   ❌ Error with selector {selector}: {e}")
                
                # Look for any buttons or links that might reveal lease information
                print("\n🔍 Looking for buttons that might reveal lease info...")
                try:
                    buttons = await page.query_selector_all('button')
                    for button in buttons[:10]:  # Check first 10 buttons
                        try:
                            button_text = await button.inner_text()
                            if any(keyword in button_text for keyword in ["리스", "렌트", "상세", "자세히"]):
                                print(f"   ✅ Found relevant button: {button_text}")
                        except:
                            continue
                except Exception as e:
                    print(f"   ❌ Error checking buttons: {e}")
                
                # Wait a bit so we can see the browser
                print("\n⏳ Waiting 15 seconds to inspect the page...")
                await page.wait_for_timeout(15000)
                
                await browser.close()
                
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_lease_detection()) 