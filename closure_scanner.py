#!/usr/bin/env python3
"""
Closure Scanner
Scans existing listings to detect closed/withdrawn advertisements.
Integrates with the monitoring system to track listing lifecycle.
"""

import asyncio
import logging
import yaml
import sys
import os
from datetime import datetime, timedelta
from typing import Dict
from playwright.async_api import async_playwright

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_storage import EncarDatabase

class ClosureScanner:
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        # Use the same database path as the main monitor
        db_path = config.get('database', {}).get('filename', 'encar_listings.db')
        self.db = EncarDatabase(db_path)

        self.logger.info(f"Database path: {db_path}")
        
        # Test database connection and show basic stats
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM listings")
                total_count = cursor.fetchone()[0]
                self.logger.info(f"Database connected successfully. Total listings: {total_count}")
        except Exception as e:
            self.logger.error(f"Database connection test failed: {e}")
        
    async def check_listing_status(self, listing_url: str, car_id: str) -> Dict:
        """
        Check if a specific listing is still active or has been closed.
        
        Args:
            listing_url: URL of the listing to check
            car_id: Car ID for logging purposes
            
        Returns:
            Dict with status information: {
                'is_active': bool,
                'closure_type': str,  # if not active
                'error': str  # if error occurred
            }
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=self.config['browser']['headless']
                )
                
                context = await browser.new_context()
                page = await context.new_page()
                
                try:
                    # Navigate to the listing
                    response = await page.goto(listing_url, timeout=30000)
                    
                    if not response:
                        await browser.close()
                        return {
                            'is_active': False,
                            'closure_type': 'no_response',
                            'error': 'No response from server'
                        }
                    
                    status_code = response.status
                    
                    # Check for 404 or other error codes
                    if status_code == 404:
                        await browser.close()
                        return {
                            'is_active': False,
                            'closure_type': 'error_404',
                            'error': f'Page not found (404)'
                        }
                    elif status_code >= 400:
                        await browser.close()
                        return {
                            'is_active': False,
                            'closure_type': f'error_{status_code}',
                            'error': f'HTTP error {status_code}'
                        }
                    
                    # Wait for page to load
                    await page.wait_for_timeout(3000)
                    
                    # Get page title and content
                    page_title = await page.title()
                    page_url = page.url
                    
                    self.logger.debug(f"Checking {car_id}: {page_title}")
                    
                    # Check for various closure indicators
                    closure_indicators = await self.detect_closure_indicators(page)
                    
                    if closure_indicators['is_closed']:
                        await browser.close()
                        return {
                            'is_active': False,
                            'closure_type': closure_indicators['closure_type'],
                            'error': None
                        }
                    
                    # If no closure indicators found, listing is likely still active
                    await browser.close()
                    return {
                        'is_active': True,
                        'closure_type': None,
                        'error': None
                    }
                    
                except Exception as page_error:
                    await browser.close()
                    return {
                        'is_active': False,
                        'closure_type': 'access_error',
                        'error': str(page_error)
                    }
                    
        except Exception as e:
            self.logger.error(f"Error checking listing status for {car_id}: {e}")
            return {
                'is_active': False,
                'closure_type': 'check_error',
                'error': str(e)
            }
    
    async def detect_closure_indicators(self, page) -> Dict:
        """
        Detect various indicators that a listing has been closed.
        Uses precise detection based on actual closed page HTML structure.
        
        Returns:
            Dict with closure detection results
        """
        try:
            # Get page content and title
            content = await page.content()
            title = await page.title()
            
            self.logger.debug(f"Checking page title: {title[:100]}")
            
            # 1. Check for the specific "DetailNone" class structure (most reliable)
            # This is the exact structure from closed listing: car_id 39514996
            try:
                # Look for the specific closed listing div
                detail_none_selector = '.DetailNone_no_data__zLK\\+L, .DetailNone_no_data, [class*="DetailNone_no_data"]'
                detail_none_element = await page.query_selector(detail_none_selector)
                
                if detail_none_element:
                    detail_text = await detail_none_element.text_content()
                    if detail_text and '이 차량은 판매되었거나 삭제된 차량입니다' in detail_text:
                        return {
                            'is_closed': True,
                            'closure_type': 'confirmed_closed',
                            'indicator': 'DetailNone structure with closure message'
                        }
                
                # Also check for the broader DetailNone class patterns
                broad_selectors = [
                    '[class*="DetailNone"]',
                    '.DetailNone_text',
                    '[class*="no_data"]'
                ]
                
                for selector in broad_selectors:
                    element = await page.query_selector(selector)
                    if element:
                        element_text = await element.text_content()
                        if element_text and ('판매되었거나 삭제된' in element_text or '판매완료' in element_text):
                            return {
                                'is_closed': True,
                                'closure_type': 'confirmed_closed',
                                'indicator': f'Found closure message: {element_text[:50]}'
                            }
                            
            except Exception as e:
                self.logger.debug(f"Error checking DetailNone elements: {e}")
            
            # 2. Check for 404 or error page titles (very reliable)
            error_titles = [
                '404',
                'not found',
                'page not found',
                'error',
                '페이지를 찾을 수 없습니다',
                '존재하지 않는',
                '오류'
            ]
            
            title_lower = title.lower()
            for error_title in error_titles:
                if error_title in title_lower:
                    return {
                        'is_closed': True,
                        'closure_type': 'error_page',
                        'indicator': f'Error page title: {title}'
                    }
            
            # 3. Check for very specific closure messages in content (must be exact)
            specific_closure_messages = [
                '이 차량은 판매되었거나 삭제된 차량입니다',  # Exact message from example
                '차량정보가 존재하지 않습니다',  # Vehicle info doesn't exist
                '해당 매물을 찾을 수 없습니다',  # Cannot find this listing
                '삭제되었거나 존재하지 않는',  # Deleted or doesn't exist
                '판매가 완료된 차량',  # Sale completed vehicle
            ]
            
            for message in specific_closure_messages:
                if message in content:
                    return {
                        'is_closed': True,
                        'closure_type': 'confirmed_message',
                        'indicator': f'Found exact closure message: {message}'
                    }
            
            # 4. Check for error page elements (reliable)
            try:
                error_selectors = [
                    '.error-page',
                    '.not-found-page',
                    '[class*="error"]',
                    '[class*="notfound"]',
                    '[class*="404"]'
                ]
                
                for selector in error_selectors:
                    element = await page.query_selector(selector)
                    if element:
                        element_text = await element.text_content()
                        if element_text and len(element_text.strip()) > 10:  # Must have substantial content
                            return {
                                'is_closed': True,
                                'closure_type': 'error_element',
                                'indicator': f'Error element found: {element_text[:30]}'
                            }
                            
            except Exception as e:
                self.logger.debug(f"Error checking error elements: {e}")
            
            # 5. Check if we're on a completely different page (redirect detection)
            current_url = page.url
            if current_url and ('error' in current_url.lower() or '404' in current_url or 'notfound' in current_url):
                return {
                    'is_closed': True,
                    'closure_type': 'redirect_error',
                    'indicator': f'Redirected to error URL: {current_url}'
                }
            
            # If no clear closure indicators found, listing is likely still active
            return {
                'is_closed': False,
                'closure_type': None,
                'indicator': None
            }
            
        except Exception as e:
            self.logger.error(f"Error detecting closure indicators: {e}")
            return {
                'is_closed': False,
                'closure_type': None,
                'indicator': f'Detection error: {str(e)}'
            }
    
    async def scan_listings_for_closure(self, max_listings: int = None, max_age_days: int = 30) -> Dict:
        """
        Scan active listings to detect which ones have been closed.
        
        Args:
            max_listings: Maximum number of listings to check (None for all)
            max_age_days: Only check listings older than this many days
            
        Returns:
            Dict with scan results
        """
        try:
            self.logger.info(f"🔍 Starting closure scan...")
            
            # Get active listings from database
            active_listings = self.db.get_active_listings()
            
            if not active_listings:
                self.logger.info("No active listings found")
                return {
                    'total_checked': 0,
                    'closed_found': 0,
                    'errors': 0,
                    'still_active': 0
                }
            
            # Filter by age if specified (check listings that are AT LEAST max_age_days old)
            if max_age_days > 0:
                cutoff_date = datetime.now() - timedelta(days=max_age_days)
                filtered_listings = []
                self.logger.info(f"Filtering for listings at least {max_age_days} days old (before {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')})")
                
                for listing in active_listings:
                    try:
                        first_seen = datetime.fromisoformat(listing['first_seen'].replace('Z', '+00:00'))
                        days_old = (datetime.now() - first_seen).days
                        self.logger.debug(f"Listing {listing['car_id']}: first_seen={first_seen.strftime('%Y-%m-%d %H:%M:%S')}, days_old={days_old}")
                        
                        if first_seen <= cutoff_date:  # Changed from < to <=
                            filtered_listings.append(listing)
                            self.logger.debug(f"  -> Included (age: {days_old} days)")
                        else:
                            self.logger.debug(f"  -> Excluded (age: {days_old} days, too new)")
                    except Exception as e:
                        # If date parsing fails, include the listing
                        self.logger.warning(f"Date parsing failed for {listing['car_id']}: {e}, including anyway")
                        filtered_listings.append(listing)
                
                active_listings = filtered_listings
                self.logger.info(f"Filtered to {len(active_listings)} listings at least {max_age_days} days old")
            
            # Limit number of listings if specified
            if max_listings and len(active_listings) > max_listings:
                active_listings = active_listings[:max_listings]
                self.logger.info(f"Limited to {max_listings} listings for this scan")
            
            self.logger.info(f"Checking {len(active_listings)} active listings for closure...")
            
            # Show sample of listings being checked
            if active_listings:
                sample_size = min(3, len(active_listings))
                self.logger.info(f"Sample of listings to check:")
                for i, listing in enumerate(active_listings[:sample_size]):
                    self.logger.info(f"  {i+1}. {listing['car_id']} - {listing['title'][:50]}...")
                if len(active_listings) > sample_size:
                    self.logger.info(f"  ... and {len(active_listings) - sample_size} more")
            
            # Scan listings
            checked = 0
            closed_found = 0
            errors = 0
            still_active = 0
            
            for i, listing in enumerate(active_listings):
                car_id = listing['car_id']
                listing_url = listing['listing_url']
                
                self.logger.info(f"[{i+1}/{len(active_listings)}] Checking {car_id}...")
                
                # Check listing status
                status = await self.check_listing_status(listing_url, car_id)
                checked += 1
                
                if status['error']:
                    errors += 1
                    self.logger.warning(f"❌ Error checking {car_id}: {status['error']}")
                    
                    # Mark as closed if it's a clear error (404, etc.)
                    if status['closure_type'] in ['error_404', 'no_response']:
                        self.db.mark_listing_closed(car_id, status['closure_type'])
                        closed_found += 1
                        self.logger.info(f"🔒 Marked {car_id} as closed ({status['closure_type']})")
                    
                elif not status['is_active']:
                    closed_found += 1
                    self.db.mark_listing_closed(car_id, status['closure_type'])
                    self.logger.info(f"🔒 Marked {car_id} as closed ({status['closure_type']})")
                    
                else:
                    still_active += 1
                    self.logger.debug(f"✅ {car_id} still active")
                
                # Small delay between checks to be respectful
                await asyncio.sleep(2)
            
            results = {
                'total_checked': checked,
                'closed_found': closed_found,
                'errors': errors,
                'still_active': still_active
            }
            
            self.logger.info(f"📊 Closure scan completed:")
            self.logger.info(f"   - Total checked: {checked}")
            self.logger.info(f"   - Closed found: {closed_found}")
            self.logger.info(f"   - Errors: {errors}")
            self.logger.info(f"   - Still active: {still_active}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error during closure scan: {e}")
            return {
                'total_checked': 0,
                'closed_found': 0,
                'errors': 1,
                'still_active': 0,
                'error': str(e)
            }
    
    def get_closure_summary(self) -> Dict:
        """Get summary of closure detection statistics"""
        try:
            stats = self.db.get_closure_statistics()
            
            self.logger.info("📊 Closure Statistics:")
            for key, value in stats.items():
                self.logger.info(f"   {key}: {value}")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting closure summary: {e}")
            return {}
    
    async def run_closure_scan(self, max_listings: int = None, max_age_days: int = 7, show_stats: bool = True) -> Dict:
        """
        Run a complete closure scan process.
        
        Args:
            max_listings: Maximum number of listings to check
            max_age_days: Only check listings older than this many days
            show_stats: Whether to show statistics at the end
        """
        try:
            self.logger.info("🔍 Starting closure detection scan...")
            
            # Show initial statistics
            if show_stats:
                initial_stats = self.db.get_closure_statistics()
                self.logger.info("📊 Initial statistics:")
                for key, value in initial_stats.items():
                    self.logger.info(f"   {key}: {value}")
            
            # Run the scan
            results = await self.scan_listings_for_closure(max_listings, max_age_days)
            
            # Show final statistics
            if show_stats:
                final_stats = self.db.get_closure_statistics()
                self.logger.info("📊 Final statistics:")
                for key, value in final_stats.items():
                    self.logger.info(f"   {key}: {value}")
            
            return {
                'status': 'completed',
                'scan_results': results,
                'initial_stats': initial_stats if show_stats else None,
                'final_stats': final_stats if show_stats else None
            }
            
        except Exception as e:
            self.logger.error(f"Error running closure scan: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }


async def main():
    """Main function to run the closure scanner"""
    print("🔍 Encar Closure Scanner")
    print("=" * 50)
    print("Usage: python closure_scanner.py [options]")
    print("Options:")
    print("  --stats, -s           Show statistics only")
    print("  --max-listings N, -m N  Check maximum N listings")
    print("  --max-age N, --age N    Check listings at least N days old (default: 0 = all)")
    print("  --all, -a              Check all listings (same as --age 0)")
    print()
    
    # Check command line arguments
    stats_only = '--stats' in sys.argv or '-s' in sys.argv
    max_listings = None
    max_age_days = 0  # Changed default to 0 (check all listings)
    check_all = '--all' in sys.argv or '-a' in sys.argv
    
    # Parse arguments
    for i, arg in enumerate(sys.argv):
        if arg in ['--max-listings', '-m'] and i + 1 < len(sys.argv):
            try:
                max_listings = int(sys.argv[i + 1])
            except ValueError:
                print(f"❌ Invalid max_listings value: {sys.argv[i + 1]}")
                return
        elif arg in ['--max-age', '--age'] and i + 1 < len(sys.argv):
            try:
                max_age_days = int(sys.argv[i + 1])
            except ValueError:
                print(f"❌ Invalid max_age value: {sys.argv[i + 1]}")
                return
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('closure_scanner.log', encoding='utf-8')
        ]
    )
    
    # Load config
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return
    
    # Create scanner
    scanner = ClosureScanner(config)
    
    # Debug: Show database path being used
    db_path = config.get('database', {}).get('filename', 'encar_listings.db')
    print(f"📁 Using database: {db_path}")
    
    # Check if database file exists
    if os.path.exists(db_path):
        file_size = os.path.getsize(db_path)
        print(f"✅ Database file exists ({file_size:,} bytes)")
    else:
        print(f"❌ Database file not found: {db_path}")
        print("🔍 Looking for database files in current directory...")
        for file in os.listdir('.'):
            if file.endswith('.db'):
                print(f"   Found: {file}")
        return
    
    if stats_only:
        print("\n📊 Closure Statistics:")
        stats = scanner.get_closure_summary()
        return
    
    # Run the closure scan
    try:
        print(f"\n🔍 Running closure scan...")
        if max_listings:
            print(f"   - Max listings: {max_listings}")
        if max_age_days > 0:
            print(f"   - Max age: {max_age_days} days")
        else:
            print("   - Checking all listings (no age filter)")
        
        results = await scanner.run_closure_scan(
            max_listings=max_listings,
            max_age_days=max_age_days,
            show_stats=True
        )
        
        if results['status'] == 'completed':
            scan_results = results['scan_results']
            print(f"\n✅ Closure scan completed!")
            print(f"   - Total checked: {scan_results['total_checked']}")
            print(f"   - Closed found: {scan_results['closed_found']}")
            print(f"   - Errors: {scan_results['errors']}")
            print(f"   - Still active: {scan_results['still_active']}")
        else:
            print(f"\n❌ Closure scan failed: {results.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error during closure scan: {e}")
        logging.error(f"Closure scan error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
