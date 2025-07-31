#!/usr/bin/env python3
"""
Utility functions for the Encar monitoring system.
"""

import asyncio
import logging
import yaml
from datetime import datetime
from typing import Dict, List
from playwright.async_api import async_playwright

def load_config(config_path: str = "config.yaml") -> Dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return {}

def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Set up logging configuration."""
    handlers = [logging.StreamHandler()]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

async def test_tooltip_extraction(url: str = None):
    """Test the tooltip extraction functionality on a specific URL."""
    import re  # Move import to the top
    
    if not url:
        # Use the example URL provided by the user
        url = "https://fem.encar.com/cars/detail/39936778?pageid=fc_carsearch&listAdvType=word&carid=39936778&view_type=hs_ad&wtClick_forList=017&advClickPosition=imp_word_p1_g2"
    
    print(f"🧪 Testing tooltip extraction on: {url}")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Non-headless for debugging
            page = await browser.new_page()
            
            print("📖 Loading page...")
            await page.goto(url)
            await page.wait_for_timeout(3000)
            
            # Look for the detail button that opens the modal
            print("🔍 Looking for detail button...")
            detail_button = await page.query_selector('.DetailSummary_btn_detail__msm-h')
            
            if detail_button:
                print("✅ Found detail button, clicking...")
                await detail_button.click()
                await page.wait_for_timeout(3000)  # Wait longer for dynamic content
                
                print("🔍 Looking for views count in modal...")
                # Find the specific <li> element that contains "조회수" (Views)
                view_li_elements = await page.query_selector_all('li')
                views_found = False
                
                for li_element in view_li_elements:
                    li_text = await li_element.inner_text()
                    if "조회수" in li_text:
                        print(f"✅ Found views <li> element: {li_text}")
                        views_found = True
                        
                        # Debug: show the HTML structure of this <li>
                        li_html = await li_element.inner_html()
                        print(f"🐛 Views <li> HTML: {li_html}")
                        
                        # Extract views count from this specific <li>
                        views_span = await li_element.query_selector('.DetailSpec_txt__NGapF')
                        if views_span:
                            views_text = await views_span.inner_text()
                            print(f"📊 Views text: {views_text}")
                            
                            # Extract number from text like "1,029"
                            views_match = re.search(r'([\d,]+)', views_text)
                            if views_match:
                                views_str = views_match.group(1).replace(',', '')
                                print(f"✅ Views count: {views_str}")
                        break
                
                # Wait a bit more for dynamic content to load
                print("⏳ Waiting for dynamic content to load...")
                await page.wait_for_timeout(2000)
                
                # Look for the specific question mark button with "조회수 자세히보기" text
                print("🔍 Looking for views detail button...")
                question_button = await page.query_selector('button:has-text("조회수 자세히보기")')
                
                if question_button:
                    print("✅ Found question mark button, clicking...")
                    await question_button.click()
                    await page.wait_for_timeout(2000)
                    
                    # Look for tooltip content with registration date
                    print("🔍 Looking for tooltip...")
                    tooltip_element = await page.query_selector('.TooltipPopper_area__iKVzy')
                    
                    if tooltip_element:
                        tooltip_text = await tooltip_element.inner_text()
                        print(f"📋 Tooltip content: {tooltip_text}")
                        
                        # Look for pattern like "최초등록일 2025/06/24"
                        date_match = re.search(r'최초등록일\s*(\d{4}/\d{2}/\d{2})', tooltip_text)
                        if date_match:
                            registration_date = date_match.group(1)
                            print(f"✅ Found registration date: {registration_date}")
                        else:
                            print("❌ Registration date pattern not found in tooltip")
                    else:
                        print("❌ Tooltip not found after clicking question mark")
                else:
                    print("❌ Question mark button not found")
                
                if not views_found:
                    print("❌ Views <li> element not found in modal")
            else:
                print("❌ Detail button not found")
            
            await browser.close()
            print("✅ Test completed!")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")

def create_test_listing() -> Dict:
    """Create a test listing for testing notifications."""
    return {
        'car_id': f'TEST_{int(datetime.now().timestamp())}',
        'title': 'GLE400d 4MATIC 쿠페 TEST LISTING',
        'year': 2024,
        'price': '6,500만원',
        'mileage': '12,000km',
        'views': 3,
        'registration_date': '2024/12/01',
        'listing_url': 'http://test.encar.com/test',
        'is_coupe': True,
        'scraped_at': datetime.now().timestamp()
    }

def format_korean_number(number: int) -> str:
    """Format number in Korean style (with commas)."""
    return f"{number:,}"

def parse_korean_price(price_str: str) -> float:
    """Parse Korean price string to float (in 만원 units)."""
    try:
        # Remove non-numeric characters except for decimal point
        import re
        numeric = re.sub(r'[^\d.]', '', price_str)
        return float(numeric) if numeric else 0.0
    except:
        return 0.0

def parse_korean_mileage(mileage_str: str) -> int:
    """Parse Korean mileage string to integer."""
    try:
        # Extract number and convert km to integer
        import re
        numeric = re.sub(r'[^\d]', '', mileage_str)
        return int(numeric) if numeric else 0
    except:
        return 0

def is_new_listing(views: int, threshold: int = 50) -> bool:
    """Check if a listing is considered 'new' based on view count."""
    return views <= threshold

def validate_config(config: Dict) -> List[str]:
    """Validate configuration and return list of errors."""
    errors = []
    
    required_sections = ['search', 'filters', 'monitoring', 'database', 'notifications', 'browser']
    for section in required_sections:
        if section not in config:
            errors.append(f"Missing required section: {section}")
    
    # Validate search section
    if 'search' in config:
        search = config['search']
        required_search_fields = ['base_url', 'manufacturer', 'model_group']
        for field in required_search_fields:
            if field not in search:
                errors.append(f"Missing required search field: {field}")
    
    # Validate monitoring settings
    if 'monitoring' in config:
        monitoring = config['monitoring']
        if monitoring.get('check_interval_minutes', 0) < 1:
            errors.append("check_interval_minutes must be at least 1")
    
    return errors

def print_system_info():
    """Print system information and status."""
    import sys
    import platform
    
    print(f"\n🖥️  SYSTEM INFORMATION")
    print(f"{'='*40}")
    print(f"Python Version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Processor: {platform.processor()}")
    print(f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*40}\n")

async def test_browser_functionality():
    """Test basic browser functionality."""
    print("🧪 Testing browser functionality...")
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Test basic navigation
            await page.goto("https://www.google.com")
            title = await page.title()
            print(f"✅ Browser test successful - Page title: {title}")
            
            await browser.close()
            return True
            
    except Exception as e:
        print(f"❌ Browser test failed: {e}")
        return False

# CLI utility functions
def run_tooltip_test():
    """Run tooltip extraction test from command line."""
    asyncio.run(test_tooltip_extraction())

def run_browser_test():
    """Run browser functionality test from command line."""
    asyncio.run(test_browser_functionality())

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Encar Monitoring Utilities')
    parser.add_argument('--test', choices=['tooltip', 'browser', 'all'], 
                       help='Run specific tests')
    parser.add_argument('--url', help='URL for tooltip test')
    parser.add_argument('--info', action='store_true', help='Show system info')
    
    args = parser.parse_args()
    
    if args.info:
        print_system_info()
    
    if args.test:
        if args.test in ['tooltip', 'all']:
            if args.url:
                asyncio.run(test_tooltip_extraction(args.url))
            else:
                run_tooltip_test()
        
        if args.test in ['browser', 'all']:
            run_browser_test()
    
    if not args.test and not args.info:
        print("Use --help to see available options")
        print_system_info()