#!/usr/bin/env python3
"""
DEPRECATED: Legacy browser-based scraper
This module is deprecated and will be removed in future versions.
Use encar_scraper_api.py for API-based scraping instead.

Encar Mercedes-Benz GLE Coupe Scraper
Scrapes car listings from Encar.com using browser automation.
"""

import warnings
warnings.warn(
    "encar_scraper.py is deprecated. Use encar_scraper_api.py for API-based scraping.",
    DeprecationWarning,
    stacklevel=2
)

import asyncio
import re
import logging
import time
from typing import List, Dict, Optional
from urllib.parse import quote
from playwright.async_api import async_playwright
import yaml

class EncarScraper:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the Encar scraper with configuration."""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.browser = None
        self.page = None
        
    async def start_browser(self):
        """Start the browser session."""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.config['browser']['headless']
            )
            self.page = await self.browser.new_page()
            
            # Set reasonable timeouts
            self.page.set_default_timeout(self.config['browser']['timeout'] * 1000)
            
            logging.info("Browser started successfully")
            
        except Exception as e:
            logging.error(f"Error starting browser: {e}")
            raise
    
    async def close_browser(self):
        """Clean up browser resources."""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
                
        except Exception as e:
            logging.error(f"Error closing browser: {e}")
    
    def build_search_url(self, page_num: int = 1) -> str:
        """Build the search URL with filters."""
        search_config = self.config['search']
        
        # URL encode the Korean characters
        manufacturer = quote(search_config['manufacturer'])
        model_group = quote(search_config['model_group'])
        
        # Build the filter JSON
        filter_json = {
            "action": f"(And.Hidden.N._.(C.CarType.N._.(C.Manufacturer.{search_config['manufacturer']}._.ModelGroup.{search_config['model_group']}))_.Year.range({search_config['year_range']})._.Price.range({search_config['price_range']}).))",
            "toggle": {},
            "layer": "",
            "sort": search_config['sort'],
            "page": page_num,
            "limit": search_config['limit'],
            "searchKey": "",
            "loginCheck": False
        }
        
        # Convert to URL-encoded JSON
        import json
        filter_string = quote(json.dumps(filter_json, ensure_ascii=False))
        
        url = f"{search_config['base_url']}?carType={search_config['car_type']}#!{filter_string}"
        return url
    
    async def get_listings_from_page(self, page_num: int = 1) -> List[Dict]:
        """Extract car listings from a search results page."""
        try:
            url = self.build_search_url(page_num)
            logging.info(f"Scraping page {page_num}: {url}")
            
            await self.page.goto(url)
            await self.page.wait_for_timeout(self.config['browser']['wait_time'] * 1000)
            
            # Wait for the car listings to load
            await self.page.wait_for_selector('.listWrap .itemWrap', timeout=10000)
            
            # Extract listing elements
            listings = []
            listing_elements = await self.page.query_selector_all('.listWrap .itemWrap')
            
            for element in listing_elements:
                try:
                    listing_data = await self.extract_listing_data(element)
                    if listing_data:
                        listings.append(listing_data)
                        
                except Exception as e:
                    logging.warning(f"Error extracting listing data: {e}")
                    continue
            
            logging.info(f"Found {len(listings)} listings on page {page_num}")
            return listings
            
        except Exception as e:
            logging.error(f"Error scraping page {page_num}: {e}")
            return []
    
    async def extract_listing_data(self, element) -> Optional[Dict]:
        """Extract data from a single car listing element."""
        try:
            # Get the link and car ID
            link_element = await element.query_selector('a')
            if not link_element:
                return None
                
            listing_url = await link_element.get_attribute('href')
            if not listing_url:
                return None
            
            # Extract car_id from URL
            car_id_match = re.search(r'carid=(\d+)', listing_url)
            if not car_id_match:
                return None
            car_id = car_id_match.group(1)
            
            # Get title/model information
            title_element = await element.query_selector('.carName')
            title = await title_element.inner_text() if title_element else ""
            
            # Check if it's a coupe
            is_coupe = "쿠페" in title
            
            # Filter based on coupe requirement
            if not is_coupe:
                return None
            
            # Extract year from title (e.g., "21년" means 2021)
            year_match = re.search(r'(\d{2})년', title)
            year = None
            if year_match:
                year_short = int(year_match.group(1))
                year = 2000 + year_short if year_short >= 21 else 1900 + year_short
            
            # Extract price
            price_element = await element.query_selector('.carPrice')
            price = await price_element.inner_text() if price_element else ""
            
            # Extract mileage
            mileage_element = await element.query_selector('.carMileage')
            mileage = await mileage_element.inner_text() if mileage_element else ""
            
            # Get views count - this might be on the detail page
            views = await self.get_views_count(listing_url)
            
            # Get registration date from tooltip
            registration_date = await self.get_registration_date(listing_url)
            
            listing_data = {
                'car_id': car_id,
                'title': title.strip(),
                'model': title.strip(),
                'year': year,
                'price': price.strip(),
                'mileage': mileage.strip(),
                'views': views,
                'registration_date': registration_date,
                'listing_url': listing_url,
                'is_coupe': is_coupe,
                'scraped_at': time.time()
            }
            
            return listing_data
            
        except Exception as e:
            logging.error(f"Error extracting listing data: {e}")
            return None
    
    async def get_views_count(self, listing_url: str) -> int:
        """Extract views count from the detail page modal."""
        try:
            # Open detail page in new tab
            detail_page = await self.browser.new_page()
            await detail_page.goto(listing_url)
            await detail_page.wait_for_timeout(2000)
            
            # Click the detail button to open modal
            detail_button = await detail_page.query_selector('.DetailSummary_btn_detail__msm-h')
            if detail_button:
                await detail_button.click()
                await detail_page.wait_for_timeout(2000)
                
                # Find the specific <li> element that contains "조회수" (Views)
                view_li_elements = await detail_page.query_selector_all('li')
                
                for li_element in view_li_elements:
                    li_text = await li_element.inner_text()
                    if "조회수" in li_text:
                        # Found the views <li>, now extract the number from DetailSpec_txt__NGapF span
                        views_span = await li_element.query_selector('.DetailSpec_txt__NGapF')
                        if views_span:
                            views_text = await views_span.inner_text()
                            # Extract number from text like "1,029"
                            views_match = re.search(r'([\d,]+)', views_text)
                            if views_match:
                                views_str = views_match.group(1).replace(',', '')
                                await detail_page.close()
                                return int(views_str)
                        break
            
            await detail_page.close()
            return 0
            
        except Exception as e:
            logging.error(f"Error getting views count: {e}")
            return 0
    
    async def get_registration_date(self, listing_url: str) -> Optional[str]:
        """Extract registration date from tooltip on detail page."""
        try:
            # Open detail page in new tab
            detail_page = await self.browser.new_page()
            await detail_page.goto(listing_url)
            await detail_page.wait_for_timeout(3000)
            
            # Click the detail button to open modal
            detail_button = await detail_page.query_selector('.DetailSummary_btn_detail__msm-h')
            if detail_button:
                await detail_button.click()
                await detail_page.wait_for_timeout(2000)
                
                # Wait for dynamic content to load
                await detail_page.wait_for_timeout(1000)
                
                # Look for the specific question mark button with "조회수 자세히보기" text
                question_button = await detail_page.query_selector('button:has-text("조회수 자세히보기")')
                if question_button:
                    await question_button.click()
                    await detail_page.wait_for_timeout(1500)
                    
                    # Now look for the tooltip with registration date
                    tooltip_element = await detail_page.query_selector('.TooltipPopper_area__iKVzy')
                    if tooltip_element:
                        tooltip_text = await tooltip_element.inner_text()
                        
                        # Look for pattern like "최초등록일 2025/06/24"
                        date_match = re.search(r'최초등록일\s*(\d{4}/\d{2}/\d{2})', tooltip_text)
                        if date_match:
                            registration_date = date_match.group(1)
                            await detail_page.close()
                            return registration_date
            
            await detail_page.close()
            return None
            
        except Exception as e:
            logging.error(f"Error getting registration date: {e}")
            return None
    
    def filter_listings(self, listings: List[Dict]) -> List[Dict]:
        """Apply filtering criteria to listings using the new architecture."""
        filtered = []
        filter_config = self.config['filters']
        
        for listing in listings:
            # Check if it's a coupe (already filtered in extraction)
            if not listing.get('is_coupe', False):
                continue
                
            # Check for exclude keywords
            title_lower = listing['title'].lower()
            if any(keyword in title_lower for keyword in filter_config['exclude_keywords']):
                continue
                
            # All coupe listings pass basic filtering
            # The "new" determination is now done in the database layer
            filtered.append(listing)
        
        return filtered
    
    async def scrape_multiple_pages(self, max_pages: int = 5, is_initial_population: bool = False) -> List[Dict]:
        """Scrape multiple pages of search results."""
        all_listings = []
        
        try:
            await self.start_browser()
            
            # Use more pages for initial population
            if is_initial_population:
                max_pages = self.config['monitoring'].get('initial_population_pages', 20)
                logging.info(f"Initial population mode: scanning {max_pages} pages")
            
            for page_num in range(1, max_pages + 1):
                try:
                    page_listings = await self.get_listings_from_page(page_num)
                    if not page_listings:
                        logging.info(f"No listings found on page {page_num}, stopping scan")
                        break
                        
                    filtered_listings = self.filter_listings(page_listings)
                    all_listings.extend(filtered_listings)
                    
                    logging.info(f"Page {page_num}: {len(filtered_listings)} coupe listings found")
                    
                    # Add delay between pages to be respectful
                    delay = self.config['browser'].get('delay_between_requests', 2)
                    await asyncio.sleep(delay)
                    
                except Exception as e:
                    logging.error(f"Error scraping page {page_num}: {e}")
                    continue
            
            logging.info(f"Total listings found: {len(all_listings)}")
            return all_listings
            
        finally:
            await self.close_browser()
    
    async def scrape_with_details(self, max_pages: int = 5, is_initial_population: bool = False) -> List[Dict]:
        """
        Scrape listings and get detailed information including registration dates.
        This is slower but gets complete data.
        """
        all_listings = []
        
        try:
            await self.start_browser()
            
            # Use more pages for initial population
            if is_initial_population:
                max_pages = self.config['monitoring'].get('initial_population_pages', 20)
                logging.info(f"Initial population mode: scanning {max_pages} pages with full details")
            
            for page_num in range(1, max_pages + 1):
                try:
                    page_listings = await self.get_listings_from_page(page_num)
                    if not page_listings:
                        logging.info(f"No listings found on page {page_num}, stopping scan")
                        break
                        
                    filtered_listings = self.filter_listings(page_listings)
                    
                    # Get detailed info for each listing (including registration date)
                    detailed_listings = []
                    for listing in filtered_listings:
                        try:
                            # The views and registration date are already extracted in extract_listing_data
                            # but we could enhance this further if needed
                            detailed_listings.append(listing)
                            
                            # Small delay between detail requests
                            delay = self.config['browser'].get('delay_between_details', 1)
                            await asyncio.sleep(delay)
                            
                        except Exception as e:
                            logging.warning(f"Error getting details for listing {listing.get('car_id', 'unknown')}: {e}")
                            # Still include the listing without full details
                            detailed_listings.append(listing)
                    
                    all_listings.extend(detailed_listings)
                    logging.info(f"Page {page_num}: {len(detailed_listings)} detailed coupe listings processed")
                    
                    # Add delay between pages
                    delay = self.config['browser'].get('delay_between_requests', 2)
                    await asyncio.sleep(delay)
                    
                except Exception as e:
                    logging.error(f"Error scraping page {page_num}: {e}")
                    continue
            
            logging.info(f"Total detailed listings found: {len(all_listings)}")
            return all_listings
            
        finally:
            await self.close_browser()
    
    async def get_quick_scan(self) -> List[Dict]:
        """Quick scan of just the first page for new listings."""
        try:
            await self.start_browser()
            listings = await self.get_listings_from_page(1)
            filtered_listings = self.filter_listings(listings)
            
            return filtered_listings
            
        finally:
            await self.close_browser()

# Enhanced utility functions
async def run_initial_population():
    """Run initial database population with detailed scraping."""
    scraper = EncarScraper()
    return await scraper.scrape_with_details(is_initial_population=True)

async def run_regular_scan(max_pages: int = 10):
    """Run regular monitoring scan."""
    scraper = EncarScraper()
    return await scraper.scrape_multiple_pages(max_pages)

async def run_detailed_scan(max_pages: int = 5):
    """Run detailed scan with registration dates."""
    scraper = EncarScraper()
    return await scraper.scrape_with_details(max_pages)

# Utility functions for running the scraper
async def run_scraper_async():
    """Async wrapper for running the scraper."""
    scraper = EncarScraper()
    return await scraper.scrape_multiple_pages()

def run_scraper():
    """Synchronous wrapper for running the scraper."""
    return asyncio.run(run_scraper_async())

if __name__ == "__main__":
    # Test the scraper
    logging.basicConfig(level=logging.INFO)
    listings = run_scraper()
    print(f"Found {len(listings)} coupe listings")
    for listing in listings[:3]:  # Show first 3
        print(f"- {listing['title']} (Views: {listing['views']}, Reg: {listing['registration_date']})")