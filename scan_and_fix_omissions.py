#!/usr/bin/env python3
"""
Scan and Fix Omissions Script
Scans the existing database for listings missing views, registration dates, or lease information
and processes them using the enhanced extraction methods.
"""

import asyncio
import logging
import yaml
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from encar_scraper_api import EncarScraperAPI
from data_storage import EncarDatabase

class OmissionScanner:
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.db = EncarDatabase()
        
    def scan_for_omissions(self) -> List[Dict]:
        """Scan database for listings with missing data"""
        try:
            # Connect to database
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            # Query for listings with missing data
            query = """
            SELECT 
                car_id,
                title,
                listing_url,
                views,
                registration_date,
                is_lease,
                lease_deposit,
                lease_monthly_payment,
                lease_term_months,
                first_seen,
                last_updated
            FROM listings 
            WHERE 
                (views IS NULL OR views = 0) OR
                (registration_date IS NULL OR registration_date = '') OR
                (is_lease = 1 AND (lease_deposit IS NULL OR lease_monthly_payment IS NULL))
            ORDER BY first_seen DESC
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            omissions = []
            for row in rows:
                # Check if lease info exists
                has_lease_info = bool(row[6] or row[7] or row[8])  # deposit, monthly_payment, or term_months
                
                omission = {
                    'car_id': row[0],
                    'title': row[1],
                    'listing_url': row[2],
                    'views': row[3],
                    'registration_date': row[4],
                    'is_lease': bool(row[5]),
                    'lease_info': {
                        'deposit': row[6],
                        'monthly_payment': row[7],
                        'lease_term_months': row[8]
                    } if has_lease_info else None,
                    'created_at': row[9],
                    'updated_at': row[10]
                }
                omissions.append(omission)
            
            conn.close()
            
            # Analyze what's missing
            missing_views = sum(1 for o in omissions if o['views'] is None or o['views'] == 0)
            missing_registration = sum(1 for o in omissions if not o['registration_date'])
            missing_lease_info = sum(1 for o in omissions if o['is_lease'] and not o['lease_info'])
            
            self.logger.info(f"📊 Found {len(omissions)} listings with missing data:")
            self.logger.info(f"   - Missing views: {missing_views}")
            self.logger.info(f"   - Missing registration dates: {missing_registration}")
            self.logger.info(f"   - Missing lease info: {missing_lease_info}")
            
            return omissions
            
        except Exception as e:
            self.logger.error(f"❌ Error scanning for omissions: {e}")
            return []
    
    async def process_omissions(self, omissions: List[Dict]) -> Dict:
        """Process the omissions using enhanced extraction"""
        if not omissions:
            self.logger.info("✅ No omissions found to process")
            return {'processed': 0, 'successful': 0, 'failed': 0}
        
        self.logger.info(f"🔧 Processing {len(omissions)} listings with missing data...")
        
        # Convert to format expected by the batch processor
        listings_to_process = []
        for omission in omissions:
            listing = {
                'car_id': omission['car_id'],
                'title': omission['title'],
                'listing_url': omission['listing_url'],
                'is_lease': omission['is_lease'],
                'lease_info': omission['lease_info'] if omission['lease_info'] else None
            }
            listings_to_process.append(listing)
        
        # Process using the enhanced extraction method
        async with EncarScraperAPI(self.config) as scraper:
            enhanced_listings = await scraper.get_views_registration_and_lease_batch(listings_to_process)
        
        # Update database with enhanced data
        processed = 0
        successful = 0
        failed = 0
        
        for enhanced_listing in enhanced_listings:
            try:
                car_id = enhanced_listing['car_id']
                views = enhanced_listing.get('views', 0)
                registration_date = enhanced_listing.get('registration_date', '')
                is_lease = enhanced_listing.get('is_lease', False)
                lease_info = enhanced_listing.get('lease_info')
                
                # Update database
                self.db.update_listing_data(
                    car_id=car_id,
                    views=views,
                    registration_date=registration_date,
                    is_lease=is_lease,
                    lease_info=lease_info
                )
                
                processed += 1
                if views > 0 or registration_date or lease_info:
                    successful += 1
                    self.logger.debug(f"✅ Updated {car_id}: views={views}, reg={registration_date}, lease={is_lease}")
                else:
                    failed += 1
                    self.logger.debug(f"⚠️ No data extracted for {car_id}")
                    
            except Exception as e:
                failed += 1
                self.logger.warning(f"❌ Failed to update {enhanced_listing.get('car_id', 'unknown')}: {e}")
        
        return {
            'processed': processed,
            'successful': successful,
            'failed': failed
        }
    
    def get_statistics(self) -> Dict:
        """Get current database statistics"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            # Total listings
            cursor.execute("SELECT COUNT(*) FROM listings")
            total_listings = cursor.fetchone()[0]
            
            # Listings with views
            cursor.execute("SELECT COUNT(*) FROM listings WHERE views IS NOT NULL AND views > 0")
            listings_with_views = cursor.fetchone()[0]
            
            # Listings with registration dates
            cursor.execute("SELECT COUNT(*) FROM listings WHERE registration_date IS NOT NULL AND registration_date != ''")
            listings_with_registration = cursor.fetchone()[0]
            
            # Lease listings
            cursor.execute("SELECT COUNT(*) FROM listings WHERE is_lease = 1")
            lease_listings = cursor.fetchone()[0]
            
            # Lease listings with info
            cursor.execute("SELECT COUNT(*) FROM listings WHERE is_lease = 1 AND (lease_deposit IS NOT NULL OR lease_monthly_payment IS NOT NULL)")
            lease_listings_with_info = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_listings': total_listings,
                'listings_with_views': listings_with_views,
                'listings_with_registration': listings_with_registration,
                'lease_listings': lease_listings,
                'lease_listings_with_info': lease_listings_with_info,
                'views_coverage': f"{(listings_with_views/total_listings*100):.1f}%" if total_listings > 0 else "0%",
                'registration_coverage': f"{(listings_with_registration/total_listings*100):.1f}%" if total_listings > 0 else "0%",
                'lease_info_coverage': f"{(lease_listings_with_info/lease_listings*100):.1f}%" if lease_listings > 0 else "0%"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting statistics: {e}")
            return {}
    
    async def run_full_scan_and_fix(self, dry_run: bool = False) -> Dict:
        """Run complete scan and fix process"""
        self.logger.info("🔍 Starting full scan and fix process...")
        
        # Get current statistics
        stats_before = self.get_statistics()
        self.logger.info("📊 Current database statistics:")
        for key, value in stats_before.items():
            self.logger.info(f"   {key}: {value}")
        
        # Scan for omissions
        omissions = self.scan_for_omissions()
        
        if not omissions:
            self.logger.info("✅ No omissions found - database is complete!")
            return {'status': 'complete', 'omissions_found': 0}
        
        if dry_run:
            self.logger.info(f"🔍 DRY RUN: Found {len(omissions)} omissions to process")
            self.logger.info("Sample omissions:")
            for i, omission in enumerate(omissions[:5]):
                self.logger.info(f"   {i+1}. {omission['car_id']} - {omission['title'][:50]}...")
            return {'status': 'dry_run', 'omissions_found': len(omissions)}
        
        # Process omissions
        results = await self.process_omissions(omissions)
        
        # Get updated statistics
        stats_after = self.get_statistics()
        
        self.logger.info("📊 Processing results:")
        self.logger.info(f"   - Processed: {results['processed']}")
        self.logger.info(f"   - Successful: {results['successful']}")
        self.logger.info(f"   - Failed: {results['failed']}")
        
        self.logger.info("📊 Updated database statistics:")
        for key, value in stats_after.items():
            self.logger.info(f"   {key}: {value}")
        
        return {
            'status': 'completed',
            'omissions_found': len(omissions),
            'processed': results['processed'],
            'successful': results['successful'],
            'failed': results['failed'],
            'stats_before': stats_before,
            'stats_after': stats_after
        }


async def main():
    """Main function to run the omission scanner"""
    print("🔍 Encar Database Omission Scanner")
    print("=" * 50)
    
    # Check command line arguments first
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv
    stats_only = '--stats' in sys.argv or '-s' in sys.argv
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('omission_scanner.log', encoding='utf-8')
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
    scanner = OmissionScanner(config)
    
    if stats_only:
        print("\n📊 Database Statistics:")
        stats = scanner.get_statistics()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        return
    
    if dry_run:
        print("\n🔍 Running in DRY RUN mode (no database updates)")
    
    # Run the scanner
    try:
        results = await scanner.run_full_scan_and_fix(dry_run=dry_run)
        
        if results['status'] == 'dry_run':
            print(f"\n✅ DRY RUN completed. Found {results['omissions_found']} omissions.")
            print("Run without --dry-run to actually process the omissions.")
        elif results['status'] == 'complete':
            print("\n✅ Database is complete - no omissions found!")
        else:
            print(f"\n✅ Processing completed!")
            print(f"   - Omissions found: {results['omissions_found']}")
            print(f"   - Processed: {results['processed']}")
            print(f"   - Successful: {results['successful']}")
            print(f"   - Failed: {results['failed']}")
            
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        logging.error(f"Processing error: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 