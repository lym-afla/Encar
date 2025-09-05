#!/usr/bin/env python3
"""
Encar Filter Tools - Advanced Search and Filtering
Provides tools to narrow search criteria for precise car hunting
"""

import asyncio
import logging
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from encar_api_client import EncarAPIClient

class EncarFilterTools:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize filter tools with configuration"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
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
    
    # Year-based filtering
    async def filter_by_year_range(self, year_min: int = None, year_max: int = None, limit: int = 50) -> Tuple[List[Dict], int]:
        """Filter vehicles by year range"""
        filters = {}
        if year_min:
            filters['year_min'] = year_min
        if year_max:
            filters['year_max'] = year_max
        
        self.logger.info(f"Filtering by year range: {year_min} - {year_max}")
        listings, total = await self.api_client.get_listings_with_filters(filters, limit=limit)
        coupe_listings = [l for l in listings if l['is_coupe']]
        
        return coupe_listings, total
    
    async def filter_recent_years(self, years_back: int = 3, limit: int = 50) -> Tuple[List[Dict], int]:
        """Filter vehicles from recent years only"""
        current_year = datetime.now().year
        year_min = current_year - years_back
        
        return await self.filter_by_year_range(year_min=year_min, limit=limit)
    
    # Price-based filtering
    async def filter_by_price_range(self, price_min: int = None, price_max: int = None, limit: int = 50, include_lease: bool = True) -> Tuple[List[Dict], int]:
        """Filter vehicles by price range (in 만원) using true cost for lease vehicles"""
        filters = {}
        if price_min:
            filters['price_min'] = price_min
        if price_max:
            filters['price_max'] = price_max
        
        self.logger.info(f"Filtering by price range: {price_min} - {price_max} 만원 (include_lease: {include_lease})")
        listings, total = await self.api_client.get_listings_with_filters(filters, limit=limit)
        coupe_listings = [l for l in listings if l['is_coupe']]
        
        # Filter by true price for lease vehicles
        if price_min or price_max:
            filtered_coupes = []
            for listing in coupe_listings:
                true_price = listing.get('true_price', listing.get('price', 0))
                is_lease = listing.get('is_lease', False)
                
                # Skip lease vehicles if not included
                if is_lease and not include_lease:
                    continue
                
                # Check price range using true price
                if price_min and true_price < price_min:
                    continue
                if price_max and true_price > price_max:
                    continue
                    
                filtered_coupes.append(listing)
            
            coupe_listings = filtered_coupes
        
        return coupe_listings, total
    
    async def filter_purchase_only(self, limit: int = 50) -> Tuple[List[Dict], int]:
        """Filter only purchase vehicles (exclude lease)"""
        self.logger.info("Filtering purchase-only vehicles (excluding lease)")
        listings, total = await self.api_client.get_listings(limit=limit)
        
        # Filter for coupes and non-lease vehicles only
        purchase_listings = [l for l in listings if l['is_coupe'] and not l.get('is_lease', False)]
        
        return purchase_listings, total
    
    async def filter_lease_only(self, limit: int = 50) -> Tuple[List[Dict], int]:
        """Filter only lease vehicles"""
        self.logger.info("Filtering lease-only vehicles")
        listings, total = await self.api_client.get_listings(limit=limit)
        
        # Filter for coupes and lease vehicles only
        lease_listings = [l for l in listings if l['is_coupe'] and l.get('is_lease', False)]
        
        return lease_listings, total
    
    async def filter_budget_friendly(self, max_budget: int, limit: int = 50) -> Tuple[List[Dict], int]:
        """Filter vehicles within budget"""
        return await self.filter_by_price_range(price_max=max_budget, limit=limit)
    
    async def filter_premium_range(self, min_price: int = 7000, limit: int = 50) -> Tuple[List[Dict], int]:
        """Filter premium vehicles above certain price"""
        return await self.filter_by_price_range(price_min=min_price, limit=limit)
    
    # Mileage-based filtering
    async def filter_by_mileage(self, max_mileage: int, limit: int = 50) -> Tuple[List[Dict], int]:
        """Filter vehicles by maximum mileage (in km)"""
        filters = {'mileage_max': max_mileage}
        
        self.logger.info(f"Filtering by max mileage: {max_mileage:,} km")
        listings, total = await self.api_client.get_listings_with_filters(filters, limit=limit)
        coupe_listings = [l for l in listings if l['is_coupe']]
        
        return coupe_listings, total
    
    async def filter_low_mileage(self, limit: int = 50) -> Tuple[List[Dict], int]:
        """Filter low mileage vehicles (under 50,000 km)"""
        return await self.filter_by_mileage(max_mileage=50000, limit=limit)
    
    async def filter_very_low_mileage(self, limit: int = 50) -> Tuple[List[Dict], int]:
        """Filter very low mileage vehicles (under 20,000 km)"""
        return await self.filter_by_mileage(max_mileage=20000, limit=limit)
    
    # Combined filtering
    async def filter_sweet_spot(self, max_price: int = 6000, max_years_old: int = 5, max_mileage: int = 80000, limit: int = 50) -> Tuple[List[Dict], int]:
        """Find the 'sweet spot' vehicles - good price, not too old, reasonable mileage"""
        current_year = datetime.now().year
        year_min = current_year - max_years_old
        
        filters = {
            'year_min': year_min,
            'price_max': max_price,
            'mileage_max': max_mileage
        }
        
        self.logger.info(f"Sweet spot filter: Year {year_min}+, Price <={max_price}만원, Mileage <={max_mileage:,}km")
        listings, total = await self.api_client.get_listings_with_filters(filters, limit=limit)
        coupe_listings = [l for l in listings if l['is_coupe']]
        
        return coupe_listings, total
    
    async def filter_luxury_recent(self, min_price: int = 8000, max_years_old: int = 3, limit: int = 50) -> Tuple[List[Dict], int]:
        """Find luxury recent vehicles"""
        current_year = datetime.now().year
        year_min = current_year - max_years_old
        
        filters = {
            'year_min': year_min,
            'price_min': min_price
        }
        
        self.logger.info(f"Luxury recent filter: Year {year_min}+, Price >={min_price}만원")
        listings, total = await self.api_client.get_listings_with_filters(filters, limit=limit)
        coupe_listings = [l for l in listings if l['is_coupe']]
        
        return coupe_listings, total
    
    # Analysis tools
    async def analyze_market_segments(self) -> Dict:
        """Analyze different market segments"""
        segments = {}
        
        # Budget segment (under 4000만원)
        budget_listings, budget_total = await self.filter_budget_friendly(4000, limit=100)
        segments['budget'] = {
            'count': len(budget_listings),
            'total_available': budget_total,
            'avg_price': sum(l.get('price', 0) for l in budget_listings) / len(budget_listings) if budget_listings else 0,
            'avg_mileage': sum(l.get('mileage', 0) for l in budget_listings) / len(budget_listings) if budget_listings else 0
        }
        
        # Mid-range segment (4000-7000만원)
        midrange_listings, midrange_total = await self.filter_by_price_range(4000, 7000, limit=100)
        segments['midrange'] = {
            'count': len(midrange_listings),
            'total_available': midrange_total,
            'avg_price': sum(l.get('price', 0) for l in midrange_listings) / len(midrange_listings) if midrange_listings else 0,
            'avg_mileage': sum(l.get('mileage', 0) for l in midrange_listings) / len(midrange_listings) if midrange_listings else 0
        }
        
        # Luxury segment (7000만원+)
        luxury_listings, luxury_total = await self.filter_premium_range(7000, limit=100)
        segments['luxury'] = {
            'count': len(luxury_listings),
            'total_available': luxury_total,
            'avg_price': sum(l.get('price', 0) for l in luxury_listings) / len(luxury_listings) if luxury_listings else 0,
            'avg_mileage': sum(l.get('mileage', 0) for l in luxury_listings) / len(luxury_listings) if luxury_listings else 0
        }
        
        return segments
    
    async def find_best_value(self, limit: int = 20, include_lease: bool = False) -> List[Dict]:
        """Find best value vehicles (good price-to-features ratio) with lease options"""
        # Get recent, low-mileage vehicles under 6000만원
        filters = {
            'year_min': 2019,  # 2019 or newer
            'price_max': 70,  # Under 6000만원 (will be filtered by true_price later)
            'mileage_max': 60000  # Under 60,000km
        }
        
        self.logger.info(f"Finding best value vehicles (include_lease: {include_lease})...")
        listings, total = await self.api_client.get_listings_with_filters(filters, limit=limit*3)
        coupe_listings = [l for l in listings if l['is_coupe']]
        
        # Filter by true price and lease preference
        filtered_listings = []
        for listing in coupe_listings:
            is_lease = listing.get('is_lease', False)
            true_price = listing.get('true_price', listing.get('price', 0))
            
            # Skip lease vehicles if not included
            if is_lease and not include_lease:
                continue
                
            # Apply true price filter
            if true_price > 6000:
                continue
                
            filtered_listings.append(listing)
        
        # Sort by price-to-year ratio (lower is better value)
        for listing in filtered_listings:
            year = listing.get('year', 2015)
            true_price = listing.get('true_price', listing.get('price', 9999))
            if isinstance(year, (int, float)) and year > 2000:
                listing['value_score'] = true_price / max(year - 2000, 1)  # Simple value scoring
            else:
                listing['value_score'] = 999  # High score for bad data
        
        # Sort by value score and return top results
        best_value = sorted(filtered_listings, key=lambda x: x.get('value_score', 999))[:limit]
        
        return best_value
    
    def print_filter_results(self, listings: List[Dict], title: str):
        """Print formatted filter results with URLs and lease information"""
        print(f"\n=== {title} ===")
        print(f"Found {len(listings)} vehicles")
        
        if not listings:
            print("No vehicles found matching criteria")
            return
        
        print("\nTop results:")
        for i, listing in enumerate(listings[:10], 1):
            year = listing.get('year', 'N/A')
            price = listing.get('price', 0)
            true_price = listing.get('true_price', price)
            mileage = listing.get('mileage', 0)
            title_text = listing.get('title', 'Unknown')
            listing_url = listing.get('listing_url', 'N/A')
            is_lease = listing.get('is_lease', False)
            
            print(f"{i:2d}. {title_text}")
            
            if is_lease:
                lease_info = listing.get('lease_info', {})
                deposit = lease_info.get('deposit', 0)
                monthly = lease_info.get('monthly_payment', 0)
                term = lease_info.get('lease_term_months', 0)
                
                print(f"    🚗 LEASE VEHICLE")
                print(f"    💰 Listed: {price:,}만원 | TRUE COST: {true_price:,}만원")
                if deposit and monthly and term:
                    print(f"    📋 Lease: {deposit:,}만원 deposit + {monthly:,}만원×{term}months")
                print(f"    📅 Year: {year} | 🛣️ Mileage: {mileage:,}km")
            else:
                print(f"    💰 Price: {price:,}만원 | 📅 Year: {year} | 🛣️ Mileage: {mileage:,}km")
            
            print(f"    🔗 URL: {listing_url}")
            
            if 'value_score' in listing:
                print(f"    📊 Value Score: {listing['value_score']:.1f}")
            print()  # Add blank line for better readability
    
    def print_market_analysis(self, segments: Dict):
        """Print market analysis results"""
        print("\n=== MARKET ANALYSIS ===")
        
        for segment_name, data in segments.items():
            print(f"\n{segment_name.upper()} SEGMENT:")
            print(f"  Available: {data['count']} vehicles (of {data['total_available']} total)")
            print(f"  Avg Price: {data['avg_price']:,.0f}만원")
            print(f"  Avg Mileage: {data['avg_mileage']:,.0f}km")

    def print_urls_only(self, listings: List[Dict], title: str, limit: int = 10):
        """Print only URLs for easy copying"""
        print(f"\n=== {title} - URLs Only ===")
        for i, listing in enumerate(listings[:limit], 1):
            url = listing.get('listing_url', 'N/A')
            title_text = listing.get('title', 'Unknown')
            price = listing.get('price', 0)
            print(f"{i:2d}. {title_text} ({price:,}만원)")
            print(f"    {url}")
    
    def export_results_to_file(self, listings: List[Dict], filename: str, title: str):
        """Export filtering results to a text file"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"=== {title} ===\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Found {len(listings)} vehicles\n\n")
            
            for i, listing in enumerate(listings, 1):
                year = listing.get('year', 'N/A')
                price = listing.get('price', 0)
                mileage = listing.get('mileage', 0)
                title_text = listing.get('title', 'Unknown')
                listing_url = listing.get('listing_url', 'N/A')
                
                f.write(f"{i:2d}. {title_text}\n")
                f.write(f"    Year: {year} | Price: {price:,}만원 | Mileage: {mileage:,}km\n")
                f.write(f"    URL: {listing_url}\n")
                
                if 'value_score' in listing:
                    f.write(f"    Value Score: {listing['value_score']:.1f}\n")
                f.write("\n")
        
        print(f"Results exported to: {filename}")
    
    async def quick_search(self, search_type: str, **kwargs) -> List[Dict]:
        """Quick search with predefined filters"""
        search_types = {
            'recent': lambda: self.filter_recent_years(years_back=kwargs.get('years', 3)),
            'budget': lambda: self.filter_budget_friendly(max_budget=kwargs.get('budget', 5000)),
            'low_mileage': lambda: self.filter_low_mileage(),
            'very_low_mileage': lambda: self.filter_very_low_mileage(),
            'sweet_spot': lambda: self.filter_sweet_spot(),
            'luxury': lambda: self.filter_premium_range(min_price=kwargs.get('min_price', 7000)),
            'best_value': lambda: self.find_best_value()
        }
        
        if search_type not in search_types:
            print(f"Available search types: {list(search_types.keys())}")
            return []
        
        listings, total = await search_types[search_type]()
        return listings

    async def check_for_lease_vehicles(self, listings: List[Dict], max_checks: int = 10) -> List[Dict]:
        """Check detail pages for potential lease vehicles"""
        from lease_detail_scraper import LeaseDetailScraper
        
        # Initialize lease scraper
        lease_scraper = LeaseDetailScraper(self.config)
        
        updated_listings = []
        check_count = 0
        
        for listing in listings:
            if check_count >= max_checks:
                # Don't check more than max_checks to avoid being too slow
                updated_listings.append(listing)
                continue
                
            # Check if this listing should be investigated for lease status
            should_check = self.should_check_for_lease(listing)
            
            if should_check:
                self.logger.info(f"Checking vehicle {listing.get('car_id')} for lease status...")
                check_count += 1
                
                try:
                    lease_details = await lease_scraper.extract_lease_details(listing['listing_url'])
                    
                    if lease_details and lease_details.get('is_lease', False):
                        # Update the listing with lease information
                        listing['is_lease'] = True
                        listing['lease_info'] = lease_details
                        listing['true_price'] = lease_details.get('total_cost', listing['price'])
                        self.logger.info(f"✅ Vehicle {listing.get('car_id')} confirmed as LEASE")
                    else:
                        listing['is_lease'] = False
                        listing['true_price'] = listing['price']
                        self.logger.info(f"✅ Vehicle {listing.get('car_id')} confirmed as PURCHASE")
                        
                except Exception as e:
                    self.logger.error(f"Error checking lease status for {listing.get('car_id')}: {e}")
                    # Default to not lease if we can't determine
                    listing['is_lease'] = False
                    listing['true_price'] = listing['price']
            else:
                # Default to not lease
                listing['is_lease'] = False
                listing['true_price'] = listing['price']
            
            updated_listings.append(listing)
        
        return updated_listings
    
    def should_check_for_lease(self, listing: Dict) -> bool:
        """Determine if a listing should be checked for lease status"""
        price = listing.get('price', 0)
        year = listing.get('year', 0)
        
        # Convert year format if needed
        if isinstance(year, (int, float)) and year > 10000:
            year = int(year / 100)
        
        # Check recent cars with moderate prices (potential lease candidates)
        if year >= 2019 and 1000 <= price <= 8000:
            return True
            
        # Check cars with suspiciously round prices (might be estimates)
        if price % 100 == 0 or str(price).endswith('77'):  # Like 5177 in user's example
            return True
            
        return False


async def demo_filter_tools():
    """Demonstrate the filtering tools with URLs"""
    print("=== ENCAR ADVANCED FILTERING DEMO ===")
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    async with EncarFilterTools() as filter_tools:
        # Test different filtering scenarios
        
        # 1. Recent years filter
        print("\n1. RECENT VEHICLES (2021+)")
        recent_vehicles, _ = await filter_tools.filter_recent_years(years_back=3, limit=20)
        filter_tools.print_filter_results(recent_vehicles, "Recent Vehicles (2021+)")
        
        # Show URLs only for top 3 recent vehicles
        if recent_vehicles:
            filter_tools.print_urls_only(recent_vehicles[:3], "Top 3 Recent Vehicles")
        
        # 2. Sweet spot filter (most interesting results)
        print("\n2. SWEET SPOT (Good balance)")
        sweet_spot, _ = await filter_tools.filter_sweet_spot(limit=15)
        filter_tools.print_filter_results(sweet_spot, "Sweet Spot")
        
        # Export sweet spot results
        if sweet_spot:
            filter_tools.export_results_to_file(sweet_spot, "sweet_spot_vehicles.txt", "Sweet Spot Vehicles")
        
        # 3. Best value analysis
        print("\n3. BEST VALUE ANALYSIS")
        best_value = await filter_tools.find_best_value(limit=10)
        filter_tools.print_filter_results(best_value, "Best Value Vehicles")
        
        # Show URLs only for best deals
        if best_value:
            filter_tools.print_urls_only(best_value[:5], "Top 5 Best Value")
        
        # 4. Budget filter
        print("\n4. BUDGET FRIENDLY (Under 5000만원)")
        budget_vehicles, _ = await filter_tools.filter_budget_friendly(max_budget=5000, limit=10)
        filter_tools.print_filter_results(budget_vehicles, "Budget Friendly")
        
        # 5. Market analysis (summary only)
        print("\n5. MARKET SEGMENT ANALYSIS")
        market_segments = await filter_tools.analyze_market_segments()
        filter_tools.print_market_analysis(market_segments)
        
        # Quick demo of the quick_search function
        print("\n6. QUICK SEARCH DEMO")
        luxury_quick = await filter_tools.quick_search('luxury', min_price=8000)
        if luxury_quick:
            print(f"Quick luxury search found {len(luxury_quick)} vehicles")
            filter_tools.print_urls_only(luxury_quick[:3], "Quick Luxury Search")

async def quick_demo():
    """Quick demo focusing on URLs and best deals"""
    print("=== QUICK DEMO - BEST DEALS WITH URLS ===")
    
    logging.basicConfig(level=logging.WARNING)  # Less verbose
    
    async with EncarFilterTools() as filter_tools:
        # Find the absolute best deals
        print("\n🎯 FINDING BEST DEALS...")
        best_deals = await filter_tools.find_best_value(limit=5)
        
        if best_deals:
            print(f"\n⭐ TOP {len(best_deals)} BEST VALUE VEHICLES:")
            for i, car in enumerate(best_deals, 1):
                year = car.get('year', 'N/A')
                price = car.get('price', 0)
                mileage = car.get('mileage', 0)
                title = car.get('title', 'Unknown')
                url = car.get('listing_url', 'N/A')
                
                print(f"\n{i}. {title}")
                print(f"   �� Price: {price:,}만원 | 📅 Year: {year} | 🛣️  Mileage: {mileage:,}km")
                print(f"   🔗 Link: {url}")
        
        # Quick sweet spot check
        print("\n🎯 SWEET SPOT VEHICLES (2020+, ≤6000만원, ≤80,000km)...")
        sweet_spot, _ = await filter_tools.filter_sweet_spot(limit=3)
        
        if sweet_spot:
            print(f"\n⭐ TOP {len(sweet_spot)} SWEET SPOT VEHICLES:")
            for i, car in enumerate(sweet_spot, 1):
                year = car.get('year', 'N/A')
                price = car.get('price', 0)
                mileage = car.get('mileage', 0)
                title = car.get('title', 'Unknown')
                url = car.get('listing_url', 'N/A')
                
                print(f"\n{i}. {title}")
                print(f"   💰 Price: {price:,}만원 | 📅 Year: {year} | 🛣️  Mileage: {mileage:,}km")
                print(f"   🔗 Link: {url}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        asyncio.run(quick_demo())
    else:
        asyncio.run(demo_filter_tools()) 