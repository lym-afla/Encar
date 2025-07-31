#!/usr/bin/env python3
"""
DEPRECATED: Legacy lease detail scraper
This module is deprecated and will be removed in future versions.
Lease detection is now integrated into encar_scraper_api.py.

Lease Detail Scraper for Encar
Extracts lease information from vehicle detail pages.
"""

import warnings
warnings.warn(
    "lease_detail_scraper.py is deprecated. Lease detection is now integrated into encar_scraper_api.py.",
    DeprecationWarning,
    stacklevel=2
)

import asyncio
import logging
import re
from datetime import datetime
from typing import Dict, Optional, Tuple
from playwright.async_api import async_playwright

class LeaseDetailScraper:
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    async def extract_lease_details(self, listing_url: str) -> Optional[Dict]:
        """Extract complete lease details from vehicle detail page"""
        try:
            self.logger.info(f"Extracting lease details from: {listing_url}")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=self.config['browser']['headless']
                )
                context = await browser.new_context()
                page = await context.new_page()
                
                # Navigate to the detail page
                await page.goto(listing_url)
                await page.wait_for_timeout(3000)
                
                # Check if this is a lease vehicle
                is_lease = await self.detect_lease_on_page(page)
                
                if not is_lease:
                    await browser.close()
                    return {
                        'is_lease': False,
                        'price_type': 'purchase'
                    }
                
                # Extract lease details
                lease_details = await self.extract_lease_terms(page)
                
                await browser.close()
                
                if lease_details:
                    lease_details['is_lease'] = True
                    lease_details['price_type'] = 'lease'
                    self.logger.info(f"Extracted lease details: {lease_details}")
                
                return lease_details
                
        except Exception as e:
            self.logger.error(f"Error extracting lease details from {listing_url}: {e}")
            return None
    
    async def detect_lease_on_page(self, page) -> bool:
        """Detect if the vehicle page shows lease terms"""
        try:
            # Look for lease-specific Korean terms
            lease_keywords = [
                "리스", "렌트", "월 납입금", "보증금", "리스료", 
                "월리스", "리스기간", "월 렌트비", "렌트료"
            ]
            
            page_content = await page.content()
            
            for keyword in lease_keywords:
                if keyword in page_content:
                    self.logger.info(f"Lease keyword '{keyword}' found on page")
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Error detecting lease on page: {e}")
            return False
    
    async def extract_lease_terms(self, page) -> Optional[Dict]:
        """Extract lease deposit, monthly payment, and term from page"""
        try:
            lease_info = {
                'deposit': 0,
                'monthly_payment': 0,
                'lease_term_months': 0,
                'total_cost': 0
            }
            
            # Extract deposit (보증금) - Based on user's example: 37.38 million won
            deposit = await self.extract_deposit(page)
            if deposit:
                lease_info['deposit'] = deposit
                self.logger.info(f"✅ Deposit found: {deposit}만원")
            else:
                self.logger.warning("❌ Deposit not found")
            
            # Extract monthly payment (월 납입금) - Based on user's example: 1.67 million won
            monthly_payment = await self.extract_monthly_payment(page)
            if monthly_payment:
                lease_info['monthly_payment'] = monthly_payment
                self.logger.info(f"✅ Monthly payment found: {monthly_payment}만원")
            else:
                self.logger.warning("❌ Monthly payment not found")
            
            # Extract lease term (리스 기간) - Based on user's example: 27 months
            lease_term = await self.extract_lease_term(page)
            if lease_term:
                lease_info['lease_term_months'] = lease_term
                self.logger.info(f"✅ Lease term found: {lease_term} months")
            else:
                self.logger.warning("❌ Lease term not found")
            
            # Debug: Show what we found
            self.logger.info(f"📊 Extracted info: deposit={lease_info['deposit']}, "
                           f"monthly={lease_info['monthly_payment']}, term={lease_info['lease_term_months']}")
            
            # Calculate total cost: deposit + (monthly × term)
            # Allow partial calculation if we have at least monthly and term
            if lease_info['monthly_payment'] and lease_info['lease_term_months']:
                total_monthly_cost = lease_info['monthly_payment'] * lease_info['lease_term_months']
                lease_info['total_monthly_cost'] = total_monthly_cost
                lease_info['total_cost'] = lease_info['deposit'] + total_monthly_cost
                
                self.logger.info(f"💰 Calculated lease cost: "
                               f"Deposit {lease_info['deposit']}만원 + "
                               f"Monthly {lease_info['monthly_payment']}만원 × {lease_info['lease_term_months']}months = "
                               f"Total {lease_info['total_cost']}만원")
                               
                return lease_info
            else:
                self.logger.error("❌ Could not calculate total cost - missing monthly payment or term")
                return None
            
        except Exception as e:
            self.logger.error(f"Error extracting lease terms: {e}")
            return None
    
    async def extract_deposit(self, page) -> Optional[float]:
        """Extract deposit amount (보증금)"""
        try:
            page_content = await page.content()
            
            # Look for deposit patterns in Korean - More comprehensive patterns
            deposit_patterns = [
                # Standard patterns
                r"보증금[:\s]*([0-9,]+\.?[0-9]*)\s*만원",
                r"선수금[:\s]*([0-9,]+\.?[0-9]*)\s*만원", 
                r"계약금[:\s]*([0-9,]+\.?[0-9]*)\s*만원",
                
                # More specific patterns based on common layouts
                r"보증금.*?([0-9,]+\.?[0-9]*)\s*만원",
                r"계약.*?보증금.*?([0-9,]+\.?[0-9]*)\s*만원",
                r"입금.*?([0-9,]+\.?[0-9]*)\s*만원",
                
                # Handle decimal patterns like "37.38"
                r"([0-9,]+\.[0-9]+)\s*만원.*?보증",
                r"보증.*?([0-9,]+\.[0-9]+)\s*만원",
                
                # Try finding large amounts (deposits are usually substantial)
                r"([3-9][0-9]\.[0-9]+)\s*만원",  # Numbers like 37.38, 45.67, etc.
                r"([0-9]{2,3}\.[0-9]+)\s*만원",  # Two or three digit decimals
            ]
            
            for pattern in deposit_patterns:
                matches = re.finditer(pattern, page_content)
                for match in matches:
                    amount_str = match.group(1).replace(',', '')
                    try:
                        amount = float(amount_str)
                        # Deposits are typically large amounts (over 1000만원)
                        if amount > 1000:  # Filter out small amounts that might not be deposits
                            self.logger.info(f"Found potential deposit: {amount}만원")
                            return amount
                        elif amount > 10 and amount < 100:  # Could be written in different units
                            # Might be in units of 100만원 (e.g., 37.38 = 3738만원)
                            self.logger.info(f"Found deposit (decimal format): {amount}만원")
                            return amount
                    except ValueError:
                        continue
            
            # If no specific deposit patterns found, look for any large monetary amounts
            # that could be deposits
            large_amount_pattern = r"([3-9][0-9]\.[0-9]{2})\s*만원"
            matches = re.finditer(large_amount_pattern, page_content)
            for match in matches:
                amount_str = match.group(1)
                try:
                    amount = float(amount_str)
                    self.logger.info(f"Found large amount (potential deposit): {amount}만원")
                    return amount
                except ValueError:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting deposit: {e}")
            return None
    
    async def extract_monthly_payment(self, page) -> Optional[float]:
        """Extract monthly payment amount (월 납입금)"""
        try:
            page_content = await page.content()
            
            # Look for monthly payment patterns - More comprehensive
            monthly_patterns = [
                # Standard patterns
                r"월\s*납입금[:\s]*([0-9,]+\.?[0-9]*)\s*만원",
                r"월\s*리스료[:\s]*([0-9,]+\.?[0-9]*)\s*만원",
                r"월\s*렌트비[:\s]*([0-9,]+\.?[0-9]*)\s*만원",
                r"월[:\s]*([0-9,]+\.?[0-9]*)\s*만원",
                
                # More specific patterns
                r"월.*?([0-9,]+\.?[0-9]*)\s*만원",
                r"매월.*?([0-9,]+\.?[0-9]*)\s*만원",
                r"월세.*?([0-9,]+\.?[0-9]*)\s*만원",
                
                # Handle different decimal formats
                r"([0-9]\.[0-9]+)\s*만원.*?월",
                r"월.*?([0-9]\.[0-9]+)\s*만원",
                
                # Look for smaller amounts that could be monthly payments
                r"([1-9]\.[0-9]+)\s*만원",  # Numbers like 1.67
                r"([0-9]{1,2}\.[0-9]+)\s*만원",  # One or two digit decimals
            ]
            
            for pattern in monthly_patterns:
                matches = re.finditer(pattern, page_content)
                for match in matches:
                    amount_str = match.group(1).replace(',', '')
                    try:
                        amount = float(amount_str)
                        # Monthly payments are typically smaller amounts
                        if 0.5 <= amount <= 50:  # Reasonable range for monthly lease payments
                            self.logger.info(f"Found monthly payment: {amount}만원")
                            return amount
                        elif 100 <= amount <= 500:  # Could be in different format (e.g., 167 = 1.67)
                            # Convert from format like 167 to 1.67
                            converted = amount / 100
                            if 0.5 <= converted <= 50:
                                self.logger.info(f"Found monthly payment (converted): {converted}만원 (from {amount})")
                                return converted
                    except ValueError:
                        continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting monthly payment: {e}")
            return None
    
    async def extract_lease_term(self, page) -> Optional[int]:
        """Extract lease term in months (리스 기간)"""
        try:
            # Look for lease term patterns
            term_patterns = [
                r"리스\s*기간[:\s]*([0-9]+)\s*개월",
                r"계약\s*기간[:\s]*([0-9]+)\s*개월",
                r"([0-9]+)\s*개월",
                r"([0-9]+)\s*month"
            ]
            
            page_content = await page.content()
            
            for pattern in term_patterns:
                match = re.search(pattern, page_content)
                if match:
                    term = int(match.group(1))
                    # Sanity check: lease terms are typically 12-60 months
                    if 12 <= term <= 60:
                        self.logger.info(f"Found lease term: {term} months")
                        return term
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting lease term: {e}")
            return None

async def test_lease_scraper():
    """Test the lease scraper with the user's example"""
    print("=== TESTING LEASE DETAIL SCRAPER ===")
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Load config (simplified for testing)
    config = {
        'browser': {
            'headless': False  # Show browser for debugging
        }
    }
    
    scraper = LeaseDetailScraper(config)
    
    # Test with the user's example URL
    test_url = "https://fem.encar.com/cars/detail/39743923"
    
    print(f"Testing lease extraction on: {test_url}")
    
    lease_details = await scraper.extract_lease_details(test_url)
    
    if lease_details:
        print("\n✅ LEASE DETAILS EXTRACTED:")
        print(f"   Is Lease: {lease_details.get('is_lease', False)}")
        print(f"   Deposit: {lease_details.get('deposit', 0):,.1f}만원")
        print(f"   Monthly Payment: {lease_details.get('monthly_payment', 0):,.1f}만원")
        print(f"   Lease Term: {lease_details.get('lease_term_months', 0)} months")
        print(f"   Total Monthly Cost: {lease_details.get('total_monthly_cost', 0):,.1f}만원")
        print(f"   TOTAL COST: {lease_details.get('total_cost', 0):,.1f}만원")
        
        # Compare with user's calculation
        print(f"\n📊 USER'S CALCULATION:")
        print(f"   Deposit: 37.38만원")
        print(f"   Monthly: 1.67만원 × 27 months = 45.09만원")
        print(f"   Total: 37.38 + 45.09 = 82.47만원")
    else:
        print("❌ Could not extract lease details")

if __name__ == "__main__":
    asyncio.run(test_lease_scraper()) 