#!/usr/bin/env python3
"""
Debug Flexible Patterns
Debug the lease extraction patterns with detailed matching information
"""

import sys
import os
import re

# Add parent directory to path so we can import modules from the root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def debug_patterns():
    """Debug pattern matching with detailed information"""
    print("🔍 Debugging Lease Extraction Patterns")
    print("=" * 50)
    
    # Actual Korean HTML content from the user
    html_content = """
    <ul class="DetailLeaseRent_list_leaserent__nzGzL">
        <li>
            <strong class="DetailLeaseRent_tit__q3gJK">차량 계약 시 비용</strong>
            <span class="DetailLeaseRent_txt__70-lf">인수금 (판매자에게 지급)</span>
            <span class="DetailLeaseRent_price__DxyTw">1,801만원</span>
        </li>
        <li>
            <strong class="DetailLeaseRent_tit__q3gJK">운행기간 동안 비용</strong>
            <span class="DetailLeaseRent_txt__70-lf">
                <span class="DetailLease_txt__KidB6">월리스료 165만원<span class="DetailLease_ico_x__hygNL"></span>26개월</span>
            </span>
            <span class="DetailLeaseRent_price__DxyTw">4,290만원</span>
        </li>
        <li>
            <strong class="DetailLeaseRent_tit__q3gJK">
                <label for="rentPrice01">리스 만기 후 비용</label>
                <button type="button" data-enlog-dt-eventnamegroup="리스렌트정보">
                    <span class="blind">리스 만기 후 비용</span>
                    <span class="DetailLeaseRent_ico_question__QZ91a"></span>
                </button>
            </strong>
            <span class="DetailLeaseRent_txt__70-lf">
                <div class="DetailLease_txt__KidB6 SelectBox_uiselect_size_h40__cLgHK">
                    <select name="leasePrice" id="leasePrice" class="SelectBox_uiselectbox_drop__JnVWV">
                        <option value="001">구매 (리스사에게 지급)</option>
                        <option value="002">반납 (보증금 환급)</option>
                    </select>
                </div>
            </span>
            <span class="DetailLeaseRent_price__DxyTw">2,301만원</span>
        </li>
    </ul>
    
    <ul class="DetailSummaryLeaseRent_list__kS+K3">
        <li>
            <p>인수금<button type="button" data-enlog-dt-eventnamegroup="플로팅">
                <span class="blind">인수금자세히 보기</span>
                <span class="DetailSummaryLeaseRent_ico_question__QEonZ"></span>
            </button></p>
            <span>
                <span class="DetailSummaryLeaseRent_price__yITp6">1,801 만원</span>
            </span>
        </li>
        <li>
            <p>차량가격<button type="button" data-enlog-dt-eventnamegroup="플로팅">
                <span class="blind">차량 가격 자세히 보기</span>
                <span class="DetailSummaryLeaseRent_ico_question__QEonZ"></span>
            </button></p>
            <span>8,825 만원</span>
        </li>
    </ul>
    """
    
    print("📄 Testing with Korean HTML content...")
    print(f"Content length: {len(html_content)} characters")
    
    # Test deposit patterns
    print("\n🔍 Testing Deposit Patterns:")
    deposit_patterns = [
        r'보증금[:\s]*([\d,]+\.?[\d]*)만원',
        r'계약금[:\s]*([\d,]+\.?[\d]*)만원',
        r'초기금[:\s]*([\d,]+\.?[\d]*)만원',
        r'선수금[:\s]*([\d,]+\.?[\d]*)만원',
        r'입금[:\s]*([\d,]+\.?[\d]*)만원',
        r'인수금[:\s]*([\d,]+\.?[\d]*)만원',
        r'([\d,]+\.[\d]+)\s*만원.*?보증',
        r'보증.*?([\d,]+\.[\d]+)\s*만원',
        r'([\d,]+\.[\d]+)\s*만원.*?인수',
        r'인수.*?([\d,]+\.[\d]+)\s*만원',
        r'([1-9][\d]\.[\d]+)\s*만원',
        # Add missing patterns
        r'인수금.*?([\d,]+)만원',
        r'([\d,]+)만원.*?인수금',
        r'([\d,]+)\s*만원.*?인수',
        r'인수.*?([\d,]+)\s*만원',
    ]
    
    for i, pattern in enumerate(deposit_patterns):
        match = re.search(pattern, html_content)
        if match:
            print(f"   ✅ Pattern {i+1}: {pattern}")
            print(f"      Matched: '{match.group(0)}' -> {match.group(1)}")
        else:
            print(f"   ❌ Pattern {i+1}: {pattern}")
    
    # Test monthly payment patterns
    print("\n🔍 Testing Monthly Payment Patterns:")
    monthly_patterns = [
        r'월\s*납입금[:\s]*([\d,]+\.?[\d]*)만원',
        r'월\s*리스료[:\s]*([\d,]+\.?[\d]*)만원',
        r'월\s*렌트비[:\s]*([\d,]+\.?[\d]*)만원',
        r'월[:\s]*([\d,]+\.?[\d]*)만원',
        r'매월[:\s]*([\d,]+\.?[\d]*)만원',
        r'월세[:\s]*([\d,]+\.?[\d]*)만원',
        r'([\d]\.[\d]+)\s*만원.*?월',
        r'월.*?([\d]\.[\d]+)\s*만원',
        r'([1-9]\.[\d]+)\s*만원',
    ]
    
    for i, pattern in enumerate(monthly_patterns):
        match = re.search(pattern, html_content)
        if match:
            print(f"   ✅ Pattern {i+1}: {pattern}")
            print(f"      Matched: '{match.group(0)}' -> {match.group(1)}")
        else:
            print(f"   ❌ Pattern {i+1}: {pattern}")
    
    # Test lease term patterns
    print("\n🔍 Testing Lease Term Patterns:")
    term_patterns = [
        r'계약기간[:\s]*(\d+)개월',
        r'리스기간[:\s]*(\d+)개월',
        r'렌트기간[:\s]*(\d+)개월',
        r'리스\s*기간[:\s]*(\d+)\s*개월',
        r'계약\s*기간[:\s]*(\d+)\s*개월',
        r'(\d+)\s*개월',
    ]
    
    for i, pattern in enumerate(term_patterns):
        match = re.search(pattern, html_content)
        if match:
            print(f"   ✅ Pattern {i+1}: {pattern}")
            print(f"      Matched: '{match.group(0)}' -> {match.group(1)}")
        else:
            print(f"   ❌ Pattern {i+1}: {pattern}")
    
    # Test true price patterns
    print("\n🔍 Testing True Price Patterns:")
    true_price_patterns = [
        r'차량가격.*?([\d,]+\.?[\d]*)만원',
        r'([\d,]+\.?[\d]*)만원.*?차량가격',
        r'인수금.*?([\d,]+\.?[\d]*)만원',
        r'([\d,]+\.?[\d]*)만원.*?인수금',
        # Add missing patterns
        r'차량가격.*?([\d,]+)만원',
        r'([\d,]+)만원.*?차량가격',
        r'([\d,]+)\s*만원.*?차량가격',
        r'차량가격.*?([\d,]+)\s*만원'
    ]
    
    for i, pattern in enumerate(true_price_patterns):
        match = re.search(pattern, html_content)
        if match:
            print(f"   ✅ Pattern {i+1}: {pattern}")
            print(f"      Matched: '{match.group(0)}' -> {match.group(1)}")
        else:
            print(f"   ❌ Pattern {i+1}: {pattern}")
    
    # Show all numbers found in the content
    print("\n🔍 All numbers found in content:")
    number_pattern = r'([\d,]+\.?[\d]*)'
    numbers = re.findall(number_pattern, html_content)
    for i, num in enumerate(numbers):
        print(f"   {i+1}: {num}")
    
    # Show all 만원 occurrences
    print("\n🔍 All 만원 occurrences:")
    manwon_pattern = r'([\d,]+\.?[\d]*)\s*만원'
    manwon_matches = re.findall(manwon_pattern, html_content)
    for i, match in enumerate(manwon_matches):
        print(f"   {i+1}: {match}만원")
    
    # Test fallback logic
    print("\n🔍 Testing Fallback Logic:")
    all_amounts = re.findall(r'([\d,]+)\s*만원', html_content)
    large_amounts = []
    
    for amount_str in all_amounts:
        try:
            amount = float(amount_str.replace(',', ''))
            print(f"   Found: {amount_str} -> {amount}")
            if amount > 1000:  # Large amounts that could be deposits or true prices
                large_amounts.append(amount)
                print(f"     -> Large amount: {amount}")
        except (ValueError, TypeError):
            print(f"   Error parsing: {amount_str}")
    
    print(f"\n   Large amounts found: {large_amounts}")
    if len(large_amounts) >= 2:
        print(f"   Would use: True Price = {large_amounts[0] / 100.0}, Deposit = {large_amounts[1] / 100.0}")
    elif len(large_amounts) == 1:
        print(f"   Would use: True Price = {large_amounts[0] / 100.0}")
    
    # Test context matching
    print("\n🔍 Testing Context Matching:")
    for amount in large_amounts:
        amount_str = f"{int(amount):,}"
        print(f"   Testing amount: {amount_str}만원 ({amount})")
        
        # Find positions of this amount
        amount_positions = [m.start() for m in re.finditer(re.escape(f"{amount_str}만원"), html_content)]
        print(f"     Positions: {amount_positions}")
        
        for i, pos in enumerate(amount_positions):
            context_before = html_content[max(0, pos-200):pos]
            context_after = html_content[pos:pos+200]
            print(f"     Context {i+1} before: {context_before[-50:]}")
            print(f"     Context {i+1} after: {context_after[:50]}")
            
            has_insugum = "인수금" in context_before or "인수금" in context_after
            has_charyang = "차량가격" in context_before or "차량가격" in context_after
            print(f"     Has 인수금: {has_insugum}")
            print(f"     Has 차량가격: {has_charyang}")
            
            if has_insugum:
                print(f"     -> Would be deposit: {amount / 100.0}")
            if has_charyang:
                print(f"     -> Would be true price: {amount / 100.0}")
    
    # Check why 8,825만원 is not found
    print("\n🔍 Checking for 8,825만원:")
    if "8,825만원" in html_content:
        print("   ✅ Found '8,825만원' in HTML")
        # Find all occurrences
        positions = [m.start() for m in re.finditer('8,825만원', html_content)]
        print(f"   Positions: {positions}")
        for i, pos in enumerate(positions):
            context = html_content[max(0, pos-50):pos+50]
            print(f"   Context {i+1}: {context}")
    else:
        print("   ❌ '8,825만원' not found in HTML")
    
    # Check for 8,825 with space before 만원
    print("\n🔍 Checking for '8,825 만원':")
    if "8,825 만원" in html_content:
        print("   ✅ Found '8,825 만원' in HTML")
        positions = [m.start() for m in re.finditer('8,825 만원', html_content)]
        print(f"   Positions: {positions}")
        for i, pos in enumerate(positions):
            context = html_content[max(0, pos-50):pos+50]
            print(f"   Context {i+1}: {context}")
    else:
        print("   ❌ '8,825 만원' not found in HTML")
    
    # Test different patterns
    print("\n🔍 Testing different patterns:")
    patterns = [
        r'([\d,]+)만원',
        r'([\d,]+)\s*만원',
        r'([\d,]+)\s+만원',
    ]
    for i, pattern in enumerate(patterns):
        matches = re.findall(pattern, html_content)
        print(f"   Pattern {i+1} '{pattern}': {matches}")
    
    # Check the exact text around 차량가격
    print("\n🔍 Checking text around 차량가격:")
    if "차량가격" in html_content:
        positions = [m.start() for m in re.finditer('차량가격', html_content)]
        for i, pos in enumerate(positions):
            context = html_content[max(0, pos-100):pos+100]
            print(f"   Context around 차량가격 {i+1}: {context}")
            
            # Look for amounts near 차량가격
            context_before = html_content[max(0, pos-200):pos]
            context_after = html_content[pos:pos+200]
            print(f"   Context before 차량가격: {context_before[-50:]}")
            print(f"   Context after 차량가격: {context_after[:50]}")
            
            # Check for amounts in the context
            amount_pattern = r'([\d,]+)\s*만원'
            amounts_before = re.findall(amount_pattern, context_before)
            amounts_after = re.findall(amount_pattern, context_after)
            print(f"   Amounts before 차량가격: {amounts_before}")
            print(f"   Amounts after 차량가격: {amounts_after}")
            
            # Look for 8,825 in a larger context
            print(f"   Looking for 8,825 in larger context...")
            larger_context_after = html_content[pos:pos+500]
            amounts_larger = re.findall(amount_pattern, larger_context_after)
            print(f"   Amounts in larger context (500 chars): {amounts_larger}")
            
            # Check if 8,825 appears in the larger context
            if "8,825" in larger_context_after:
                print(f"   ✅ Found 8,825 in larger context!")
                # Find the position of 8,825 in the larger context
                eight_pos = larger_context_after.find("8,825")
                print(f"   Position of 8,825 in larger context: {eight_pos}")
                context_around_eight = larger_context_after[max(0, eight_pos-50):eight_pos+50]
                print(f"   Context around 8,825: {context_around_eight}")
            else:
                print(f"   ❌ 8,825 not found in larger context")
    else:
        print("   ❌ '차량가격' not found in HTML")

if __name__ == "__main__":
    debug_patterns() 