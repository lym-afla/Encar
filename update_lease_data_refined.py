#!/usr/bin/env python3
"""
DEPRECATED: Legacy refined lease data update script
This module is deprecated and will be removed in future versions.
Lease detection is now integrated into the main monitoring system.

Refined Update Lease Data Script
Updates existing database entries with refined lease information.
"""

import warnings
warnings.warn(
    "update_lease_data_refined.py is deprecated. Lease detection is now integrated into the main monitoring system.",
    DeprecationWarning,
    stacklevel=2
)

import asyncio
import logging
import yaml
import sqlite3
from encar_scraper_api import EncarScraperAPI
from data_storage import EncarDatabase

async def update_lease_data_refined():
    """Update lease data using refined hybrid approach"""
    
    print("🔄 UPDATING LEASE DATA WITH REFINED HYBRID APPROACH")
    print("=" * 60)
    print("Strategy:")
    print("  1. Only extract lease terms for vehicles flagged by API heuristics")
    print("  2. Use browser automation to get actual lease terms from detail pages")
    print("  3. Update true_price and lease_info with accurate data")
    print()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Load config
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Initialize components
    database = EncarDatabase(config['database']['filename'])
    
    # Get all lease vehicles from database
    print("📊 Getting lease vehicles from database...")
    conn = sqlite3.connect(config['database']['filename'])
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT car_id, title, listing_url, price, is_lease, lease_deposit, 
               lease_monthly_payment, lease_term_months, lease_total_monthly_cost
        FROM listings 
        WHERE is_lease = 1
        ORDER BY car_id
    """)
    
    lease_vehicles = cursor.fetchall()
    conn.close()
    
    print(f"📋 Found {len(lease_vehicles)} lease vehicles in database")
    print()
    
    if not lease_vehicles:
        print("❌ No lease vehicles found in database")
        print("   Run initial population first to populate with API-based lease detection")
        return
    
    # Convert to list of dictionaries for processing
    listings = []
    for row in lease_vehicles:
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
    
    # Process with browser extraction (only for flagged lease vehicles)
    print("🌐 Starting browser-based lease term extraction...")
    print("This will visit each lease vehicle's detail page to extract actual terms")
    print()
    
    async with EncarScraperAPI(config) as scraper:
        # Extract lease data for flagged vehicles
        updated_listings = await scraper.get_views_registration_and_lease_batch(listings)
        
        # Update database with refined lease data
        print("💾 Updating database with refined lease data...")
        update_count = 0
        lease_updates = 0
        browser_confirmed = 0
        
        for listing in updated_listings:
            try:
                result = database.save_listing(listing)
                if result in ['updated', 'new']:
                    update_count += 1
                
                # Track lease-specific updates
                if listing.get('is_lease', False):
                    lease_updates += 1
                    
                    # Check if browser confirmed lease terms
                    if listing.get('lease_info'):
                        browser_confirmed += 1
                        lease_info = listing.get('lease_info', {})
                        print(f"✅ Browser confirmed lease terms for {listing.get('car_id')}:")
                        print(f"   Deposit: {lease_info.get('deposit', 0)}만원")
                        print(f"   Monthly: {lease_info.get('monthly_payment', 0)}만원")
                        print(f"   Term: {lease_info.get('lease_term_months', 0)} months")
                        print(f"   Total: {lease_info.get('total_cost', 0)}만원")
                        print()
                    else:
                        print(f"⚠️ API flagged but no lease terms found on page: {listing.get('car_id')}")
                
                if update_count % 5 == 0:
                    print(f"   Updated {update_count}/{len(updated_listings)} vehicles...")
                    
            except Exception as e:
                logging.error(f"Error updating listing {listing.get('car_id', 'unknown')}: {e}")
        
        print()
        print("📊 UPDATE SUMMARY")
        print("-" * 20)
        print(f"✅ Total vehicles updated: {update_count}")
        print(f"🚗 Lease vehicles processed: {lease_updates}")
        print(f"🔍 Browser-confirmed lease terms: {browser_confirmed}")
        print(f"📈 Success rate: {browser_confirmed}/{lease_updates} ({browser_confirmed/lease_updates*100:.1f}%)")
        print()
        
        # Show detailed statistics
        print("📈 LEASE VEHICLE STATISTICS:")
        confirmed_leases = [l for l in updated_listings if l.get('is_lease', False) and l.get('lease_info')]
        unconfirmed_leases = [l for l in updated_listings if l.get('is_lease', False) and not l.get('lease_info')]
        
        print(f"   🔍 Browser-confirmed: {len(confirmed_leases)}")
        print(f"   ⚠️ API-only (no page terms): {len(unconfirmed_leases)}")
        
        if confirmed_leases:
            print()
            print("💰 CONFIRMED LEASE COST ANALYSIS:")
            total_listed = sum(l.get('price', 0) for l in confirmed_leases)
            total_true = sum(l.get('true_price', 0) for l in confirmed_leases)
            avg_increase = (total_true - total_listed) / len(confirmed_leases)
            
            print(f"   Average listed price: {total_listed/len(confirmed_leases):.0f}만원")
            print(f"   Average true cost: {total_true/len(confirmed_leases):.0f}만원")
            print(f"   Average cost increase: {avg_increase:.0f}만원")
        
        print()
        print("🎉 LEASE DATA UPDATE COMPLETE!")
        print("=" * 30)

async def main():
    await update_lease_data_refined()

if __name__ == "__main__":
    asyncio.run(main()) 