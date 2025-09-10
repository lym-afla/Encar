#!/usr/bin/env python3
"""
Test script for closure scanner debugging
"""

import asyncio
import logging
import yaml
import sys
import os
from datetime import datetime, timedelta

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_storage import EncarDatabase

async def test_closure_scanner():
    """Test the closure scanner with debugging"""
    print("🧪 Testing Closure Scanner Database Access")
    print("=" * 50)
    
    # Load config
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return
    
    # Test database connection
    db_path = config.get('database', {}).get('filename', 'encar_listings.db')
    print(f"📁 Database path: {db_path}")
    
    if os.path.exists(db_path):
        file_size = os.path.getsize(db_path)
        print(f"✅ Database file exists ({file_size:,} bytes)")
    else:
        print(f"❌ Database file not found: {db_path}")
        return
    
    # Initialize database
    db = EncarDatabase(db_path)
    
    # Test basic queries
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total listings
            cursor.execute("SELECT COUNT(*) FROM listings")
            total_count = cursor.fetchone()[0]
            print(f"📊 Total listings: {total_count}")
            
            # Active listings
            cursor.execute("SELECT COUNT(*) FROM listings WHERE is_closed = 0")
            active_count = cursor.fetchone()[0]
            print(f"📊 Active listings: {active_count}")
            
            # Closed listings
            cursor.execute("SELECT COUNT(*) FROM listings WHERE is_closed = 1")
            closed_count = cursor.fetchone()[0]
            print(f"📊 Closed listings: {closed_count}")
            
            # Sample of recent listings
            cursor.execute("""
                SELECT car_id, title, first_seen, is_closed 
                FROM listings 
                ORDER BY first_seen DESC 
                LIMIT 5
            """)
            recent = cursor.fetchall()
            
            print(f"\n📋 Sample of recent listings:")
            for i, (car_id, title, first_seen, is_closed) in enumerate(recent, 1):
                status = "🔒 CLOSED" if is_closed else "✅ ACTIVE"
                print(f"  {i}. {car_id} - {title[:40]}... - {first_seen} - {status}")
            
            # Test age filtering
            print(f"\n🔍 Testing age filtering:")
            cutoff_date = datetime.now() - timedelta(days=7)
            print(f"   Cutoff date (7 days ago): {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
            
            cursor.execute("""
                SELECT car_id, first_seen, 
                       (julianday('now') - julianday(first_seen)) as days_old
                FROM listings 
                WHERE is_closed = 0
                ORDER BY first_seen DESC
                LIMIT 10
            """)
            age_test = cursor.fetchall()
            
            print(f"   Recent active listings with age:")
            for car_id, first_seen, days_old in age_test:
                age_status = "OLD" if days_old >= 7 else "NEW"
                print(f"     {car_id}: {first_seen} ({days_old:.1f} days old) - {age_status}")
            
    except Exception as e:
        print(f"❌ Database query error: {e}")
        return
    
    print(f"\n✅ Database test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_closure_scanner())
