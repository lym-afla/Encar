#!/usr/bin/env python3
"""
DEPRECATED: Legacy lease data update script
This module is deprecated and will be removed in future versions.
Lease detection is now integrated into the main monitoring system.

Update Lease Data Script
Updates existing database entries with lease information.
"""

import warnings
warnings.warn(
    "update_lease_data.py is deprecated. Lease detection is now integrated into the main monitoring system.",
    DeprecationWarning,
    stacklevel=2
)

import asyncio
import logging
import yaml
import sqlite3
from encar_scraper_api import EncarScraperAPI
from data_storage import EncarDatabase

async def update_lease_data():
    """Update all vehicles in database with correct lease data from browser extraction"""
    
    print("🔄 UPDATING LEASE DATA IN DATABASE")
    print("=" * 50)
    print("This will re-extract lease terms for all vehicles using browser automation")
    print()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Load config
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Initialize components
    database = EncarDatabase(config['database']['filename'])
    
    # Get all listings from database
    print("📊 Getting all listings from database...")
    conn = sqlite3.connect(config['database']['filename'])
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT car_id, title, listing_url, price, is_lease, lease_deposit, 
               lease_monthly_payment, lease_term_months, lease_total_monthly_cost
        FROM listings 
        ORDER BY car_id
    """)
    
    db_listings = cursor.fetchall()
    conn.close()
    
    print(f"📋 Found {len(db_listings)} vehicles in database")
    print()
    
    # Convert to list of dictionaries for processing
    listings = []
    for row in db_listings:
        car_id, title, listing_url, price, is_lease, lease_deposit, lease_monthly, lease_term, lease_total = row
        listings.append({
            'car_id': car_id,
            'title': title,
            'listing_url': listing_url,
            'price': price,
            'is_lease': bool(is_lease),
            'lease_deposit': lease_deposit,
            'lease_monthly_payment': lease_monthly,
            'lease_term_months': lease_term,
            'lease_total_monthly_cost': lease_total
        })
    
    # Process with browser extraction
    print("🌐 Starting browser-based lease extraction...")
    print("This will take some time as it visits each vehicle's detail page")
    print()
    
    async with EncarScraperAPI(config) as scraper:
        # Extract lease data for all listings
        updated_listings = await scraper.get_views_and_registration_batch(listings)
        
        # Update database with new lease data
        print("💾 Updating database with extracted lease data...")
        update_count = 0
        lease_updates = 0
        
        for listing in updated_listings:
            try:
                result = database.save_listing(listing)
                if result in ['updated', 'new']:
                    update_count += 1
                
                # Track lease-specific updates
                if listing.get('is_lease', False) and listing.get('lease_info'):
                    lease_updates += 1
                    print(f"✅ Updated lease data for {listing.get('car_id')}: {listing.get('lease_info')}")
                
                if update_count % 10 == 0:
                    print(f"   Updated {update_count}/{len(updated_listings)} vehicles...")
                    
            except Exception as e:
                logging.error(f"Error updating listing {listing.get('car_id', 'unknown')}: {e}")
        
        print()
        print("📊 UPDATE SUMMARY")
        print("-" * 20)
        print(f"✅ Total vehicles updated: {update_count}")
        print(f"🚗 Lease vehicles updated: {lease_updates}")
        print()
        
        # Show lease statistics
        print("📈 LEASE VEHICLE STATISTICS:")
        lease_vehicles = [l for l in updated_listings if l.get('is_lease', False)]
        purchase_vehicles = [l for l in updated_listings if not l.get('is_lease', False)]
        
        print(f"   🚗 Lease vehicles: {len(lease_vehicles)}")
        print(f"   🏪 Purchase vehicles: {len(purchase_vehicles)}")
        
        if lease_vehicles:
            print()
            print("📋 SAMPLE LEASE VEHICLES:")
            for i, vehicle in enumerate(lease_vehicles[:5]):  # Show first 5
                lease_info = vehicle.get('lease_info', {})
                print(f"   {i+1}. {vehicle.get('car_id')}: {vehicle.get('title')}")
                print(f"      Deposit: {lease_info.get('deposit', 0)}만원")
                print(f"      Monthly: {lease_info.get('monthly_payment', 0)}만원")
                print(f"      Term: {lease_info.get('lease_term_months', 0)} months")
                print(f"      Total: {lease_info.get('total_cost', 0)}만원")
                print()
        
        print("🎉 LEASE DATA UPDATE COMPLETE!")
        print("=" * 30)

async def main():
    await update_lease_data()

if __name__ == "__main__":
    asyncio.run(main()) 