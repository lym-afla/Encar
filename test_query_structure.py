#!/usr/bin/env python3
"""
Test the query structure without making API calls
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from encar_api_client import EncarAPIClient
import yaml

def test_query_structure():
    """Test the query structure"""
    print("🧪 Testing Query Structure")
    print("=" * 50)
    
    # Load config
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return
    
    client = EncarAPIClient(config)
    
    # Test base query
    print("1️⃣ Base Query (No Filters)")
    print("-" * 30)
    base_query = client.build_api_query()
    print(f"Query: {base_query}")
    print(f"Length: {len(base_query)} characters")
    print()
    
    # Test with year filter
    print("2️⃣ With Year Filter (2021+)")
    print("-" * 30)
    year_query = client.build_api_query({'year_min': 2021})
    print(f"Query: {year_query}")
    print(f"Length: {len(year_query)} characters")
    print()
    
    # Test with price filter
    print("3️⃣ With Price Filter (≤90M)")
    print("-" * 30)
    price_query = client.build_api_query({'price_max': 90.0})
    print(f"Query: {price_query}")
    print(f"Length: {len(price_query)} characters")
    print()
    
    # Test with both filters
    print("4️⃣ With Both Filters (2021+, ≤90M)")
    print("-" * 30)
    both_query = client.build_api_query({'year_min': 2021, 'price_max': 90.0})
    print(f"Query: {both_query}")
    print(f"Length: {len(both_query)} characters")
    print()
    
    # Analyze the query structure
    print("5️⃣ Query Structure Analysis")
    print("-" * 30)
    print("The new base query targets:")
    print("  • Manufacturer: 벤츠 (Mercedes-Benz)")
    print("  • Model Group: GLE-클래스 (GLE Class)")
    print("  • Model: GLE-클래스 W167 (GLE Class W167)")
    print("  • Badge Groups:")
    print("    - 가솔린 4WD (Gasoline 4WD):")
    print("      • GLE450 4MATIC 쿠페")
    print("      • AMG GLE53 4MATIC+ 쿠페")
    print("      • AMG GLE63 S 4MATIC+ 쿠페")
    print("    - 디젤 4WD (Diesel 4WD):")
    print("      • GLE450d 4MATIC 쿠페")
    print("      • GLE400d 4MATIC 쿠페")
    print()
    print("This should eliminate the need for post-filtering by title keywords!")
    print("✅ Query structure test completed!")

if __name__ == "__main__":
    test_query_structure()
