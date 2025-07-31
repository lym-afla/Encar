#!/usr/bin/env python3
"""
Encar Scraper API - Fast API-based scraping
Uses the hybrid API client for fast and reliable data retrieval
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from playwright.async_api import async_playwright

# Import the API client from local file
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from encar_api_client import EncarAPIClient
from monetary_utils import extract_lease_components_from_page_content

class EncarScraperAPI:
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.api_client = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.api_client = EncarAPIClient(self.config)
        await self.api_client.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.api_client:
            await self.api_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def get_listings_from_page(self, page_num: int = 1, limit: int = 20) -> List[Dict]:
        """Get listings from a specific page using API"""
        try:
            offset = (page_num - 1) * limit
            listings, total_count = await self.api_client.get_listings(offset=offset, limit=limit)
            
            # Filter for coupe models only
            coupe_listings = [listing for listing in listings if listing['is_coupe']]
            
            self.logger.info(f"📄 Page {page_num}: {len(listings)} total, {len(coupe_listings)} coupes")
            return coupe_listings
            
        except Exception as e:
            self.logger.error(f"❌ Error getting page {page_num}: {e}")
            return []
    
    async def scrape_multiple_pages(self, max_pages: int = 5) -> List[Dict]:
        """Scrape multiple pages efficiently using API"""
        try:
            self.logger.info(f"Scraping up to {max_pages} pages...")
            
            # Get all listings at once using the API client's efficient method
            all_listings, total_count = await self.api_client.get_multiple_pages(
                max_pages=max_pages, 
                limit=20
            )
            
            # Filter for coupe models only
            coupe_listings = [listing for listing in all_listings if listing['is_coupe']]
            
            self.logger.info(f"Retrieved {len(all_listings)} total listings, {len(coupe_listings)} coupes")
            self.logger.info(f"Total available vehicles: {total_count}")
            
            return coupe_listings
            
        except Exception as e:
            self.logger.error(f"Error scraping multiple pages: {e}")
            return []
    
    async def scrape_with_filters(self, filters: dict, max_pages: int = 5) -> List[Dict]:
        """Scrape with specific filtering criteria"""
        try:
            self.logger.info(f"Scraping with filters: {filters}")
            
            all_listings = []
            total_count = 0
            
            for page in range(max_pages):
                offset = page * 20
                listings, count = await self.api_client.get_listings_with_filters(
                    filters=filters, 
                    offset=offset, 
                    limit=20
                )
                
                if page == 0:
                    total_count = count
                
                if not listings:
                    break
                    
                # Filter for coupe models only
                coupe_listings = [listing for listing in listings if listing['is_coupe']]
                all_listings.extend(coupe_listings)
                
                if len(listings) < 20:  # Last page
                    break
            
            self.logger.info(f"Filtered search returned {len(all_listings)} coupe listings from {total_count} total")
            return all_listings
            
        except Exception as e:
            self.logger.error(f"Error scraping with filters: {e}")
            return []
    
    async def get_quick_scan(self, pages: int = 3) -> List[Dict]:
        """Quick scan of first few pages for monitoring"""
        return await self.scrape_multiple_pages(max_pages=pages)
    
    async def get_total_available_count(self) -> int:
        """Get total count of available vehicles"""
        try:
            return await self.api_client.get_total_count()
        except Exception as e:
            self.logger.error(f"❌ Error getting total count: {e}")
            return 0
    
    # Enhanced detail extraction methods (using browser for views/registration when needed)
    async def get_views_and_registration_batch(self, listings: List[Dict]) -> List[Dict]:
        """Get views count and registration dates for a batch of listings"""
        enhanced_listings = []
        
        # Process all listings for enhanced data
        self.logger.info(f"🔍 Processing {len(listings)} listings for enhanced data")
        
        # Process in smaller batches to avoid overwhelming the system
        batch_size = 10
        total_processed = 0
        successful_extractions = 0
        
        for batch_start in range(0, len(listings), batch_size):
            batch_end = min(batch_start + batch_size, len(listings))
            batch_listings = listings[batch_start:batch_end]
            
            for i, listing in enumerate(batch_listings):
                try:
                    enhanced_listing = listing.copy()
                    
                    # Get detailed info using the correct URL key
                    listing_url = listing.get('listing_url')
                    if listing_url:
                        # Use efficient single-browser method to get views, registration, and lease terms
                        views, registration_date, lease_info = await self.get_views_and_registration_efficient(listing_url, listing)
                        
                        enhanced_listing['views'] = views
                        enhanced_listing['registration_date'] = registration_date or ''
                        
                        # Handle lease information - respect API-based detection
                        if lease_info:
                            # Browser confirmed lease terms - update with actual data
                            enhanced_listing['is_lease'] = True
                            enhanced_listing['lease_info'] = lease_info
                            enhanced_listing['true_price'] = lease_info.get('total_cost', listing.get('price', 0))
                            self.logger.info(f"✅ Browser confirmed lease terms: {listing.get('car_id')} - {lease_info}")
                        elif listing.get('is_lease', False):
                            # API flagged as lease but no terms found on page - keep API estimate
                            self.logger.debug(f"⚠️ API flagged lease but no terms found on page: {listing.get('car_id')}")
                            # Keep existing API-based lease_info and true_price
                        else:
                            # Not a lease vehicle
                            enhanced_listing['is_lease'] = False
                            enhanced_listing['lease_info'] = None
                            enhanced_listing['true_price'] = listing.get('price', 0)
                        
                        # Track successful extractions
                        if views > 0 or registration_date or lease_info:
                            successful_extractions += 1
                        
                        # Add freshness indicators based on views
                        if views > 0 and views <= 10:
                            enhanced_listing['freshness'] = 'very_fresh'
                        elif views > 0 and views <= 50:
                            enhanced_listing['freshness'] = 'fresh'
                        else:
                            enhanced_listing['freshness'] = 'normal'
                    else:
                        # Set defaults if no URL
                        enhanced_listing['views'] = 0
                        enhanced_listing['registration_date'] = ''
                        enhanced_listing['is_lease'] = False
                        enhanced_listing['lease_info'] = None
                    
                    enhanced_listings.append(enhanced_listing)
                    total_processed += 1
                    
                    # Progress reporting every 5 items
                    if total_processed % 5 == 0:
                        self.logger.info(f"📊 Processed {total_processed}/{len(listings)} listings, {successful_extractions} with extracted data")
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not enhance listing {total_processed + 1}: {e}")
                    # Add original listing with defaults
                    enhanced_listing = listing.copy()
                    enhanced_listing['views'] = 0
                    enhanced_listing['registration_date'] = ''
                    enhanced_listings.append(enhanced_listing)
                    total_processed += 1
            
            # Small delay between batches to be respectful
            if batch_end < len(listings):
                await asyncio.sleep(1)
        
        self.logger.info(f"✅ Enhanced data extraction complete: {successful_extractions}/{total_processed} successful")
        return enhanced_listings
    
    async def get_views_and_registration_efficient(self, listing_url: str, listing: dict) -> Tuple[int, Optional[str], Optional[dict]]:
        """Extract views count, registration date, and lease terms efficiently in single browser session"""
        browser = None
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Navigate to the page with better error handling
                try:
                    await page.goto(listing_url, wait_until='domcontentloaded', timeout=30000)
                    await page.wait_for_timeout(3000)
                except Exception as e:
                    self.logger.warning(f"Navigation timeout for {listing_url}: {e}")
                    return 0, None, None
                
                views = 0
                registration_date = None
                lease_info = None
                
                # First, try to get views from main page (faster)
                try:
                    main_info_ul = await page.query_selector('.DetailCarPhotoPc_info__0IA0t')
                    if main_info_ul:
                        li_elements = await main_info_ul.query_selector_all('li')
                        for li in li_elements:
                            li_text = await li.inner_text()
                            if "조회수" in li_text:
                                views_match = re.search(r'조회수\s+([\d,]+)', li_text)
                                if views_match:
                                    views_str = views_match.group(1).replace(',', '')
                                    views = int(views_str)
                                    self.logger.debug(f"Got views from main page: {views}")
                                break
                except Exception as e:
                    self.logger.debug(f"Could not get views from main page: {e}")
                
                # Open modal to get registration date (and views if not found above)
                detail_button = await page.wait_for_selector('.DetailSummary_btn_detail__msm-h', timeout=10000)
                if detail_button:
                    await detail_button.click()
                    await page.wait_for_timeout(3000)
                    
                    # Try to find modal container - be more flexible with selectors
                    modal_ul = None
                    try:
                        # First try the specific modal container
                        modal_ul = await page.wait_for_selector('.DetailSpec_list_default__Gx+ZA', timeout=3000)
                    except:
                        # Fallback: look for any list in the modal
                        try:
                            modal_ul = await page.wait_for_selector('.BottomSheet-module_inner_contents__-vTmf ul', timeout=2000)
                        except:
                            # Last resort: search all li elements in modal area
                            pass
                    
                    # Get views from modal if not found on main page
                    if views == 0:
                        li_elements = []
                        if modal_ul:
                            li_elements = await modal_ul.query_selector_all('li')
                        else:
                            # Fallback: search all li elements in modal
                            li_elements = await page.query_selector_all('.BottomSheet-module_inner_contents__-vTmf li')
                        
                        for li_element in li_elements:
                            try:
                                li_text = await li_element.inner_text()
                                if "조회수" in li_text:
                                    views_span = await li_element.query_selector('.DetailSpec_txt__NGapF')
                                    if views_span:
                                        views_text = await views_span.inner_text()
                                        views_match = re.search(r'([\d,]+)', views_text)
                                        if views_match:
                                            views_str = views_match.group(1).replace(',', '')
                                            views = int(views_str)
                                            self.logger.debug(f"Got views from modal: {views}")
                                    break
                            except Exception as inner_e:
                                continue
                    
                    # Get registration date by clicking the question mark button
                    try:
                        question_button = await page.wait_for_selector('button:has-text("조회수 자세히보기")', timeout=5000)
                        if question_button:
                            await question_button.click()
                            await page.wait_for_timeout(2000)
                            
                            # Extract registration date from tooltip
                            tooltip_element = await page.wait_for_selector('.TooltipPopper_area__iKVzy', timeout=5000)
                            if tooltip_element:
                                tooltip_text = await tooltip_element.inner_text()
                                date_match = re.search(r'최초등록일\s*(\d{4}/\d{2}/\d{2})', tooltip_text)
                                if date_match:
                                    registration_date = date_match.group(1)
                                    self.logger.debug(f"Got registration date: {registration_date}")
                    except Exception as e:
                        self.logger.debug(f"Could not get registration date: {e}")
                
                # Extract lease terms only if this was flagged as a lease vehicle by API
                lease_info = None
                if listing.get('is_lease', False):
                    self.logger.debug(f"Extracting lease terms for flagged lease vehicle")
                    lease_info = await self.extract_lease_terms_from_page(page)
                    if lease_info:
                        self.logger.info(f"✅ Extracted actual lease terms: {lease_info}")
                    else:
                        self.logger.debug(f"⚠️ No lease terms found on page for flagged lease vehicle")
                
                return views, registration_date, lease_info
                
        except Exception as e:
            self.logger.warning(f"⚠️ Could not extract views/registration: {e}")
            return 0, None, None
        finally:
            if browser:
                try:
                    await browser.close()
                except:
                    pass
    
    async def extract_lease_terms_from_page(self, page) -> Optional[dict]:
        """Extract lease terms from vehicle detail page"""
        try:
            # Check if this is a lease vehicle by looking for lease keywords
            page_content = await page.content()
            lease_keywords = ["리스", "렌트", "월 납입금", "보증금", "리스료", "월리스", "리스기간", "월 렌트비", "렌트료"]
            
            is_lease = any(keyword in page_content for keyword in lease_keywords)
            if not is_lease:
                return None
            
            self.logger.info("🔍 Lease vehicle detected, extracting terms...")
            
            # Use the new monetary utilities to extract lease components
            lease_info = extract_lease_components_from_page_content(page_content)
            
            # Only return if we found meaningful lease data
            if lease_info['deposit'] > 0 or lease_info['monthly_payment'] > 0:
                self.logger.info(f"✅ Lease terms extracted: {lease_info}")
                return lease_info
            else:
                self.logger.debug("❌ No meaningful lease terms found")
                return None
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error extracting lease terms: {e}")
            return None
    
    async def get_views_count(self, listing_url: str) -> int:
        """Extract views count (legacy method, use get_views_and_registration_efficient for better performance)"""
        # Create dummy listing for legacy compatibility
        dummy_listing = {'is_lease': False}
        views, _, _ = await self.get_views_and_registration_efficient(listing_url, dummy_listing)
        return views
    
    async def get_registration_date(self, listing_url: str) -> Optional[str]:
        """Extract registration date (legacy method, use get_views_and_registration_efficient for better performance)"""
        # Create dummy listing for legacy compatibility
        dummy_listing = {'is_lease': False}
        _, registration_date, _ = await self.get_views_and_registration_efficient(listing_url, dummy_listing)
        return registration_date
    
    def filter_listings(self, listings: List[Dict]) -> List[Dict]:
        """Apply additional filtering criteria"""
        filtered = []
        filter_config = self.config['filters']
        
        for listing in listings:
            # Coupe filter already applied in API client
            if not listing.get('is_coupe', False):
                continue
                
            # Exclude keywords filter
            title_lower = listing['title'].lower()
            if any(keyword in title_lower for keyword in filter_config['exclude_keywords']):
                continue
                
            filtered.append(listing)
        
        return filtered

    # API Testing and Diagnostics
    async def test_api_connectivity(self) -> bool:
        """Test if API client is working"""
        try:
            return await self.api_client.test_api_connectivity()
        except Exception as e:
            self.logger.error(f"❌ API connectivity test failed: {e}")
            return False
    
    async def get_api_status(self) -> Dict:
        """Get API status information"""
        try:
            total_count = await self.get_total_available_count()
            sample_listings, _ = await self.api_client.get_listings(limit=5)
            coupe_count = sum(1 for l in sample_listings if l['is_coupe'])
            
            return {
                'api_working': True,
                'total_vehicles': total_count,
                'sample_listings': len(sample_listings),
                'sample_coupes': coupe_count,
                'auth_valid': await self.api_client.is_auth_valid()
            }
        except Exception as e:
            self.logger.error(f"❌ Error getting API status: {e}")
            return {
                'api_working': False,
                'error': str(e)
            }


async def test_api_scraper():
    """Test the API-based scraper"""
    print("🧪 Testing API-based Encar Scraper...")
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
    
    # Load config
    import yaml
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    async with EncarScraperAPI(config) as scraper:
        # Test API connectivity
        print("\n🔗 Testing API connectivity...")
        if await scraper.test_api_connectivity():
            print("✅ API connectivity test passed!")
        else:
            print("❌ API connectivity test failed!")
            return
        
        # Get API status
        print("\n📊 Getting API status...")
        status = await scraper.get_api_status()
        print(f"   API working: {status['api_working']}")
        print(f"   Total vehicles: {status.get('total_vehicles', 'N/A')}")
        print(f"   Auth valid: {status.get('auth_valid', 'N/A')}")
        
        # Test quick scan
        print("\n⚡ Testing quick scan (3 pages)...")
        quick_results = await scraper.get_quick_scan(pages=3)
        print(f"   Found: {len(quick_results)} coupe listings")
        
        if quick_results:
            # Show sample
            sample = quick_results[0]
            print(f"\n🚗 Sample listing:")
            print(f"   Title: {sample['title']}")
            print(f"   Year: {sample['year']}")
            print(f"   Price: {sample['price']:,}만원")
            print(f"   URL: {sample['listing_url']}")
            
            # Test enhanced data for first listing
            print("\n🔍 Testing enhanced data extraction...")
            enhanced = await scraper.get_views_and_registration_batch([sample])
            if enhanced and enhanced[0].get('views') is not None:
                print(f"   Views: {enhanced[0]['views']}")
                print(f"   Registration: {enhanced[0].get('registration_date', 'N/A')}")
                print(f"   Freshness: {enhanced[0].get('freshness', 'normal')}")
            else:
                print("   ⚠️ Enhanced data extraction may need adjustment")
        
        print("\n✅ API scraper test completed!")


if __name__ == "__main__":
    asyncio.run(test_api_scraper()) 