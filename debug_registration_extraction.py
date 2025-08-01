#!/usr/bin/env python3
"""
Debug Registration Extraction
Test the registration date extraction with specific selectors
"""

import asyncio
import logging
import yaml
from playwright.async_api import async_playwright
import re

async def debug_registration_extraction():
    """Debug the registration date extraction specifically"""
    
    # Load config
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    test_car_id = "39940079"
    test_url = f"https://fem.encar.com/cars/detail/{test_car_id}"
    
    print(f"🔍 Debugging registration extraction for: {test_url}")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
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
            
            # Now look for the question mark button with specific selectors
            print("\n🔍 Testing question mark button selectors...")
            
            question_selectors = [
                'button:has-text("조회수 자세히보기")',
                '.Icon_uiico_question__JxaTq',
            ]
            
            question_button = None
            for i, selector in enumerate(question_selectors):
                try:
                    element = await page.query_selector(selector)
                    if element:
                        print(f"✅ Found question button with selector {i+1}: {selector}")
                        question_button = element
                        break
                    else:
                        print(f"❌ Selector {i+1} not found: {selector}")
                except Exception as e:
                    print(f"❌ Error with selector {i+1}: {e}")
            
            if question_button:
                print("\n🔍 Clicking question button...")
                await question_button.click()
                await page.wait_for_timeout(2000)
                
                # Look for tooltip
                print("\n🔍 Looking for tooltip...")
                tooltip_selectors = [
                    '.TooltipPopper_area__iKVzy',
                ]
                
                tooltip_element = None
                for i, selector in enumerate(tooltip_selectors):
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            print(f"✅ Found tooltip with selector {i+1}: {selector}")
                            tooltip_element = element
                            break
                        else:
                            print(f"❌ Tooltip selector {i+1} not found: {selector}")
                    except Exception as e:
                        print(f"❌ Error with tooltip selector {i+1}: {e}")
                
                if tooltip_element:
                    tooltip_text = await tooltip_element.inner_text()
                    print(f"\n📄 Tooltip text: {tooltip_text}")
                    
                    # Look for registration date
                    date_match = re.search(r'최초등록일\s*(\d{4}/\d{2}/\d{2})', tooltip_text)
                    if date_match:
                        registration_date = date_match.group(1)
                        print(f"✅ Found registration date: {registration_date}")
                    else:
                        print("❌ No registration date found in tooltip")
                        print(f"Tooltip content: {tooltip_text[:500]}...")
                else:
                    print("❌ No tooltip found")
                    
                    # Let's see what elements are available
                    print("\n🔍 Checking for any tooltip-like elements...")
                    all_elements = await page.query_selector_all('*')
                    tooltip_candidates = []
                    
                    for elem in all_elements[:50]:  # Check first 50 elements
                        try:
                            elem_class = await elem.get_attribute('class')
                            elem_text = await elem.inner_text()
                            if elem_class and ('tooltip' in elem_class.lower() or 'Tooltip' in elem_class):
                                tooltip_candidates.append((elem_class, elem_text[:100]))
                        except:
                            continue
                    
                    if tooltip_candidates:
                        print("🔍 Found potential tooltip elements:")
                        for class_name, text in tooltip_candidates:
                            print(f"  Class: {class_name}")
                            print(f"  Text: {text}")
                    else:
                        print("❌ No tooltip-like elements found")
            else:
                print("❌ No question button found")
            
            # Take a screenshot
            await page.screenshot(path="debug_registration.png")
            print("\n📸 Screenshot saved as 'debug_registration.png'")
            
            print("\n⏳ Browser will close in 5 seconds...")
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"❌ Error during debugging: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_registration_extraction()) 