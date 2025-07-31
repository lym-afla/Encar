#!/usr/bin/env python3
"""
Monetary Utilities for Korean Won Handling
Handles Korean monetary units in 만원 (million won) format consistently
"""

import re
import logging
from typing import Optional, Union

def parse_korean_price(price_value: Union[str, int, float]) -> Optional[float]:
    """
    Parse Korean price and return in 만원 (million won) format.
    
    Args:
        price_value: Price in various formats:
            - "180만원" -> 180.0
            - "1,800만원" -> 1800.0
            - 180 -> 180.0 (assumes 만원)
            - "1,800,000원" -> 180.0 (converts from won)
    
    Returns:
        Price in 만원 as float, or None if parsing fails
    """
    if not price_value:
        return None
    
    try:
        if isinstance(price_value, (int, float)):
            # Assume it's already in 만원 units
            return float(price_value)
        
        price_str = str(price_value).strip()
        
        # Handle "원" suffix (actual won amounts) - convert to 만원
        if '원' in price_str and '만원' not in price_str:
            # Extract numeric value from "1,800,000원" format
            numeric = re.sub(r'[^\d]', '', price_str.replace('원', ''))
            if numeric:
                won_amount = int(numeric)
                return won_amount / 10000.0  # Convert to 만원
            return None
        
        # Handle "만원" suffix (million won units)
        if '만원' in price_str:
            numeric = re.sub(r'[^\d.]', '', price_str.replace('만원', ''))
            if numeric:
                return float(numeric)
            return None
        
        # Handle plain numbers (assume 만원 units)
        numeric = re.sub(r'[^\d.]', '', price_str)
        if numeric:
            return float(numeric)
        
        return None
        
    except Exception as e:
        logging.warning(f"Could not parse Korean price '{price_value}': {e}")
        return None

def format_price_to_manwon(price_value: Union[int, float]) -> str:
    """
    Format price value to Korean 만원 format.
    
    Args:
        price_value: Price in 만원 (e.g., 180.5)
    
    Returns:
        Formatted string (e.g., "180.5만원")
    """
    try:
        return f"{price_value:,.1f}만원"
    except Exception as e:
        logging.warning(f"Could not format price '{price_value}': {e}")
        return "0.0만원"

def format_price_to_manwon_compact(price_value: Union[int, float]) -> str:
    """
    Format price value to compact Korean 만원 format.
    
    Args:
        price_value: Price in 만원 (e.g., 180.5)
    
    Returns:
        Compact formatted string (e.g., "180.5만원")
    """
    try:
        return f"{price_value:.1f}만원"
    except Exception as e:
        logging.warning(f"Could not format price '{price_value}': {e}")
        return "0.0만원"

def calculate_lease_true_cost(deposit: float, monthly_payment: float, term_months: int) -> float:
    """
    Calculate true cost for lease vehicle.
    
    Args:
        deposit: Initial deposit in 만원
        monthly_payment: Monthly payment in 만원
        term_months: Lease term in months
    
    Returns:
        Total true cost in 만원
    """
    try:
        total_monthly_cost = monthly_payment * term_months
        true_cost = deposit + total_monthly_cost
        return true_cost
    except Exception as e:
        logging.warning(f"Could not calculate lease true cost: {e}")
        return 0.0

def extract_lease_components_from_page_content(page_content: str) -> dict:
    """
    Extract lease components from page content.
    
    Args:
        page_content: HTML content of the vehicle page
    
    Returns:
        Dictionary with lease components in 만원:
        {
            'is_lease': bool,
            'deposit': float,  # in 만원
            'monthly_payment': float,  # in 만원
            'lease_term_months': int,
            'total_cost': float  # in 만원
        }
    """
    result = {
        'is_lease': False,
        'deposit': None,
        'monthly_payment': None,
        'lease_term_months': None,
        'total_cost': None
    }
    
    try:
        # Look for lease-related keywords
        lease_keywords = ['리스', '렌트', '월세', '월납입금', '보증금', '계약금']
        has_lease_content = any(keyword in page_content for keyword in lease_keywords)
        
        if not has_lease_content:
            return result
        
        result['is_lease'] = True
        
        # Extract deposit (보증금)
        deposit_patterns = [
            r'보증금[:\s]*([\d,]+)만원',
            r'계약금[:\s]*([\d,]+)만원',
            r'초기금[:\s]*([\d,]+)만원'
        ]
        
        for pattern in deposit_patterns:
            match = re.search(pattern, page_content)
            if match:
                deposit_str = match.group(1).replace(',', '')
                result['deposit'] = float(deposit_str)
                break
        
        # Extract monthly payment (월납입금)
        monthly_patterns = [
            r'월납입금[:\s]*([\d,]+)만원',
            r'월세[:\s]*([\d,]+)만원',
            r'월납[:\s]*([\d,]+)만원'
        ]
        
        for pattern in monthly_patterns:
            match = re.search(pattern, page_content)
            if match:
                monthly_str = match.group(1).replace(',', '')
                result['monthly_payment'] = float(monthly_str)
                break
        
        # Extract lease term (계약기간)
        term_patterns = [
            r'계약기간[:\s]*(\d+)개월',
            r'리스기간[:\s]*(\d+)개월',
            r'렌트기간[:\s]*(\d+)개월'
        ]
        
        for pattern in term_patterns:
            match = re.search(pattern, page_content)
            if match:
                result['lease_term_months'] = int(match.group(1))
                break
        
        # Calculate total cost if we have all components
        if result['deposit'] and result['monthly_payment'] and result['lease_term_months']:
            result['total_cost'] = calculate_lease_true_cost(
                result['deposit'], 
                result['monthly_payment'], 
                result['lease_term_months']
            )
        
        return result
        
    except Exception as e:
        logging.warning(f"Error extracting lease components: {e}")
        return result

def is_lease_vehicle_by_heuristics(listing_data: dict) -> bool:
    """
    Determine if a vehicle is likely a lease based on heuristics.
    
    Args:
        listing_data: Vehicle listing data
    
    Returns:
        True if likely a lease vehicle
    """
    try:
        # Check for lease keywords in title
        title = listing_data.get('title', '').lower()
        lease_keywords = ['리스', '렌트', '월세']
        if any(keyword in title for keyword in lease_keywords):
            return True
        
        # Check for suspiciously round prices (common in lease estimates)
        price = listing_data.get('price', 0)
        if isinstance(price, (int, float)):
            # Check if price ends in 00 or 77 (common lease estimate patterns)
            price_str = str(int(price))
            if price_str.endswith('00') or price_str.endswith('77'):
                return True
        
        # Check for recent vehicles with moderate prices (potential lease candidates)
        year = listing_data.get('year', 0)
        if isinstance(year, (int, float)) and year > 10000:
            year = int(year / 100)  # Convert YYYYMM format
        
        if year >= 2019 and 1000 <= price <= 8000:
            return True
        
        return False
        
    except Exception as e:
        logging.warning(f"Error in lease heuristics: {e}")
        return False

# Legacy functions for backward compatibility (deprecated)
def convert_manwon_to_won(manwon_value: Union[int, float, str]) -> int:
    """
    DEPRECATED: Convert 만원 to won (for backward compatibility)
    Use parse_korean_price() instead.
    """
    import warnings
    warnings.warn(
        "convert_manwon_to_won() is deprecated. Use parse_korean_price() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    result = parse_korean_price(manwon_value)
    if result is not None:
        return int(result * 10000)  # Convert back to won for legacy compatibility
    return 0

def convert_won_to_manwon(won_amount: int) -> float:
    """
    DEPRECATED: Convert won to 만원 (for backward compatibility)
    Use parse_korean_price() instead.
    """
    import warnings
    warnings.warn(
        "convert_won_to_manwon() is deprecated. Use parse_korean_price() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    return won_amount / 10000.0

def format_won_to_manwon(won_amount: int) -> str:
    """
    DEPRECATED: Format won to 만원 (for backward compatibility)
    Use format_price_to_manwon() instead.
    """
    import warnings
    warnings.warn(
        "format_won_to_manwon() is deprecated. Use format_price_to_manwon() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    manwon = won_amount / 10000.0
    return format_price_to_manwon(manwon)

def format_won_to_won(won_amount: int) -> str:
    """
    DEPRECATED: Format won amount (for backward compatibility)
    Use format_price_to_manwon() instead.
    """
    import warnings
    warnings.warn(
        "format_won_to_won() is deprecated. Use format_price_to_manwon() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    manwon = won_amount / 10000.0
    return format_price_to_manwon(manwon) 