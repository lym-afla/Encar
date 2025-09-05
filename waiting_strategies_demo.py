#!/usr/bin/env python3
"""
Waiting Strategies Demo
Show different waiting strategies and their trade-offs
"""

import asyncio
import logging
import yaml
from playwright.async_api import async_playwright
import time

async def demo_waiting_strategies():
    """Demo different waiting strategies"""
    
    # Load config
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    test_car_id = "39940079"
    test_url = f"https://fem.encar.com/cars/detail/{test_car_id}"
    
    print(f"🔍 Demo waiting strategies for: {test_url}")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Strategy 1: Fixed timeout (least efficient)
            print("\n1️⃣ Strategy 1: Fixed timeout")
            start_time = time.time()
            await page.goto(test_url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(5000)  # Fixed 5 second wait
            elapsed = time.time() - start_time
            print(f"   ⏱️  Time taken: {elapsed:.2f}s")
            print(f"   ❌ Always waits full time, even if page loads faster")
            
            # Strategy 2: Wait for specific element (more efficient)
            print("\n2️⃣ Strategy 2: Wait for specific element")
            start_time = time.time()
            await page.goto(test_url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_selector('.DetailSummary_btn_detail__msm-h', timeout=10000)
            elapsed = time.time() - start_time
            print(f"   ⏱️  Time taken: {elapsed:.2f}s")
            print(f"   ✅ Waits only until element appears")
            
            # Strategy 3: Wait for load state (most efficient for static pages)
            print("\n3️⃣ Strategy 3: Wait for load state")
            start_time = time.time()
            await page.goto(test_url, wait_until='domcontentloaded', timeout=30000)
            try:
                await page.wait_for_load_state('networkidle', timeout=25000)
                elapsed = time.time() - start_time
                print(f"   ⏱️  Time taken: {elapsed:.2f}s")
                print(f"   ✅ Waits for network to be idle")
            except:
                elapsed = time.time() - start_time
                print(f"   ⏱️  Time taken: {elapsed:.2f}s (timed out)")
                print(f"   ⚠️  Network never becomes idle (common with dynamic sites)")
            
            # Strategy 4: Wait for function (most flexible)
            print("\n4️⃣ Strategy 4: Wait for function")
            start_time = time.time()
            await page.goto(test_url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_function(
                'document.querySelector(".DetailSummary_btn_detail__msm-h") && document.querySelector(".DetailSummary_btn_detail__msm-h").offsetParent !== null',
                timeout=10000
            )
            elapsed = time.time() - start_time
            print(f"   ⏱️  Time taken: {elapsed:.2f}s")
            print(f"   ✅ Waits for element to be visible and clickable")
            
            # Strategy 5: Hybrid approach (recommended)
            print("\n5️⃣ Strategy 5: Hybrid approach (recommended)")
            start_time = time.time()
            await page.goto(test_url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait for essential elements
            await page.wait_for_selector('.DetailSummary_btn_detail__msm-h', timeout=10000)
            
            # Click and wait for modal
            detail_button = await page.query_selector('.DetailSummary_btn_detail__msm-h')
            if detail_button:
                await detail_button.click()
                
                # Wait for modal content to appear - more robust approach
                try:
                    # First try the specific modal selector
                    await page.wait_for_selector('.BottomSheet-module_inner_contents__-vTmf', timeout=5000)
                    print("   ✅ Modal opened with specific selector")
                except:
                    print("   ⚠️ Modal didn't open with specific selector, trying alternative...")
                    # Wait for any ul element that might contain modal content
                    await page.wait_for_function(
                        'document.querySelector("ul") && document.querySelector("ul").textContent.length > 100',
                        timeout=5000
                    )
                    print("   ✅ Modal content detected with alternative approach")
                
                elapsed = time.time() - start_time
                print(f"   ⏱️  Time taken: {elapsed:.2f}s")
                print(f"   ✅ Waits for each step to complete before proceeding")
                
                # Show what's actually in the modal
                print("\n   📄 Modal content preview:")
                try:
                    modal_content = await page.query_selector('.BottomSheet-module_inner_contents__-vTmf')
                    if modal_content:
                        content_text = await modal_content.inner_text()
                        print(f"   {content_text[:200]}...")
                    else:
                        # Try alternative selectors
                        all_ul_elements = await page.query_selector_all('ul')
                        for i, ul in enumerate(all_ul_elements[:3]):
                            try:
                                ul_text = await ul.inner_text()
                                if len(ul_text) > 50:  # Only show substantial content
                                    print(f"   UL {i+1}: {ul_text[:100]}...")
                            except:
                                continue
                except Exception as e:
                    print(f"   ❌ Error reading modal content: {e}")
            else:
                print("   ❌ Detail button not found")
            
            print("\n📊 Summary of waiting strategies:")
            print("   • Fixed timeout: Simple but inefficient")
            print("   • Element selector: Good for specific elements")
            print("   • Load state: Good for static pages")
            print("   • Function wait: Most flexible")
            print("   • Hybrid: Best for complex interactions")
            
            # Take a screenshot
            await page.screenshot(path="waiting_strategies_demo.png")
            print("\n📸 Screenshot saved as 'waiting_strategies_demo.png'")
            
            print("\n⏳ Browser will close in 10 seconds...")
            await asyncio.sleep(10)
            
        except Exception as e:
            print(f"❌ Error during demo: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(demo_waiting_strategies()) 