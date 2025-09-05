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

def calculate_lease_true_cost(deposit: float, monthly_payment: float, term_months: int, final_payment: float = 0) -> float:
    """
    Calculate true cost for lease vehicle.
    
    Args:
        deposit: Initial deposit in 만원
        monthly_payment: Monthly payment in 만원
        term_months: Lease term in months
        final_payment: Final payment at end of lease in 만원 (optional)
    
    Returns:
        Total true cost in 만원
    """
    try:
        total_monthly_cost = monthly_payment * term_months
        true_cost = deposit + total_monthly_cost + final_payment
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
            'estimated_price': float,  # in 만원 (previously 'true_price')
            'final_payment': float,  # in 만원
            'total_cost': float  # in 만원
        }
    """
    result = {
        'is_lease': False,
        'deposit': None,
        'monthly_payment': None,
        'lease_term_months': None,
        'estimated_price': None,  # Previously 'true_price'
        'final_payment': None,  # Final payment at end of lease
        'total_cost': None
    }
    
    try:
        
        # Don't automatically set is_lease to True - let the parent function decide
        # based on whether we found meaningful lease data
        
        # Extract deposit (보증금) - Korean patterns only
        deposit_patterns = [
            r'보증금[:\s]*([\d,]+\.?[\d]*)만원',
            r'계약금[:\s]*([\d,]+\.?[\d]*)만원',
            r'초기금[:\s]*([\d,]+\.?[\d]*)만원',
            r'선수금[:\s]*([\d,]+\.?[\d]*)만원',
            r'입금[:\s]*([\d,]+\.?[\d]*)만원',
            r'인수금[:\s]*([\d,]+\.?[\d]*)만원',
            # Handle comma-separated amounts like "1,801"
            r'([\d,]+)\s*만원.*?인수',
            r'인수.*?([\d,]+)\s*만원',
            # Handle decimal patterns like "18.01"
            r'([\d,]+\.[\d]+)\s*만원.*?보증',
            r'보증.*?([\d,]+\.[\d]+)\s*만원',
            r'([\d,]+\.[\d]+)\s*만원.*?인수',
            r'인수.*?([\d,]+\.[\d]+)\s*만원',
            # Try finding large amounts (deposits are usually substantial)
            r'([1-9][\d]\.[\d]+)\s*만원',  # Numbers like 18.01, 37.38, etc.
            # Direct match for comma-separated amounts in deposit context
            r'인수금.*?([\d,]+)만원',
            r'([\d,]+)만원.*?인수금',
        ]
        
        for pattern in deposit_patterns:
            match = re.search(pattern, page_content)
            if match:
                deposit_str = match.group(1).replace(',', '')
                try:
                    # Handle comma-separated amounts
                    if ',' in deposit_str:
                        # Remove commas and convert to float
                        amount = float(deposit_str.replace(',', ''))
                    else:
                        amount = float(deposit_str)
                    
                    # For deposits, if the amount is > 1000, it's likely in thousands
                    # So 1,801 should be interpreted as 18.01 million won
                    if amount > 1000:
                        amount = amount / 100.0
                    
                    if amount and amount > 0:  # Ensure we have a valid positive amount
                        result['deposit'] = amount
                        break
                except (ValueError, TypeError):
                    continue
        
        # Extract monthly payment (월납입금) - Korean patterns only
        monthly_patterns = [
            r'월\s*납입금[:\s]*([\d,]+\.?[\d]*)만원',
            r'월\s*리스료[:\s]*([\d,]+\.?[\d]*)만원',
            r'월\s*렌트비[:\s]*([\d,]+\.?[\d]*)만원',
            r'월[:\s]*([\d,]+\.?[\d]*)만원',
            r'매월[:\s]*([\d,]+\.?[\d]*)만원',
            r'월세[:\s]*([\d,]+\.?[\d]*)만원',
            # Handle different decimal formats
            r'([\d]\.[\d]+)\s*만원.*?월',
            r'월.*?([\d]\.[\d]+)\s*만원',
            # Look for smaller amounts that could be monthly payments
            r'([1-9]\.[\d]+)\s*만원',  # Numbers like 1.67
            # Handle comma-separated amounts that are likely monthly payments (smaller amounts)
            r'([\d]{1,3})\s*만원.*?월',  # Numbers like 165 (1.65 million won)
        ]
        
        for pattern in monthly_patterns:
            match = re.search(pattern, page_content)
            if match:
                monthly_str = match.group(1).replace(',', '')
                try:
                    # Handle comma-separated amounts
                    if ',' in monthly_str:
                        # Remove commas and convert to float
                        amount = float(monthly_str.replace(',', ''))
                    else:
                        amount = float(monthly_str)
                    
                    # For monthly payments, if the amount is > 100, it's likely in thousands
                    # So 165 should be interpreted as 1.65 million won
                    if amount > 100:
                        amount = amount / 100.0
                    
                    # Monthly payments are typically smaller amounts
                    if amount and 0.5 <= amount <= 50:  # Reasonable range for monthly lease payments
                        result['monthly_payment'] = amount
                        break
                except (ValueError, TypeError):
                    continue
        
        # If no monthly payment found with patterns, try a more flexible approach for Korean content
        if not result['monthly_payment']:
            # Look for any number followed by "만원" that appears near "개월"
            flexible_monthly_pattern = r'([\d,]+\.?[\d]*)\s*만원'
            matches = re.finditer(flexible_monthly_pattern, page_content)
            for match in matches:
                amount_str = match.group(1).replace(',', '')
                try:
                    amount = float(amount_str)
                    # Check if this amount appears near "개월" text
                    match_start = match.start()
                    # Look for "개월" within 200 characters after this amount
                    context_after = page_content[match_start:match_start+200]
                    if "개월" in context_after and 0.5 <= amount <= 50:
                        result['monthly_payment'] = amount
                        break
                except (ValueError, TypeError):
                    continue
            
            # If still not found, try a more sophisticated approach for HTML with font tags
            if not result['monthly_payment']:
                # Look for numbers that appear before "만원" in the HTML
                manwon_positions = [m.start() for m in re.finditer('만원', page_content)]
                for pos in manwon_positions:
                    # Look for numbers in a larger context before "만원" (500 characters)
                    before_manwon = page_content[max(0, pos-500):pos]
                    number_pattern = r'([\d,]+\.?[\d]*)'
                    numbers_before = re.findall(number_pattern, before_manwon)
                    
                    for number_str in numbers_before:
                        try:
                            amount = float(number_str.replace(',', ''))
                            # Check if this amount appears near "개월" text
                            # Look in a broader context around the 만원 position
                            context_before = page_content[max(0, pos-500):pos]
                            context_after = page_content[pos:pos+500]
                            full_context = context_before + context_after
                            if "개월" in full_context and 0.5 <= amount <= 50:
                                # Prefer smaller amounts for monthly payments (they're typically 1-5만원)
                                if not result['monthly_payment'] or amount < result['monthly_payment']:
                                    result['monthly_payment'] = amount
                        except (ValueError, TypeError):
                            continue
                    
                    if result['monthly_payment']:
                        break
        
        # Extract lease term (계약기간) - Korean patterns only
        term_patterns = [
            r'계약기간[:\s]*(\d+)개월',
            r'리스기간[:\s]*(\d+)개월',
            r'렌트기간[:\s]*(\d+)개월',
            r'리스\s*기간[:\s]*(\d+)\s*개월',
            r'계약\s*기간[:\s]*(\d+)\s*개월',
            r'(\d+)\s*개월',
        ]
        
        for pattern in term_patterns:
            match = re.search(pattern, page_content)
            if match:
                result['lease_term_months'] = int(match.group(1))
                break
        
        # If no lease term found with patterns, try a more flexible approach for Korean content
        if not result['lease_term_months']:
            # Look for any number followed by "개월"
            flexible_term_pattern = r'(\d+)\s*개월'
            match = re.search(flexible_term_pattern, page_content)
            if match:
                term = int(match.group(1))
                # Sanity check: lease terms are typically 12-60 months
                if 12 <= term <= 60:
                    result['lease_term_months'] = term
            
            # If still not found, try a more sophisticated approach for HTML with font tags
            if not result['lease_term_months']:
                # Look for numbers that appear before "개월" in the HTML
                months_positions = [m.start() for m in re.finditer('개월', page_content)]
                for pos in months_positions:
                    # Look for numbers in the 200 characters before "개월"
                    before_months = page_content[max(0, pos-200):pos]
                    number_pattern = r'(\d+)'
                    numbers_before = re.findall(number_pattern, before_months)
                    
                    for number_str in numbers_before:
                        try:
                            term = int(number_str)
                            # Sanity check: lease terms are typically 12-60 months
                            if 12 <= term <= 60:
                                result['lease_term_months'] = term
                                break
                        except (ValueError, TypeError):
                            continue
                    
                    if result['lease_term_months']:
                        break
        
        # Extract estimated price (vehicle price) from Korean HTML
        estimated_price_patterns = [
            r'차량가격.*?([\d,]+\.?[\d]*)만원',
            r'차량가격.*?([\d,]+)\s*만원',
            r'차량가격.*?([\d,]+)만원',
            # Direct match for comma-separated amounts near 차량가격
            r'([\d,]+)만원.*?차량가격',
        ]
        
        for pattern in estimated_price_patterns:
            match = re.search(pattern, page_content)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    # Handle comma-separated amounts
                    if ',' in price_str:
                        # Remove commas and convert to float
                        amount = float(price_str.replace(',', ''))
                    else:
                        amount = float(price_str)
                    
                    if amount and amount > 0:
                        # For estimated price, if the amount is > 1000, it's likely in thousands
                        # So 8,825 should be interpreted as 88.25 million won
                        if amount > 1000:
                            amount = amount / 100.0
                        result['estimated_price'] = amount
                        break
                except (ValueError, TypeError):
                    continue
        
        # If no estimated price found with patterns, try a more sophisticated approach for Korean content
        if not result['estimated_price']:
            # Look for numbers that appear before "차량가격" in the HTML
            vehicle_price_positions = [m.start() for m in re.finditer('차량가격', page_content)]
            for pos in vehicle_price_positions:
                # Look for numbers in the 500 characters before "차량가격"
                before_vehicle_price = page_content[max(0, pos-500):pos]
                number_pattern = r'([\d,]+\.?[\d]*)'
                numbers_before = re.findall(number_pattern, before_vehicle_price)
                
                for number_str in numbers_before:
                    try:
                        amount = float(number_str.replace(',', ''))
                        # Vehicle prices are typically large amounts (over 50만원)
                        if amount and amount > 50:
                            result['estimated_price'] = amount
                            break
                    except (ValueError, TypeError):
                        continue
                
                if result['estimated_price']:
                    break
        
        # Extract final payment (리스 만기 후 비용) - Korean patterns
        final_payment_patterns = [
            r'리스\s*만기\s*후\s*비용.*?([\d,]+\.?[\d]*)만원',
            r'만기\s*후\s*비용.*?([\d,]+\.?[\d]*)만원',
            r'구매.*?([\d,]+\.?[\d]*)만원',  # "구매 (리스사에게 지급)" context
            r'반납.*?([\d,]+\.?[\d]*)만원',  # "반납 (보증금 환급)" context
            # Look for amounts near "리스 만기 후 비용" or "만기 후 비용"
            r'([\d,]+\.?[\d]*)만원.*?만기\s*후',
            r'만기\s*후.*?([\d,]+\.?[\d]*)만원',
            # Handle comma-separated amounts
            r'([\d,]+)\s*만원.*?만기',
            r'만기.*?([\d,]+)\s*만원',
        ]
        
        for pattern in final_payment_patterns:
            match = re.search(pattern, page_content)
            if match:
                payment_str = match.group(1).replace(',', '')
                try:
                    # Handle comma-separated amounts
                    if ',' in payment_str:
                        # Remove commas and convert to float
                        amount = float(payment_str.replace(',', ''))
                    else:
                        amount = float(payment_str)
                    
                    # For final payments, if the amount is > 1000, it's likely in thousands
                    # So 2,301 should be interpreted as 23.01 million won
                    if amount > 1000:
                        amount = amount / 100.0
                    
                    if amount and amount > 0:
                        result['final_payment'] = amount
                        break
                except (ValueError, TypeError):
                    continue
        
        # If no final payment found with patterns, try a more flexible approach
        if not result['final_payment']:
            # Look for amounts that appear near "만기 후" or "구매" or "반납" keywords
            manwon_positions = [m.start() for m in re.finditer('만원', page_content)]
            for pos in manwon_positions:
                # Look for numbers in a larger context around "만원" (500 characters)
                before_manwon = page_content[max(0, pos-500):pos]
                after_manwon = page_content[pos:pos+500]
                full_context = before_manwon + after_manwon
                
                # Check if this context contains final payment keywords
                if any(keyword in full_context for keyword in ["만기 후", "구매", "반납", "리스 만기"]):
                    number_pattern = r'([\d,]+\.?[\d]*)'
                    numbers_before = re.findall(number_pattern, before_manwon)
                    
                    for number_str in numbers_before:
                        try:
                            amount = float(number_str.replace(',', ''))
                            # Final payments are typically substantial amounts (10-50만원)
                            if amount > 1000 and 10 <= amount/100.0 <= 50:
                                result['final_payment'] = amount / 100.0
                                break
                        except (ValueError, TypeError):
                            continue
                    
                    if result['final_payment']:
                        break
        
        # Fallback: If deposit and estimated price are still not found, try to extract from remaining amounts
        if not result['deposit'] or not result['estimated_price']:
            # Find all comma-separated amounts in the content (including those with spaces)
            all_amounts = re.findall(r'([\d,]+)\s*만원', page_content)
            large_amounts = []
            
            for amount_str in all_amounts:
                try:
                    amount = float(amount_str.replace(',', ''))
                    if amount > 1000:  # Large amounts that could be deposits or true prices
                        large_amounts.append(amount)
                except (ValueError, TypeError):
                    continue
            
            # Sort by amount (largest first)
            large_amounts.sort(reverse=True)
            
            
            
            if len(large_amounts) >= 2:
                # Look for amounts near "인수금" (deposit) and "차량가격" (vehicle price)
                for amount in large_amounts:
                    amount_str = f"{int(amount):,}"
                    
                    # Check if this amount appears near "인수금" (deposit context)
                    if not result['deposit'] and (f"{amount_str}만원" in page_content or f"{amount_str} 만원" in page_content):
                        # Look for "인수금" near this amount
                        amount_positions = [m.start() for m in re.finditer(re.escape(f"{amount_str}만원"), page_content)]
                        amount_positions.extend([m.start() for m in re.finditer(re.escape(f"{amount_str} 만원"), page_content)])
                        for pos in amount_positions:
                            context_before = page_content[max(0, pos-200):pos]
                            context_after = page_content[pos:pos+200]
                            if "인수금" in context_before or "인수금" in context_after:
                                result['deposit'] = amount / 100.0  # Convert to million won
                                break
                    
                    # Check if this amount appears near "차량가격" (vehicle price context)
                    if not result['estimated_price']:
                        # First, try to find this amount in the content
                        amount_found = False
                        amount_positions = []
                        
                        # Look for both formats: with and without space
                        if f"{amount_str}만원" in page_content:
                            amount_positions.extend([m.start() for m in re.finditer(re.escape(f"{amount_str}만원"), page_content)])
                            amount_found = True
                        if f"{amount_str} 만원" in page_content:
                            amount_positions.extend([m.start() for m in re.finditer(re.escape(f"{amount_str} 만원"), page_content)])
                            amount_found = True
                        
                        if amount_found:
                            # Check if this amount appears near "차량가격"
                            for pos in amount_positions:
                                context_before = page_content[max(0, pos-200):pos]
                                context_after = page_content[pos:pos+200]
                                if "차량가격" in context_before or "차량가격" in context_after:
                                    result['estimated_price'] = amount / 100.0  # Convert to million won
                                    break
                        
                        # Also check if this amount appears after "차량가격" in a larger context
                        if not result['estimated_price']:
                            vehicle_price_positions = [m.start() for m in re.finditer('차량가격', page_content)]
                            for vp_pos in vehicle_price_positions:
                                # Look in a larger context after "차량가격" (500 characters)
                                context_after_vp = page_content[vp_pos:vp_pos+500]
                                if f"{amount_str}만원" in context_after_vp or f"{amount_str} 만원" in context_after_vp:
                                    result['estimated_price'] = amount / 100.0  # Convert to million won
                                    break
                
                # Use the largest amount as estimated price
                if not result['estimated_price'] and large_amounts:
                    result['estimated_price'] = large_amounts[0] / 100.0
                # Use the second largest amount as deposit
                if not result['deposit'] and len(large_amounts) >= 2:
                    result['deposit'] = large_amounts[1] / 100.0
            elif len(large_amounts) == 1:
                # Use the only large amount as estimated price
                if not result['estimated_price']:
                    result['estimated_price'] = large_amounts[0] / 100.0  # Convert to million won
        
        # Calculate total cost if we have all components
        if result['deposit'] and result['monthly_payment'] and result['lease_term_months']:
            result['total_cost'] = calculate_lease_true_cost(
                result['deposit'], 
                result['monthly_payment'], 
                result['lease_term_months'],
                result.get('final_payment', 0)
            )
        
        # Set is_lease to True if we found meaningful lease data
        if result['deposit'] or result['monthly_payment'] or result['lease_term_months']:
            result['is_lease'] = True
        
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