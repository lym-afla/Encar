#!/usr/bin/env python3
"""
Update Lease Information for Specific Car ID
Standalone script to update lease information for a specific car ID in the database.
"""

import asyncio
import logging
import yaml
import sys
import os
import sqlite3

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from encar_scraper_api import EncarScraperAPI
from data_storage import EncarDatabase

async def update_lease_for_car(car_id: str, config: dict) -> dict:
    """Update lease information for a specific car ID"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"🔧 Updating lease information for car ID: {car_id}")
        
        # Get the listing from database
        db = EncarDatabase()
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT car_id, title, listing_url, is_lease
            FROM listings 
            WHERE car_id = ?
        """, (car_id,))
        
        row = cursor.fetchone()
        if not row:
            logger.error(f"❌ Car ID {car_id} not found in database")
            return {'success': False, 'error': 'Car ID not found'}
        
        listing = {
            'car_id': row[0],
            'title': row[1],
            'listing_url': row[2],
            'is_lease': bool(row[3])
        }
        
        conn.close()
        
        print(f"📋 Found listing: {listing['title']}")
        print(f"🔗 URL: {listing['listing_url']}")
        
        # Process the single listing
        async with EncarScraperAPI(config) as scraper:
            enhanced_listings = await scraper.get_views_registration_and_lease_batch([listing])
        
        if not enhanced_listings:
            return {'success': False, 'error': 'No data extracted'}
        
        enhanced_listing = enhanced_listings[0]
        
        # Extract lease information
        views = enhanced_listing.get('views', 0)
        registration_date = enhanced_listing.get('registration_date', '')
        is_lease = enhanced_listing.get('is_lease', False)
        lease_info = enhanced_listing.get('lease_info')
        
        # Update database
        db.update_listing_data(
            car_id=car_id,
            views=views,
            registration_date=registration_date,
            is_lease=is_lease,
            lease_info=lease_info
        )
        
        # Log the results
        print(f"\n✅ Updated car ID {car_id}:")
        print(f"   - Views: {views}")
        print(f"   - Registration: {registration_date}")
        print(f"   - Is Lease: {is_lease}")
        
        if lease_info:
            print(f"   - Lease Deposit: {lease_info.get('deposit')}만원")
            print(f"   - Monthly Payment: {lease_info.get('monthly_payment')}만원")
            print(f"   - Lease Term: {lease_info.get('lease_term_months')}개월")
            print(f"   - Estimated Price: {lease_info.get('estimated_price')}만원")
            print(f"   - True Price: {lease_info.get('total_cost')}만원")
            print(f"   - Final Payment: {lease_info.get('final_payment')}만원")
            print(f"   - Total Cost: {lease_info.get('total_cost')}만원")
        else:
            print("   - No lease information found")
        
        return {
            'success': True,
            'car_id': car_id,
            'views': views,
            'registration_date': registration_date,
            'is_lease': is_lease,
            'lease_info': lease_info
        }
        
    except Exception as e:
        logger.error(f"❌ Error updating lease for car ID {car_id}: {e}")
        return {'success': False, 'error': str(e)}

async def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("❌ Error: Please provide a car ID")
        print("Usage: python update_lease_for_car.py <car_id>")
        print("Example: python update_lease_for_car.py 39727392")
        return
    
    car_id = sys.argv[1]
    
    print("🔧 Encar Lease Information Updater")
    print("=" * 50)
    print(f"Target Car ID: {car_id}")
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('lease_update.log', encoding='utf-8')
        ]
    )
    
    # Load config
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return
    
    # Update lease information
    result = await update_lease_for_car(car_id, config)
    
    if result['success']:
        print("\n✅ Lease information updated successfully!")
        print("Database has been updated with the latest information.")
    else:
        print(f"\n❌ Failed to update lease information: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main()) 