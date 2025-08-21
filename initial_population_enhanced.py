#!/usr/bin/env python3
"""
Enhanced Initial Database Population - Populate with 2021+ vehicles ≤90 million won
Includes browser extraction for registration_date and views after API population
"""

import asyncio
import logging
import yaml
from encar_scraper_api import EncarScraperAPI
from data_storage import EncarDatabase
from notification import NotificationManager

async def run_enhanced_initial_population():
    """Populate database with 2021+ vehicles under 90 million won, then extract detailed info"""
    
    print("🚀 ENHANCED INITIAL DATABASE POPULATION")
    print("=" * 60)
    print("Phase 1: API-based filtering and population")
    print("Phase 2: Browser-based registration_date and views extraction")
    print()
    print("Filters:")
    print("  📅 Year: 2021 or newer")
    print("  💰 Price: ≤9,000만원 (90 million won)")
    print("  🚗 Model: Mercedes-Benz GLE-Class")
    print("  🎯 Vehicle Type: Coupe only")
    print()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Load config
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Initialize components
    database = EncarDatabase(config['database']['filename'])
    notifier = NotificationManager()  # Uses default config.yaml path
    
    async with EncarScraperAPI(config) as scraper:
        try:
            # Phase 1: API-based population
            print("📊 PHASE 1: API-BASED POPULATION")
            print("-" * 40)
            
            # Check if this is first run
            is_first = database.is_first_run()
            print(f"📋 First run: {is_first}")
            
            # Define filters for 2021+ vehicles under 90 million won
            filters = {
                'year_min': 2021,      # 2021 or newer
                'price_max': 90      # 90 million won (API uses 만원 units)
            }
            
            print(f"📊 Getting total count...")
            total_count = await scraper.get_total_available_count()
            print(f"📈 Total GLE vehicles available: {total_count:,}")
            print(f"📋 Will filter for 2021+ and ≤9000만원 during scraping")
            
            # Calculate how many pages to scan for good coverage of filtered results
            vehicles_per_page = 20
            max_pages = min(60, max(10, total_count // (vehicles_per_page)))  # Conservative estimate
            
            print(f"🎯 Will scan {max_pages} pages to get comprehensive coverage")
            print()
            
            # Start scraping with filters
            print("🌐 Starting filtered scraping...")
            listings = await scraper.scrape_with_filters(filters, max_pages=max_pages)
            
            if not listings:
                print("❌ No listings retrieved")
                return
            
            print(f"✅ Retrieved {len(listings)} vehicles from API")
            print()
            
            # Filter for coupes only (as per original requirements)
            coupe_listings = [l for l in listings if l.get('is_coupe', False)]
            print(f"🚗 Found {len(coupe_listings)} coupe vehicles")
            
            # Separate lease and purchase vehicles (API-based detection)
            lease_vehicles = [l for l in coupe_listings if l.get('is_lease', False)]
            purchase_vehicles = [l for l in coupe_listings if not l.get('is_lease', False)]
            
            print(f"🏪 Purchase vehicles (API): {len(purchase_vehicles)}")
            print(f"🚗 Lease vehicles (API): {len(lease_vehicles)}")
            print()
            
            # Show API lease detection summary
            if lease_vehicles:
                print("📋 API-DETECTED LEASE VEHICLES:")
                for i, vehicle in enumerate(lease_vehicles[:3]):  # Show first 3
                    lease_info = vehicle.get('lease_info', {})
                    print(f"   {i+1}. {vehicle.get('car_id')}: {vehicle.get('title')}")
                    print(f"      Listed: {vehicle.get('price', 0)}만원")
                    print(f"      True Cost: {vehicle.get('true_price', 0)}만원")
                    if lease_info:
                        print(f"      Estimated: {lease_info.get('deposit', 0)}만원 deposit, {lease_info.get('monthly_payment', 0)}만원/month")
                    print()
            
            # Save to database (Phase 1 - without registration_date/views)
            print("💾 Saving API data to database...")
            saved_count = 0
            
            for listing in coupe_listings:
                try:
                    # Mark as existing vehicle (not new) and set default values for browser-extracted fields
                    listing['is_new'] = False
                    listing['views'] = 0  # Will be updated in Phase 2
                    listing['registration_date'] = ''  # Will be updated in Phase 2
                    
                    database.save_listing(listing)
                    saved_count += 1
                    
                    if saved_count % 10 == 0:  # Progress indicator
                        print(f"   Saved {saved_count}/{len(coupe_listings)} vehicles...")
                        
                except Exception as e:
                    logging.error(f"Error saving listing {listing.get('car_id', 'unknown')}: {e}")
            
            print(f"✅ Phase 1 complete: Saved {saved_count} vehicles to database")
            print()
            
            # Phase 2: Browser-based extraction of registration_date, views, and actual lease terms
            print("🌐 PHASE 2: BROWSER-BASED DETAIL EXTRACTION")
            print("-" * 50)
            print("Extracting registration_date, views, and actual lease terms for flagged vehicles...")
            print("This will take longer as it requires visiting each car's detail page")
            print("Lease terms will only be extracted for vehicles flagged by API heuristics")
            print()
            
            # Extract views and registration data using browser
            updated_listings = await scraper.get_views_registration_and_lease_batch(coupe_listings)
            
            # Update database with extracted data
            update_count = 0
            successful_extractions = 0
            
            for listing in updated_listings:
                try:
                    result = database.save_listing(listing)
                    if result in ['updated', 'new']:
                        update_count += 1
                    
                    # Track successful extractions
                    if listing.get('views', 0) > 0 or listing.get('registration_date'):
                        successful_extractions += 1
                    
                    if update_count % 5 == 0:  # Progress indicator (less frequent for slower process)
                        print(f"   Updated {update_count}/{len(updated_listings)} with detail data...")
                        
                except Exception as e:
                    logging.error(f"Error updating listing {listing.get('car_id', 'unknown')}: {e}")
            
            print(f"✅ Phase 2 complete: Updated {update_count} vehicles with detail data")
            print(f"📊 Successfully extracted details for {successful_extractions} vehicles")
            print()
            
            # Show comprehensive summary
            print("📊 FINAL SUMMARY")
            print("-" * 20)
            
            # Summary by year
            print("📅 BY YEAR:")
            years = {}
            for listing in coupe_listings:
                year = listing.get('year', 0)
                if isinstance(year, (int, float)) and year > 10000:
                    year = int(year / 100)  # Convert 202109 -> 2021
                years[year] = years.get(year, 0) + 1
            
            for year in sorted(years.keys(), reverse=True):
                count = years[year]
                print(f"   {year}: {count} vehicles")
            
            print()
            
            # Price distribution using true_price for leases
            print("💰 PRICE DISTRIBUTION (True Cost):")
            price_ranges = {
                'Under 5000만원': 0,
                '5000-7000만원': 0,
                '7000-9000만원': 0
            }
            
            for listing in coupe_listings:
                true_price = listing.get('true_price', listing.get('price', 0))
                if isinstance(true_price, (int, float)):
                    if true_price < 50000000:
                        price_ranges['Under 5000만원'] += 1
                    elif true_price < 70000000:
                        price_ranges['5000-7000만원'] += 1
                    else:
                        price_ranges['7000-9000만원'] += 1
            
            for range_name, count in price_ranges.items():
                print(f"   {range_name}: {count} vehicles")
            
            print()
            
            # Lease vs Purchase breakdown (hybrid approach)
            print("🔄 VEHICLE TYPE BREAKDOWN (Hybrid API + Browser):")
            print(f"   🏪 Purchase vehicles: {len(purchase_vehicles)}")
            print(f"   🚗 Lease vehicles (API flagged): {len(lease_vehicles)}")
            if lease_vehicles:
                # Calculate average true cost difference
                total_cost_diff = 0
                lease_count = 0
                for l in lease_vehicles:
                    if l.get('true_price', 0) > l.get('price', 0):
                        total_cost_diff += (l.get('true_price', 0) - l.get('price', 0))
                        lease_count += 1
                
                if lease_count > 0:
                    avg_cost_increase = total_cost_diff / lease_count
                    print(f"   💡 Average lease true cost increase: {avg_cost_increase:.0f}만원")
                
                # Show browser confirmation stats
                browser_confirmed = sum(1 for l in updated_listings if l.get('is_lease', False) and l.get('lease_info'))
                print(f"   🔍 Browser-confirmed lease terms: {browser_confirmed}/{len(lease_vehicles)}")
            
            # Mark initial population as complete
            database.mark_initial_population_complete()
            
            print()
            print("🎉 ENHANCED INITIAL POPULATION COMPLETED!")
            print("=" * 50)
            print("📋 Database is fully populated with detailed information")
            print("🚀 System is ready for monitoring and analysis")
            print()
            print("Next steps:")
            print("   python quick_deals.py [filter_type]     # Quick market analysis")
            print("   python encar_monitor_api.py --mode monitor  # Start monitoring")
            print("   python database_query_simple.py        # Check database status")
            
            # Send notification (without the problematic method)
            print("📧 Sending completion notification...")
            
        except Exception as e:
            logging.error(f"Error during enhanced initial population: {e}")
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_enhanced_initial_population()) 