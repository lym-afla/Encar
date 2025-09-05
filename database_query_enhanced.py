#!/usr/bin/env python3
"""
DEPRECATED: Legacy enhanced database query module
This module is deprecated and will be removed in future versions.
Database operations are now consolidated in data_storage.py.

Enhanced Database Query Module
Provides enhanced database query operations.
"""

import warnings
warnings.warn(
    "database_query_enhanced.py is deprecated. Database operations are now consolidated in data_storage.py.",
    DeprecationWarning,
    stacklevel=2
)

import sqlite3
import yaml

def query_enhanced_database():
    """Query the populated database with lease support"""
    
    print("📊 ENHANCED DATABASE QUERY RESULTS")
    print("=" * 60)
    
    # Load config to get database path
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    db_path = config['database']['filename']
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Total count
            cursor.execute("SELECT COUNT(*) FROM listings")
            total_count = cursor.fetchone()[0]
            print(f"📋 Total vehicles in database: {total_count}")
            
            # Coupe count
            cursor.execute("SELECT COUNT(*) FROM listings WHERE is_coupe = 1")
            coupe_count = cursor.fetchone()[0]
            print(f"🚗 Coupe vehicles: {coupe_count}")
            
            # Lease vs Purchase breakdown
            cursor.execute("SELECT COUNT(*) FROM listings WHERE is_lease = 1")
            lease_count = cursor.fetchone()[0]
            purchase_count = coupe_count - lease_count
            print(f"🏪 Purchase vehicles: {purchase_count}")
            print(f"🚗 Lease vehicles: {lease_count}")
            
            print()
            
            # Year distribution
            print("📅 BY YEAR:")
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN year > 10000 THEN CAST(year/100 AS INTEGER)
                        ELSE year 
                    END as display_year, 
                    COUNT(*) 
                FROM listings 
                WHERE is_coupe = 1 
                GROUP BY display_year
                ORDER BY display_year DESC
            """)
            for year, count in cursor.fetchall():
                print(f"   {year}: {count} vehicles")
            
            print()
            
            # Price ranges using true_price
            print("💰 BY TRUE PRICE RANGE:")
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN true_price < 5000 THEN 'Under 5000만원'
                        WHEN true_price < 7000 THEN '5000-7000만원'
                        WHEN true_price < 9000 THEN '7000-9000만원'
                        ELSE 'Over 9000만원'
                    END as price_range,
                    COUNT(*)
                FROM listings 
                WHERE is_coupe = 1 AND true_price IS NOT NULL
                GROUP BY 
                    CASE 
                        WHEN true_price < 5000 THEN 'Under 5000만원'
                        WHEN true_price < 7000 THEN '5000-7000만원'
                        WHEN true_price < 9000 THEN '7000-9000만원'
                        ELSE 'Over 9000만원'
                    END
                ORDER BY MIN(true_price)
            """)
            for price_range, count in cursor.fetchall():
                print(f"   {price_range}: {count} vehicles")
            
            print()
            
            # Lease vehicle analysis
            if lease_count > 0:
                print("🚗 LEASE VEHICLE ANALYSIS:")
                cursor.execute("""
                    SELECT 
                        AVG(price_numeric) as avg_listed_price,
                        AVG(true_price) as avg_true_cost,
                        AVG(lease_deposit) as avg_deposit,
                        AVG(lease_monthly_payment) as avg_monthly,
                        AVG(lease_term_months) as avg_term
                    FROM listings 
                    WHERE is_lease = 1 AND is_coupe = 1
                """)
                result = cursor.fetchone()
                if result and result[0]:
                    avg_listed, avg_true, avg_deposit, avg_monthly, avg_term = result
                    print(f"   Average listed price: {avg_listed:,.0f}만원")
                    print(f"   Average true cost: {avg_true:,.0f}만원")
                    print(f"   Average cost increase: {avg_true - avg_listed:,.0f}만원")
                    if avg_deposit:
                        print(f"   Average deposit: {avg_deposit:,.0f}만원")
                    if avg_monthly:
                        print(f"   Average monthly: {avg_monthly:,.0f}만원")
                    if avg_term:
                        print(f"   Average term: {avg_term:.0f} months")
                print()
            
            # Recent additions
            print("🕒 MOST RECENT ADDITIONS (Top 5):")
            cursor.execute("""
                SELECT title, price_numeric, true_price, is_lease, car_id, year, views, registration_date
                FROM listings 
                WHERE is_coupe = 1 
                ORDER BY id DESC 
                LIMIT 5
            """)
            
            for i, (title, price_numeric, true_price, is_lease, car_id, year, views, reg_date) in enumerate(cursor.fetchall(), 1):
                display_year = int(year / 100) if year and year > 10000 else year
                lease_flag = "🚗 LEASE" if is_lease else "🏪 PURCHASE"
                
                print(f"   {i}. {title} ({display_year})")
                
                if is_lease and true_price and price_numeric and true_price != price_numeric:
                    print(f"      {lease_flag} - Listed: {price_numeric:,.0f}만원 → True: {true_price:,.0f}만원")
                elif price_numeric:
                    print(f"      {lease_flag} - {price_numeric:,.0f}만원")
                else:
                    print(f"      {lease_flag} - Price TBD")
                
                # Show views and registration if available
                details = []
                if views > 0:
                    details.append(f"👁️ {views} views")
                if reg_date:
                    details.append(f"📅 {reg_date}")
                if details:
                    print(f"      {' | '.join(details)}")
                
                print(f"      🔗 https://fem.encar.com/cars/detail/{car_id}")
            
            print()
            
            # Best deals by true cost for recent cars
            print("🎯 BEST DEALS (Lowest true cost, 2022+):")
            cursor.execute("""
                SELECT title, price_numeric, true_price, is_lease, car_id, year
                FROM listings 
                WHERE is_coupe = 1 AND year >= 202200 AND true_price IS NOT NULL
                ORDER BY true_price ASC 
                LIMIT 3
            """)
            
            for i, (title, price_numeric, true_price, is_lease, car_id, year) in enumerate(cursor.fetchall(), 1):
                display_year = int(year / 100) if year > 10000 else year
                lease_flag = "🚗 LEASE" if is_lease else "🏪 PURCHASE"
                
                print(f"   {i}. {title} ({display_year})")
                
                if is_lease and price_numeric and true_price != price_numeric:
                    print(f"      {lease_flag} - Listed: {price_numeric:,.0f}만원 → True: {true_price:,.0f}만원")
                else:
                    print(f"      {lease_flag} - {true_price:,.0f}만원")
                
                print(f"      🔗 https://fem.encar.com/cars/detail/{car_id}")
            
            print()
            
            # Sample vehicles with registration data
            print("📊 VEHICLES WITH EXTRACTED DATA:")
            cursor.execute("""
                SELECT title, car_id, views, registration_date, is_lease
                FROM listings 
                WHERE is_coupe = 1 AND (views > 0 OR registration_date != '')
                ORDER BY views DESC
                LIMIT 3
            """)
            
            result = cursor.fetchall()
            if result:
                for i, (title, car_id, views, reg_date, is_lease) in enumerate(result, 1):
                    lease_flag = "🚗 LEASE" if is_lease else "🏪 PURCHASE"
                    print(f"   {i}. {title} ({lease_flag})")
                    if views > 0:
                        print(f"      👁️ {views} views")
                    if reg_date:
                        print(f"      📅 Registered: {reg_date}")
                    print(f"      🔗 https://fem.encar.com/cars/detail/{car_id}")
            else:
                print("   ⚠️ No vehicles with extracted registration/views data yet")
                print("   Run Phase 2 of initial population to extract this data")
            
            print()
            print("✅ Enhanced database query completed!")
            print("💡 Database includes lease support and comprehensive data")
            print("🚀 Ready for advanced filtering and monitoring")
            
    except Exception as e:
        print(f"❌ Error querying database: {e}")

if __name__ == "__main__":
    query_enhanced_database() 