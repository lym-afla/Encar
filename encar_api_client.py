#!/usr/bin/env python3
"""
Encar API Client - Hybrid Approach
Extracts authentication from browser session and uses direct API calls
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from playwright.async_api import async_playwright
# Removed deprecated convert_manwon_to_won import

class EncarAPIClient:
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # API endpoints discovered from network analysis
        self.api_base = "https://api.encar.com"
        self.endpoints = {
            'general': f"{self.api_base}/search/car/list/general",
            'premium': f"{self.api_base}/search/car/list/premium"
        }
        
        # Authentication data
        self.session_cookies = {}
        self.session_headers = {}
        self.auth_valid_until = None
        
        # Session management
        self.http_session = None
        self.auth_browser = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.http_session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.http_session:
            await self.http_session.close()
        if self.auth_browser:
            await self.auth_browser.close()
    
    async def extract_authentication(self) -> bool:
        """Extract authentication tokens from browser session"""
        try:
            self.logger.info("Extracting authentication from browser session...")
            
            async with async_playwright() as p:
                # Launch browser in headless mode
                browser = await p.chromium.launch(
                    headless=self.config['browser']['headless']
                )
                
                context = await browser.new_context()
                page = await context.new_page()
                
                # Navigate to main search page to establish session
                search_url = self.build_search_url()
                self.logger.info(f"Navigating to: {search_url}")
                
                await page.goto(search_url)
                await page.wait_for_timeout(5000)  # Increased wait time
                
                # Try to find any car listings to confirm page loaded
                try:
                    await page.wait_for_selector('.listWrap, .list_wrap, [data-testid="car-list"], .itemWrap', timeout=15000)
                    self.logger.info("Search page loaded successfully")
                except:
                    self.logger.warning("Could not confirm page load, continuing...")
                    # Debug: check what's on the page
                    page_title = await page.title()
                    page_url = page.url
                    self.logger.info(f"   Page title: {page_title}")
                    self.logger.info(f"   Page URL: {page_url}")
                
                # Extract cookies
                cookies = await context.cookies()
                self.session_cookies = {cookie['name']: cookie['value'] for cookie in cookies}
                self.logger.info(f"Extracted {len(self.session_cookies)} cookies")
                
                # Build session headers
                self.session_headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'en-US,en;q=0.9,ko;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Referer': 'http://www.encar.com/',
                    'Origin': 'http://www.encar.com',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-site'
                }
                
                await browser.close()
                
                # Set auth validity
                self.auth_valid_until = datetime.now() + timedelta(hours=1)
                
                self.logger.info(f"Authentication extracted successfully")
                self.logger.info(f"   Cookies: {len(self.session_cookies)} items")
                self.logger.info(f"   Headers: {len(self.session_headers)} items")
                self.logger.info(f"   Valid until: {self.auth_valid_until}")
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to extract authentication: {e}")
            return False
    
    def build_search_url(self) -> str:
        """Build search URL for browser navigation"""
        # Use the actual working URL from our browser analysis
        # Navigate to the specific GLE search page
        return "http://www.encar.com/fc/fc_carsearchlist.do?carType=for#!%7B%22action%22%3A%22(And.Hidden.N._.(C.CarType.N._.(C.Manufacturer.%EB%B2%A4%EC%B8%A0._.ModelGroup.GLE-%ED%81%B4%EB%9E%98%EC%8A%A4.))_.Year.range(202100..)._.Price.range(..9000).)%22%2C%22toggle%22%3A%7B%7D%2C%22layer%22%3A%22%22%2C%22sort%22%3A%22ModifiedDate%22%2C%22page%22%3A1%2C%22limit%22%3A20%2C%22searchKey%22%3A%22%22%2C%22loginCheck%22%3Afalse%7D"
    
    def build_api_query(self, filters: dict = None) -> str:
        """Build API query string with advanced filtering support"""
        # Start with the base working query format - manufacturer and model
        base_part = "(And.Hidden.N._.(C.CarType.N._.(C.Manufacturer.벤츠._.ModelGroup.GLE-클래스.))"
        
        # If no filters, return the base query that we know works
        if not filters:
            return base_part + ")"
        
        # For filtered queries, add filters OUTSIDE the CarType clause 
        # Based on working URL format: (And.Hidden.N._.(C.CarType.N._.(C.Manufacturer.벤츠._.ModelGroup.GLE-클래스.))_.Year.range(202100..)._.Price.range(..9000).)
        
        # Build filter parts
        filter_parts = []
        
        # Year range filter
        if 'year_min' in filters or 'year_max' in filters:
            year_min = filters.get('year_min', '')
            year_max = filters.get('year_max', '')
            if year_min and year_max:
                filter_parts.append(f"Year.range({year_min}00..{year_max}99)")
            elif year_min:
                filter_parts.append(f"Year.range({year_min}00..)")
            elif year_max:
                filter_parts.append(f"Year.range(..{year_max}99)")
        
        # Price range filter (convert from millions to 만원 units)
        if 'price_min' in filters or 'price_max' in filters:
            price_min = filters.get('price_min', '')
            price_max = filters.get('price_max', '')
            
            # Convert from millions to 만원 units (e.g., 90M -> 9000만원)
            if price_min:
                price_min_manwon = int(float(price_min) * 100)
            if price_max:
                price_max_manwon = int(float(price_max) * 100)
            
            if price_min and price_max:
                filter_parts.append(f"Price.range({price_min_manwon}..{price_max_manwon})")
            elif price_min:
                filter_parts.append(f"Price.range({price_min_manwon}..)")
            elif price_max:
                filter_parts.append(f"Price.range(..{price_max_manwon})")
        
        # Mileage filter (in km)
        if 'mileage_max' in filters:
            mileage_max = filters['mileage_max']
            filter_parts.append(f"Mileage.range(..{mileage_max})")
        
        # Build the final query with filters outside
        if filter_parts:
            filter_str = "._.".join(filter_parts)
            query = f"{base_part}_.{filter_str}.)"
        else:
            query = base_part + ")"
        
        return query
    
    async def is_auth_valid(self) -> bool:
        """Check if current authentication is still valid"""
        if not self.auth_valid_until:
            return False
        return datetime.now() < self.auth_valid_until
    
    async def ensure_authenticated(self) -> bool:
        """Ensure we have valid authentication"""
        if await self.is_auth_valid():
            return True
        
        self.logger.info("Authentication expired, refreshing...")
        return await self.extract_authentication()
    
    async def make_api_request(self, endpoint: str, params: dict) -> Optional[dict]:
        """Make authenticated API request"""
        try:
            if not await self.ensure_authenticated():
                raise Exception("Failed to authenticate")
            
            # Prepare cookies for request
            cookie_string = '; '.join([f"{name}={value}" for name, value in self.session_cookies.items()])
            headers = self.session_headers.copy()
            headers['Cookie'] = cookie_string
            
            self.logger.info(f"API Request: {endpoint}")
            self.logger.info(f"   Parameters: {params}")
            
            async with self.http_session.get(
                endpoint,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                self.logger.info(f"   Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    self.logger.info(f"   Success! Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not dict'}")
                    return data
                elif response.status == 407:
                    self.logger.warning("Authentication failed (407), will refresh on next call")
                    self.auth_valid_until = None  # Force re-auth
                    return None
                else:
                    self.logger.error(f"API request failed: {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"API request error: {e}")
            return None
    
    async def get_listings(self, offset: int = 0, limit: int = 20, endpoint_type: str = 'general', filters: dict = None) -> Tuple[List[Dict], int]:
        """Get car listings from API with optional filtering"""
        if filters:
            return await self.get_listings_with_filters(filters, offset, limit)
        
        try:
            query = self.build_api_query()
            
            params = {
                'count': 'true',
                'q': query,
                'sr': f'|ModifiedDate|{offset}|{limit}'
            }
            
            endpoint = self.endpoints[endpoint_type]
            data = await self.make_api_request(endpoint, params)
            
            if not data:
                return [], 0
            
            total_count = data.get('Count', 0)
            search_results = data.get('SearchResults', [])
            
            # Convert API response to our format
            listings = []
            for item in search_results:
                listing = self.convert_api_item_to_listing(item)
                if listing:
                    listings.append(listing)
            
            self.logger.info(f"Retrieved {len(listings)} listings (page {offset//limit + 1})")
            return listings, total_count
            
        except Exception as e:
            self.logger.error(f"Error getting listings: {e}")
            return [], 0
    
    async def get_listings_with_filters(self, filters: dict = None, offset: int = 0, limit: int = 20) -> Tuple[List[Dict], int]:
        """Get car listings with advanced filtering"""
        try:
            query = self.build_api_query(filters)
            
            params = {
                'count': 'true',
                'q': query,
                'sr': f'|ModifiedDate|{offset}|{limit}'
            }
            
            endpoint = self.endpoints['general']
            data = await self.make_api_request(endpoint, params)
            
            if not data:
                return [], 0
            
            total_count = data.get('Count', 0)
            search_results = data.get('SearchResults', [])
            
            # Convert API response to our format
            listings = []
            for item in search_results:
                listing = self.convert_api_item_to_listing(item)
                if listing:
                    listings.append(listing)
            
            self.logger.info(f"Retrieved {len(listings)} filtered listings (page {offset//limit + 1})")
            return listings, total_count
            
        except Exception as e:
            self.logger.error(f"Error getting filtered listings: {e}")
            return [], 0
    
    def convert_api_item_to_listing(self, item: dict) -> Optional[dict]:
        """Convert API response item to our listing format with API-based lease detection"""
        try:
            # Extract basic info
            car_id = str(item.get('Id', ''))
            model = item.get('Model', '')
            badge = item.get('Badge', '')
            year = item.get('Year', '')
            price_manwon = item.get('Price', 0)  # API returns prices in 만원
            mileage = item.get('Mileage', 0)
            
            # Convert API prices from 만원 format to millions format
            # API returns 6290만원, we need to store as 62.9 million won
            price_millions = price_manwon / 100.0 if price_manwon else 0
            
            # Check if it's a coupe
            is_coupe = self.is_coupe_model(model, badge)
            
            # Build listing URL
            listing_url = f"https://fem.encar.com/cars/detail/{car_id}"
            
            # Build title
            title = f"{model} {badge}".strip()
            
            # API-based lease detection (heuristics)
            is_lease = self.detect_lease_vehicle(item)
            lease_info = None
            
            if is_lease:
                lease_info = self.extract_lease_info(item)
                # Convert lease prices from 만원 format to millions format
                if lease_info:
                    lease_info['deposit'] = lease_info.get('deposit', 0) / 100.0 if lease_info.get('deposit', 0) else 0
                    lease_info['monthly_payment'] = lease_info.get('monthly_payment', 0) / 100.0 if lease_info.get('monthly_payment', 0) else 0
                    lease_info['total_cost'] = lease_info.get('total_cost', 0) / 100.0 if lease_info.get('total_cost', 0) else 0
                    true_price = lease_info.get('total_cost', price_millions)
                else:
                    true_price = price_millions
            else:
                true_price = price_millions
            
            listing = {
                'car_id': car_id,
                'title': title,
                'listing_url': listing_url,
                'price': price_millions,  # Original listed price in millions
                'true_price': true_price,  # True cost in millions (higher for leases)
                'year': str(year),
                'mileage': mileage,
                'model': model,
                'badge': badge,
                'is_coupe': is_coupe,
                'is_lease': is_lease,  # Determined by API heuristics
                'lease_info': lease_info,  # Estimated from API (will be refined in Phase 2)
                'found_at': datetime.now().isoformat(),
                'api_source': True,
                
                # Additional API fields
                'manufacturer': item.get('Manufacturer', ''),
                'fuel_type': item.get('FuelType', ''),
                'transmission': item.get('Transmission', ''),
                'modified_date': item.get('ModifiedDate', ''),
                
                # Placeholders for fields we'll get separately
                'views': 0,
                'registration_date': None
            }
            
            return listing
            
        except Exception as e:
            self.logger.error(f"Error converting API item: {e}")
            return None
    
    def is_coupe_model(self, model: str, badge: str) -> bool:
        """Check if model is a coupe based on API data"""
        model_lower = model.lower()
        badge_lower = badge.lower()
        
        # Check for explicit coupe indicators
        coupe_keywords = ['쿠페', 'coupe']
        
        for keyword in coupe_keywords:
            if keyword in model_lower or keyword in badge_lower:
                return True
        
        return False
    
    def detect_lease_vehicle(self, item: dict) -> bool:
        """Detect if a vehicle is likely a lease - DISABLED for API phase"""
        # Disable lease detection during API phase - will be handled in Phase 2 with browser
        return False
    
    def extract_lease_info(self, item: dict) -> Optional[dict]:
        """Extract lease terms and calculate true total cost - DISABLED for API phase"""
        # Disable lease detection during API phase - will be handled in Phase 2 with browser
        return None
    
    async def get_raw_api_data(self, limit: int = 5) -> List[Dict]:
        """Get raw API data without conversion (for testing)"""
        try:
            query = self.build_api_query()
            
            params = {
                'count': 'true',
                'q': query,
                'sr': f'|ModifiedDate|0|{limit}'
            }
            
            endpoint = self.endpoints['general']
            data = await self.make_api_request(endpoint, params)
            
            if not data:
                return []
            
            return data.get('SearchResults', [])
            
        except Exception as e:
            self.logger.error(f"Error getting raw API data: {e}")
            return []
    
    async def get_total_count(self) -> int:
        """Get total count of available listings"""
        try:
            query = self.build_api_query()
            
            params = {
                'count': 'true',
                'q': query
            }
            
            data = await self.make_api_request(self.endpoints['general'], params)
            
            if data:
                return data.get('Count', 0)
            return 0
            
        except Exception as e:
            self.logger.error(f"Error getting total count: {e}")
            return 0
    
    async def get_multiple_pages(self, max_pages: int = 5, limit: int = 20) -> Tuple[List[Dict], int]:
        """Get multiple pages of listings efficiently"""
        all_listings = []
        total_count = 0
        
        for page in range(max_pages):
            offset = page * limit
            listings, count = await self.get_listings(offset=offset, limit=limit)
            
            if page == 0:  # Set total count from first page
                total_count = count
            
            if not listings:
                self.logger.warning(f"No listings found on page {page + 1}, stopping")
                break
                
            all_listings.extend(listings)
            
            # Check if we've reached the end
            if len(listings) < limit:
                self.logger.info(f"Reached end of listings at page {page + 1}")
                break
            
            # Small delay between requests to be respectful
            await asyncio.sleep(0.5)
        
        self.logger.info(f"Retrieved {len(all_listings)} listings from {max_pages} pages")
        return all_listings, total_count
    
    async def test_api_connectivity(self) -> bool:
        """Test if API is working properly"""
        try:
            self.logger.info("Testing API connectivity...")
            
            total_count = await self.get_total_count()
            if total_count > 0:
                self.logger.info(f"API working! Total vehicles: {total_count}")
                
                # Test getting first page
                listings, _ = await self.get_listings(limit=5)
                coupe_count = sum(1 for listing in listings if listing['is_coupe'])
                
                self.logger.info(f"Sample data: {len(listings)} listings, {coupe_count} coupes")
                return True
            else:
                self.logger.error("API test failed - no data returned")
                return False
                
        except Exception as e:
            self.logger.error(f"API test failed: {e}")
            return False


async def test_api_client():
    """Test the API client functionality"""
    print("Testing Encar API Client...")
    
    # Set up logging to see debug info
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s:%(name)s:%(message)s'
    )
    
    # Load config
    import yaml
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    async with EncarAPIClient(config) as client:
        # Test connectivity
        if await client.test_api_connectivity():
            print("API client test passed!")
            
            # Get sample data
            listings, total = await client.get_multiple_pages(max_pages=2)
            coupe_listings = [l for l in listings if l['is_coupe']]
            
            print(f"Results:")
            print(f"   Total available: {total}")
            print(f"   Retrieved: {len(listings)}")
            print(f"   Coupe models: {len(coupe_listings)}")
            
            if coupe_listings:
                print(f"\nSample Coupe:")
                sample = coupe_listings[0]
                print(f"   Title: {sample['title']}")
                print(f"   Year: {sample['year']}")
                print(f"   Price: {sample['price']:,}만원")
                print(f"   URL: {sample['listing_url']}")
        else:
            print("API client test failed")


if __name__ == "__main__":
    asyncio.run(test_api_client()) 