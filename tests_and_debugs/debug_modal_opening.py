#!/usr/bin/env python3
"""
Debug Modal Opening
Test the modal opening process and find correct selectors
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

async def debug_modal_opening():
    """Debug the modal opening process"""
    
    # Load config
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    test_car_id = "39940079"
    test_url = f"https://fem.encar.com/cars/detail/{test_car_id}"
    
    print(f"🔍 Debugging modal opening for: {test_url}")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Navigate to the page
            print("🌐 Navigating to page...")
            await page.goto(test_url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait for page to be fully loaded instead of fixed timeout
            print("⏳ Waiting for page to be fully loaded...")
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Check for CAPTCHA
            page_title = await page.title()
            if "reCAPTCHA" in page_title or "grecaptcha" in await page.content():
                print("🛡️ CAPTCHA detected, waiting for verification...")
                await page.wait_for_function(
                    'document.title && !document.title.includes("reCAPTCHA") && !document.querySelector(".grecaptcha-badge")',
                    timeout=30000
                )
                print("✅ CAPTCHA verification completed")
            
            # Wait for important elements to be present instead of fixed timeout
            print("⏳ Waiting for important page elements...")
            await page.wait_for_selector('.DetailSummary_btn_detail__msm-h', timeout=10000)
            
            # Check for detail button before clicking
            print("\n🔍 Checking for detail button...")
            detail_button = await page.query_selector('.DetailSummary_btn_detail__msm-h')
            if detail_button:
                button_text = await detail_button.inner_text()
                print(f"✅ Found detail button: '{button_text}'")
                
                # Check if button is visible and clickable
                is_visible = await detail_button.is_visible()
                print(f"   Visible: {is_visible}")
                
                if is_visible:
                    print("🔍 Clicking detail button...")
                    await detail_button.click()
                    
                    # Wait for modal to appear instead of fixed timeout
                    print("⏳ Waiting for modal to open...")
                    try:
                        await page.wait_for_selector('.BottomSheet-module_inner_contents__-vTmf', timeout=5000)
                        print("✅ Modal opened successfully")
                    except:
                        print("⚠️ Modal didn't open with expected selector, trying alternative...")
                        # Wait for any element that contains views info
                        await page.wait_for_function(
                            'document.querySelector("ul") && document.querySelector("ul").textContent.includes("조회수")',
                            timeout=5000
                        )
                        print("✅ Modal content detected")
                    
                    # Check for modal elements
                    print("\n🔍 Checking for modal elements...")
                    
                    modal_selectors = [
                        '.DetailSpec_list_default__Gx+ZA',
                        '.BottomSheet-module_inner_contents__-vTmf',
                    ]
                    
                    modal_found = False
                    for i, selector in enumerate(modal_selectors):
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                print(f"✅ Found modal element with selector {i+1}: {selector}")
                                modal_found = True
                                
                                # Check if it contains the views information
                                element_text = await element.inner_text()
                                if "조회수" in element_text:
                                    print(f"  ⭐ CONTAINS VIEWS INFO!")
                                    print(f"  Text: {element_text[:200]}...")
                                break
                            else:
                                print(f"❌ Modal selector {i+1} not found: {selector}")
                        except Exception as e:
                            print(f"❌ Error with modal selector {i+1}: {e}")
                    
                    if not modal_found:
                        print("\n❌ No modal elements found. Checking for any new elements...")
                        
                        # Look for any new elements that appeared after clicking
                        all_elements = await page.query_selector_all('*')
                        new_elements = []
                        
                        for elem in all_elements[:100]:  # Check first 100 elements
                            try:
                                elem_class = await elem.get_attribute('class')
                                elem_tag = await elem.evaluate('el => el.tagName')
                                elem_text = await elem.inner_text()
                                
                                if elem_class and any(keyword in elem_class for keyword in ['Detail', 'Spec', 'Sheet', 'Modal']):
                                    new_elements.append((elem_tag, elem_class, elem_text[:100]))
                            except:
                                continue
                        
                        if new_elements:
                            print("🔍 Found potential modal-related elements:")
                            for tag, class_name, text in new_elements:
                                print(f"  Tag: {tag}, Class: {class_name}")
                                print(f"  Text: {text}")
                        else:
                            print("❌ No modal-related elements found")
                    
                    # Check for question mark button in modal
                    print("\n🔍 Checking for question mark button in modal...")
                    question_selectors = [
                        'button:has-text("조회수 자세히보기")',
                        '.Icon_uiico_question__JxaTq',
                    ]
                    
                    question_found = False
                    for i, selector in enumerate(question_selectors):
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                print(f"✅ Found question button with selector {i+1}: {selector}")
                                question_found = True

                                await element.click()
                                
                                # Wait for tooltip to appear instead of fixed timeout
                                print("⏳ Waiting for tooltip to appear...")
                                try:
                                    # Wait for any tooltip element to appear
                                    await page.wait_for_function(
                                        'document.querySelector("[class*=\\"tooltip\\"]") || document.querySelector("[class*=\\"Tooltip\\"]")',
                                        timeout=3000
                                    )
                                    print("✅ Tooltip appeared")
                                except:
                                    print("⚠️ Tooltip didn't appear with expected selectors")
                                
                                # Try multiple tooltip selectors and check content
                                tooltip_element = None
                                tooltip_selectors = [
                                    '.TooltipPopper_area__iKVzy',
                                    '.react-tooltip-lite-button',
                                ]
                                
                                for tooltip_selector in tooltip_selectors:
                                    try:
                                        # Get all tooltip elements and check their content
                                        tooltip_elements = await page.query_selector_all(tooltip_selector)
                                        for elem in tooltip_elements:
                                            try:
                                                tooltip_text = await elem.inner_text()
                                                # Look for tooltip that contains registration date info
                                                if "최초등록일" in tooltip_text or "등록일" in tooltip_text:
                                                    tooltip_element = elem
                                                    print(f"Found registration tooltip with selector: {tooltip_selector}")
                                                    break
                                            except:
                                                continue
                                        if tooltip_element:
                                            break
                                    except:
                                        continue
                                
                                if tooltip_element:
                                    tooltip_text = await tooltip_element.inner_text()
                                    date_match = re.search(r'최초등록일\s*(\d{4}/\d{2}/\d{2})', tooltip_text)
                                    if date_match:
                                        registration_date = date_match.group(1)
                                        print(f"Got registration date: {registration_date}")
                                    else:
                                        print(f"Tooltip text: {tooltip_text[:200]}...")
                                else:
                                    print("No registration tooltip found")

                                break
                            else:
                                print(f"❌ Question selector {i+1} not found: {selector}")
                        except Exception as e:
                            print(f"❌ Error with question selector {i+1}: {e}")
                    
                    if not question_found:
                        print("❌ No question button found in modal")
                else:
                    print("❌ Detail button is not visible")
            else:
                print("❌ Detail button not found")
            
            # Take a screenshot
            await page.screenshot(path="debug_modal.png")
            print("\n📸 Screenshot saved as 'debug_modal.png'")
            
            print("\n⏳ Browser will close in 15 seconds...")
            await asyncio.sleep(15)
            
        except Exception as e:
            print(f"❌ Error during debugging: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_modal_opening()) 