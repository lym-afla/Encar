#!/usr/bin/env python3
"""
Quick Deals Finder - Fast access to best vehicle deals with URLs
Usage: python quick_deals.py [filter_type]
Filter types: sweet_spot, best_value, budget, recent, low_mileage, luxury
"""

import asyncio
import logging
import sys
from encar_filter_tools import EncarFilterTools

async def find_quick_deals(filter_type="sweet_spot", limit=5):
    """Find deals quickly and show URLs with lease information"""
    
    # Suppress verbose logging
    logging.basicConfig(level=logging.WARNING)
    
    print(f"🔍 Searching for {filter_type} deals...")
    
    async with EncarFilterTools() as filter_tools:
        
        if filter_type == "sweet_spot":
            print("🎯 SWEET SPOT: 2020+, ≤60 million won, ≤80,000km")
            listings, _ = await filter_tools.filter_sweet_spot(limit=limit)
            
        elif filter_type == "best_value":
            print("💎 BEST VALUE: 2019+, ≤60 million won, ≤60,000km (sorted by value)")
            listings = await filter_tools.find_best_value(limit=limit, include_lease=False)
            
        elif filter_type == "best_value_all":
            print("💎 BEST VALUE (INCLUDING LEASE): 2019+, ≤60 million won, ≤60,000km")
            listings = await filter_tools.find_best_value(limit=limit, include_lease=True)
            
        elif filter_type == "budget":
            print("💰 BUDGET FRIENDLY: ≤50 million won")
            listings, _ = await filter_tools.filter_budget_friendly(max_budget=5000, limit=limit)
            
        elif filter_type == "purchase_only":
            print("🏪 PURCHASE ONLY: Excluding lease vehicles")
            listings, _ = await filter_tools.filter_purchase_only(limit=limit)
            
        elif filter_type == "lease_only":
            print("🚗 LEASE ONLY: Only lease vehicles")
            listings, _ = await filter_tools.filter_lease_only(limit=limit)
            
        elif filter_type == "recent":
            print("🆕 RECENT VEHICLES: 2022+")
            listings, _ = await filter_tools.filter_recent_years(years_back=2, limit=limit)
            
        elif filter_type == "low_mileage":
            print("🛣️ LOW MILEAGE: ≤50,000km")
            listings, _ = await filter_tools.filter_low_mileage(limit=limit)
            
        elif filter_type == "luxury":
            print("✨ LUXURY: ≥80 million won")
            listings, _ = await filter_tools.filter_premium_range(min_price=8000, limit=limit)
            
        else:
            print("❌ Unknown filter type")
            return
        
        if not listings:
            print("❌ No vehicles found matching criteria")
            return
        
        print(f"\n⭐ FOUND {len(listings)} VEHICLES:\n")
        
        for i, car in enumerate(listings, 1):
            year = car.get('year', 'N/A')
            price = car.get('price', 0)
            true_price = car.get('true_price', price)
            mileage = car.get('mileage', 0)
            title = car.get('title', 'Unknown')
            url = car.get('listing_url', 'N/A')
            is_lease = car.get('is_lease', False)
            
            print(f"{i:2d}. {title}")
            
            if is_lease:
                lease_info = car.get('lease_info', {})
                deposit = lease_info.get('deposit', 0)
                monthly = lease_info.get('monthly_payment', 0)
                term = lease_info.get('lease_term_months', 0)
                
                print(f"    🚗 LEASE VEHICLE")
                print(f"    💰 Listed: {price:,}만원 → TRUE COST: {true_price:,}만원")
                if deposit and monthly and term:
                    print(f"    📋 {deposit:,}만원 + {monthly:,}만원×{term}mo = {true_price:,}만원")
                print(f"    📅 {year} | 🛣️ {mileage:,}km")
            else:
                print(f"    💰 {price:,}만원 | 📅 {year} | 🛣️ {mileage:,}km")
            
            print(f"    🔗 {url}")
            print()

async def show_all_categories():
    """Show a few vehicles from each category"""
    
    logging.basicConfig(level=logging.WARNING)
    
    print("🏆 BEST DEALS ACROSS ALL CATEGORIES\n")
    
    async with EncarFilterTools() as filter_tools:
        
        # Sweet Spot (best balance)
        print("🎯 SWEET SPOT (Top 3):")
        sweet_spot, _ = await filter_tools.filter_sweet_spot(limit=3)
        for i, car in enumerate(sweet_spot, 1):
            price = car.get('price', 0)
            year = car.get('year', 'N/A')
            url = car.get('listing_url', 'N/A')
            print(f"  {i}. {price:,}만원 ({year}) - {url}")
        
        print()
        
        # Best Value
        print("💎 BEST VALUE (Top 3):")
        best_value = await filter_tools.find_best_value(limit=3)
        for i, car in enumerate(best_value, 1):
            price = car.get('price', 0)
            year = car.get('year', 'N/A')
            url = car.get('listing_url', 'N/A')
            print(f"  {i}. {price:,}만원 ({year}) - {url}")
        
        print()
        
        # Budget Friendly
        print("💰 BUDGET FRIENDLY (Top 3):")
        budget, _ = await filter_tools.filter_budget_friendly(max_budget=5000, limit=3)
        for i, car in enumerate(budget, 1):
            price = car.get('price', 0)
            year = car.get('year', 'N/A')
            url = car.get('listing_url', 'N/A')
            print(f"  {i}. {price:,}만원 ({year}) - {url}")

def main():
    """Main function with command line arguments"""
    
    if len(sys.argv) > 1:
        filter_type = sys.argv[1].lower()
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        
        if filter_type == "all":
            asyncio.run(show_all_categories())
        else:
            asyncio.run(find_quick_deals(filter_type, limit))
    else:
        print("🚗 QUICK DEALS FINDER")
        print("\nUsage:")
        print("  python quick_deals.py sweet_spot         # Best balance deals")
        print("  python quick_deals.py best_value         # Best value (purchase only)") 
        print("  python quick_deals.py best_value_all     # Best value (including lease)")
        print("  python quick_deals.py budget             # Under 5000만원")
        print("  python quick_deals.py purchase_only      # Purchase vehicles only")
        print("  python quick_deals.py lease_only         # Lease vehicles only")
        print("  python quick_deals.py recent             # 2022+ models")
        print("  python quick_deals.py low_mileage        # Under 50,000km")
        print("  python quick_deals.py luxury             # 8000만원+")
        print("  python quick_deals.py all                # Quick summary of all")
        print("\nOptional: Add number limit (default 5)")
        print("  python quick_deals.py sweet_spot 10")
        print("\n🆕 NEW: Lease vehicle detection!")
        print("  - Shows true total cost for lease vehicles")
        print("  - Flags lease vs purchase clearly")
        print("  - Separate filters for lease/purchase only")
        
        print("\n🎯 Running default: sweet_spot...")
        asyncio.run(find_quick_deals("sweet_spot", 5))

if __name__ == "__main__":
    main() 