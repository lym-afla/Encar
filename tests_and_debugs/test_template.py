#!/usr/bin/env python3
"""
Test Template
Template for creating test files in the tests_and_debugs subfolder
"""

import asyncio
import logging
import yaml
import sys
import os

# Add parent directory to path so we can import modules from the root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now you can import any module from the root directory
from encar_scraper_api import EncarScraperAPI
from data_storage import EncarDatabase
from monetary_utils import extract_lease_components_from_page_content

async def test_function():
    """Your test function here"""
    
    # Set up logging
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')
    
    # Load config from parent directory
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    print("🧪 Your test here...")
    print("=" * 50)
    
    # Your test code here
    async with EncarScraperAPI(config) as scraper:
        # Test your functionality
        pass
    
    print("✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_function()) 