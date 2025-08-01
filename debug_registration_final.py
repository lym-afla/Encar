#!/usr/bin/env python3
"""
Debug Registration Final
Test registration extraction after modal is opened
"""

import asyncio
import logging
import yaml
from playwright.async_api import async_playwright
import re

async def debug_registration_final():
    """Debug registration extraction after modal is opened"""
    
    # Load config
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    test_car_id = "39940079"
    test_url = f"https://fem.encar.com/cars/detail/{test_car_id}"
    
    print(f"🔍 Final registration debug for: {test_url}")
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
            
            # Open modal
            print("\n🔍 Opening modal...")
            detail_button = await page.wait_for_selector('.DetailSummary_btn_detail__msm-h', timeout=10000)
            if detail_button:
                print("✅ Found detail button, clicking...")
                await detail_button.click()
                await page.wait_for_timeout(3000)
                
                # Wait for modal to open
                modal_ul = await page.wait_for_selector('.BottomSheet-module_inner_contents__-vTmf', timeout=5000)
                if modal_ul:
                    print("✅ Modal opened successfully")
                    
                    # Find question button
                    print("\n🔍 Looking for question button...")
                    question_button = await page.wait_for_selector('button:has-text("조회수 자세히보기")', timeout=5000)
                    if question_button:
                        print("✅ Found question button, clicking...")
                        await question_button.click()
                        await page.wait_for_timeout(2000)
                        
                        # Look for tooltip
                        print("\n🔍 Looking for tooltip...")
                        
                        # Wait a bit for tooltip to appear
                        await page.wait_for_timeout(1000)
                        
                        # Check for tooltip elements
                        tooltip_elements = await page.query_selector_all('[class*="tooltip"]')
                        print(f"Found {len(tooltip_elements)} tooltip elements")
                        
                        for i, elem in enumerate(tooltip_elements):
                            try:
                                elem_class = await elem.get_attribute('class')
                                elem_text = await elem.inner_text()
                                print(f"\nTooltip {i+1}:")
                                print(f"  Class: {elem_class}")
                                print(f"  Text: '{elem_text[:200]}...'")
                                
                                if "등록일" in elem_text or "최초등록일" in elem_text:
                                    print(f"  ⭐ CONTAINS REGISTRATION INFO!")
                                    
                                    # Extract registration date
                                    date_match = re.search(r'최초등록일\s*(\d{4}/\d{2}/\d{2})', elem_text)
                                    if date_match:
                                        registration_date = date_match.group(1)
                                        print(f"  ✅ Found registration date: {registration_date}")
                                    else:
                                        print(f"  ❌ No registration date pattern found")
                                        print(f"  Full text: {elem_text}")
                            except Exception as e:
                                print(f"  Error reading tooltip {i+1}: {e}")
                        
                        if not tooltip_elements:
                            print("❌ No tooltip elements found")
                            
                            # Check for any new elements that appeared
                            print("\n🔍 Checking for any new elements after clicking...")
                            all_elements = await page.query_selector_all('*')
                            new_elements = []
                            
                            for elem in all_elements[:50]:
                                try:
                                    elem_class = await elem.get_attribute('class')
                                    elem_text = await elem.inner_text()
                                    if elem_class and any(keyword in elem_class for keyword in ['tooltip', 'Tooltip', 'popover', 'Popover']):
                                        new_elements.append((elem_class, elem_text[:100]))
                                except:
                                    continue
                            
                            if new_elements:
                                print("🔍 Found potential tooltip elements:")
                                for class_name, text in new_elements:
                                    print(f"  Class: {class_name}")
                                    print(f"  Text: {text}")
                            else:
                                print("❌ No tooltip-like elements found")
                    else:
                        print("❌ Question button not found")
                else:
                    print("❌ Modal not opened")
            else:
                print("❌ Detail button not found")
            
            # Take a screenshot
            await page.screenshot(path="debug_registration_final.png")
            print("\n📸 Screenshot saved as 'debug_registration_final.png'")
            
            print("\n⏳ Browser will close in 5 seconds...")
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"❌ Error during debugging: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_registration_final()) 