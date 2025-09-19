#!/usr/bin/env python3
"""
Simple test to verify the query structure without API calls
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from encar_api_client import EncarAPIClient
import yaml

def test_simple_query():
    """Test just the query building without API calls"""
    print("🧪 Testing Query Structure (No API Calls)")
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
    
    # Test with filters
    print("2️⃣ With Filters (Year >= 2021, Price <= 90M)")
    print("-" * 30)
    test_filters = {'year_min': 2021, 'price_max': 90.0}
    filtered_query = client.build_api_query(test_filters)
    print(f"Query: {filtered_query}")
    print(f"Length: {len(filtered_query)} characters")
    print()
    
    # Verify the query structure
    print("3️⃣ Query Structure Verification")
    print("-" * 30)
    
    # Check for key components
    components = [
        ("Manufacturer", "벤츠"),
        ("Model Group", "GLE-클래스"),
        ("Model", "GLE-클래스 W167"),
        ("Gasoline Badge Group", "가솔린 4WD"),
        ("Diesel Badge Group", "디젤 4WD"),
        ("GLE450 Coupe", "GLE450 4MATIC 쿠페"),
        ("GLE400d Coupe", "GLE400d 4MATIC 쿠페"),
        ("AMG GLE53", "AMG GLE53 4MATIC+ 쿠페"),
        ("AMG GLE63", "AMG GLE63 S 4MATIC+ 쿠페")
    ]
    
    all_found = True
    for name, component in components:
        if component in base_query:
            print(f"✅ {name}: Found")
        else:
            print(f"❌ {name}: Missing")
            all_found = False
    
    print()
    if all_found:
        print("🎉 All required components found in query!")
        print("✅ Query structure looks correct!")
    else:
        print("⚠️  Some components missing - check query structure")
    
    print()
    print("4️⃣ Expected Benefits")
    print("-" * 30)
    print("• More precise targeting of GLE Coupe models")
    print("• Eliminates need for post-filtering by title keywords")
    print("• Should return only W167 generation GLE Coupes")
    print("• Includes both gasoline and diesel variants")
    print("• Covers all major trim levels (GLE450, GLE400d, AMG variants)")
    print()
    print("✅ Simple query test completed!")

if __name__ == "__main__":
    test_simple_query()
