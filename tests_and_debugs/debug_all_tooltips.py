#!/usr/bin/env python3
"""
Debug All Tooltips
Find all tooltips on the page and their content
"""

import asyncio
import logging
import yaml
import sys
import os

# Add parent directory to path so we can import modules from the root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from playwright.async_api import async_playwright
import re

async def debug_all_tooltips():
    """Debug to find all tooltips on the page"""
    
    # Load config
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    test_car_id = "39940079"
    test_url = f"https://fem.encar.com/cars/detail/{test_car_id}"
    
    print(f"🔍 Debugging all tooltips for: {test_url}")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Navigate to the page
            print("🌐 Navigating to page...")
            await page.goto(test_url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(5000)
            
            # Check for CAPTCHA
            page_title = await page.title()
            if "reCAPTCHA" in page_title or "grecaptcha" in await page.content():
                print("🛡️ CAPTCHA detected, waiting for verification...")
                await page.wait_for_function(
                    'document.title && !document.title.includes("reCAPTCHA") && !document.querySelector(".grecaptcha-badge")',
                    timeout=30000
                )
                print("✅ CAPTCHA verification completed")
            
            await page.wait_for_timeout(3000)
            
            # Click the detail button first
            print("🔍 Looking for detail button...")
            detail_button = await page.wait_for_selector('.DetailSummary_btn_detail__msm-h', timeout=10000)
            if detail_button:
                print("✅ Found detail button, clicking...")
                await detail_button.click()
                await page.wait_for_timeout(3000)
            
            # Find all elements with tooltip-related classes
            print("\n🔍 Finding all tooltip-related elements...")
            
            tooltip_selectors = [
                '[class*="tooltip"]',
                '[class*="Tooltip"]',
                '[class*="popover"]',
                '[class*="Popover"]',
                '.react-tooltip-lite',
                '.TooltipPopper_area__iKVzy'
            ]
            
            all_tooltip_elements = []
            for selector in tooltip_selectors:
                elements = await page.query_selector_all(selector)
                all_tooltip_elements.extend(elements)
            
            print(f"Found {len(all_tooltip_elements)} tooltip-related elements")
            
            # Get content of all tooltip elements
            for i, elem in enumerate(all_tooltip_elements):
                try:
                    elem_class = await elem.get_attribute('class')
                    elem_text = await elem.inner_text()
                    elem_tag = await elem.evaluate('el => el.tagName')
                    
                    print(f"\nTooltip Element {i+1}:")
                    print(f"  Tag: {elem_tag}")
                    print(f"  Class: {elem_class}")
                    print(f"  Text: '{elem_text[:200]}...'")
                    
                    # Check if it contains registration-related text
                    if any(keyword in elem_text for keyword in ['등록일', '최초등록일', '등록']):
                        print(f"  ⭐ CONTAINS REGISTRATION INFO!")
                    
                except Exception as e:
                    print(f"  Error reading element {i+1}: {e}")
            
            # Now click the question button and see what tooltips appear
            print("\n🔍 Clicking question button and checking for new tooltips...")
            
            question_button = await page.query_selector('span[class*="question"]')
            if question_button:
                print("✅ Found question button, clicking...")
                await question_button.click()
                await page.wait_for_timeout(2000)
                
                # Check for new tooltips after clicking
                print("\n🔍 Checking for tooltips after clicking question button...")
                
                for selector in tooltip_selectors:
                    elements = await page.query_selector_all(selector)
                    for elem in elements:
                        try:
                            elem_class = await elem.get_attribute('class')
                            elem_text = await elem.inner_text()
                            elem_tag = await elem.evaluate('el => el.tagName')
                            
                            print(f"\nNew Tooltip after click:")
                            print(f"  Tag: {elem_tag}")
                            print(f"  Class: {elem_class}")
                            print(f"  Text: '{elem_text[:200]}...'")
                            
                            # Check if it contains registration-related text
                            if any(keyword in elem_text for keyword in ['등록일', '최초등록일', '등록']):
                                print(f"  ⭐ CONTAINS REGISTRATION INFO!")
                            
                        except Exception as e:
                            print(f"  Error reading element: {e}")
            else:
                print("❌ Question button not found")
            
            # Take a screenshot
            await page.screenshot(path="debug_all_tooltips.png")
            print("\n📸 Screenshot saved as 'debug_all_tooltips.png'")
            
            print("\n⏳ Browser will close in 15 seconds...")
            await asyncio.sleep(15)
            
        except Exception as e:
            print(f"❌ Error during debugging: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_all_tooltips()) 