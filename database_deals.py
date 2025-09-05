#!/usr/bin/env python3
"""
DEPRECATED: Legacy database deals module
This module is deprecated and will be removed in future versions.
Database operations are now consolidated in data_storage.py.

Database Deals Module
Provides database operations for deal analysis.
"""

import warnings
warnings.warn(
    "database_deals.py is deprecated. Database operations are now consolidated in data_storage.py.",
    DeprecationWarning,
    stacklevel=2
)

import sqlite3
import yaml
import sys

def get_database_deals(deal_type="all", limit=5):
    """Find deals from the populated database"""
    
    print(f"🔍 Searching database for {deal_type} deals...")
    
    # Load config to get database path
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    db_path = config['database']['filename']
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            if deal_type == "lease_only":
                print("🚗 LEASE ONLY: From populated database")
                cursor.execute("""
                    SELECT title, price_numeric, true_price, car_id, year, 
                           lease_deposit, lease_monthly_payment, lease_term_months
                    FROM listings 
                    WHERE is_lease = 1 AND is_coupe = 1
                    ORDER BY true_price ASC
                    LIMIT ?
                """, (limit,))
                
            elif deal_type == "purchase_only":
                print("🏪 PURCHASE ONLY: From populated database")
                cursor.execute("""
                    SELECT title, price_numeric, true_price, car_id, year
                    FROM listings 
                    WHERE is_lease = 0 AND is_coupe = 1
                    ORDER BY true_price ASC
                    LIMIT ?
                """, (limit,))
                
            elif deal_type == "best_value":
                print("💎 BEST VALUE: Lowest true cost from database")
                cursor.execute("""
                    SELECT title, price_numeric, true_price, is_lease, car_id, year,
                           lease_deposit, lease_monthly_payment, lease_term_months
                    FROM listings 
                    WHERE is_coupe = 1 AND true_price IS NOT NULL
                    ORDER BY true_price ASC
                    LIMIT ?
                """, (limit,))
                
            elif deal_type == "recent":
                print("📅 RECENT MODELS: 2022+ from database")
                cursor.execute("""
                    SELECT title, price_numeric, true_price, is_lease, car_id, year,
                           lease_deposit, lease_monthly_payment, lease_term_months
                    FROM listings 
                    WHERE is_coupe = 1 AND year >= 202200
                    ORDER BY true_price ASC
                    LIMIT ?
                """, (limit,))
                
            else:  # all
                print("🎯 ALL VEHICLES: From populated database")
                cursor.execute("""
                    SELECT title, price_numeric, true_price, is_lease, car_id, year,
                           lease_deposit, lease_monthly_payment, lease_term_months
                    FROM listings 
                    WHERE is_coupe = 1
                    ORDER BY true_price ASC
                    LIMIT ?
                """, (limit,))
            
            results = cursor.fetchall()
            
            if not results:
                print("❌ No vehicles found matching criteria")
                return
            
            print(f"⭐ FOUND {len(results)} VEHICLES:")
            print()
            
            for i, row in enumerate(results, 1):
                if deal_type in ["lease_only"]:
                    title, price_numeric, true_price, car_id, year, deposit, monthly, term = row
                    display_year = int(year / 100) if year and year > 10000 else year
                    
                    print(f" {i}. {title} ({display_year})")
                    print(f"    🚗 LEASE VEHICLE")
                    print(f"    💰 Listed: {price_numeric:,.0f}만원 → TRUE COST: {true_price:,.0f}만원")
                    
                    if deposit and monthly and term:
                        print(f"    📋 {deposit:,.0f}만원 + {monthly:,.0f}만원×{term:.0f}mo = {true_price:,.0f}만원")
                    
                    print(f"    🔗 https://fem.encar.com/cars/detail/{car_id}")
                    
                elif deal_type == "purchase_only":
                    title, price_numeric, true_price, car_id, year = row
                    display_year = int(year / 100) if year and year > 10000 else year
                    
                    print(f" {i}. {title} ({display_year})")
                    print(f"    💰 {true_price:,.0f}만원")
                    print(f"    🔗 https://fem.encar.com/cars/detail/{car_id}")
                    
                else:  # Mixed results with lease info
                    title, price_numeric, true_price, is_lease, car_id, year, deposit, monthly, term = row
                    display_year = int(year / 100) if year and year > 10000 else year
                    
                    print(f" {i}. {title} ({display_year})")
                    
                    if is_lease:
                        print(f"    🚗 LEASE VEHICLE")
                        print(f"    💰 Listed: {price_numeric:,.0f}만원 → TRUE COST: {true_price:,.0f}만원")
                        if deposit and monthly and term:
                            print(f"    📋 {deposit:,.0f}만원 + {monthly:,.0f}만원×{term:.0f}mo")
                    else:
                        print(f"    🏪 PURCHASE VEHICLE")
                        print(f"    💰 {true_price:,.0f}만원")
                    
                    print(f"    🔗 https://fem.encar.com/cars/detail/{car_id}")
                
                print()
            
            # Show total count
            cursor.execute("SELECT COUNT(*) FROM listings WHERE is_coupe = 1")
            total_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM listings WHERE is_lease = 1 AND is_coupe = 1")
            lease_count = cursor.fetchone()[0]
            
            print(f"📊 Database Summary:")
            print(f"   Total coupe vehicles: {total_count}")
            print(f"   Lease vehicles: {lease_count}")
            print(f"   Purchase vehicles: {total_count - lease_count}")
            
    except Exception as e:
        print(f"❌ Error querying database: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python database_deals.py <deal_type> [limit]")
        print("Deal types: lease_only, purchase_only, best_value, recent, all")
        print("Example: python database_deals.py lease_only 5")
        return
    
    deal_type = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    get_database_deals(deal_type, limit)

if __name__ == "__main__":
    main() 