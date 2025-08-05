#!/usr/bin/env python3
"""
Debug Lease Patterns
Debug the lease extraction patterns to see what's working
"""

import re

def debug_lease_patterns():
    """Debug lease extraction patterns"""
    print("🔍 Debugging Lease Extraction Patterns")
    print("=" * 50)
    
    # Actual HTML content from the user
    html_content = """
    <ul class="DetailLeaseRent_list_leaserent__nzGzL">
        <li>
            <strong class="DetailLeaseRent_tit__q3gJK">
                <font style="vertical-align: inherit;">
                    <font style="vertical-align: inherit;">Costs when signing a vehicle contract</font>
                </font>
            </strong>
            <span class="DetailLeaseRent_txt__70-lf">
                <font style="vertical-align: inherit;">
                    <font style="vertical-align: inherit;">Deposit (paid to seller)</font>
                </font>
            </span>
            <span class="DetailLeaseRent_price__DxyTw">
                <font style="vertical-align: inherit;">
                    <font style="vertical-align: inherit;">18.01 </font>
                </font>
                <font style="vertical-align: inherit;">
                    <font style="vertical-align: inherit;">million won</font>
                </font>
            </span>
        </li>
        <li>
            <strong class="DetailLeaseRent_tit__q3gJK">
                <font style="vertical-align: inherit;">
                    <font style="vertical-align: inherit;">Cost during the operation period</font>
                </font>
            </strong>
            <span class="DetailLeaseRent_txt__70-lf">
                <span class="DetailLease_txt__KidB6">
                    <font style="vertical-align: inherit;">
                        <font style="vertical-align: inherit;">Monthly rent of </font>
                    </font>
                    <font style="vertical-align: inherit;">
                        <font style="vertical-align: inherit;">1.65 </font>
                    </font>
                    <font style="vertical-align: inherit;">
                        <font style="vertical-align: inherit;">million won</font>
                    </font>
                    <span class="DetailLease_ico_x__hygNL"></span>
                    <font style="vertical-align: inherit;">
                        <font style="vertical-align: inherit;">26 </font>
                    </font>
                    <font style="vertical-align: inherit;">
                        <font style="vertical-align: inherit;">months</font>
                    </font>
                </span>
            </span>
            <span class="DetailLeaseRent_price__DxyTw">
                <font style="vertical-align: inherit;">
                    <font style="vertical-align: inherit;">42.9 </font>
                </font>
                <font style="vertical-align: inherit;">
                    <font style="vertical-align: inherit;">million won</font>
                </font>
            </span>
        </li>
    </ul>
    
    <ul class="DetailSummaryLeaseRent_list__kS+K3">
        <li>
            <p>
                <font style="vertical-align: inherit;">
                    <font style="vertical-align: inherit;">acquisition fee</font>
                </font>
                <button type="button" data-enlog-dt-eventnamegroup="플로팅">
                    <span class="blind">
                        <font style="vertical-align: inherit;"></font>
                        <font style="vertical-align: inherit;">
                            <font style="vertical-align: inherit;">View details </font>
                            <font style="vertical-align: inherit;">of acquisition fee</font>
                        </font>
                    </span>
                    <span class="DetailSummaryLeaseRent_ico_question__QEonZ"></span>
                </button>
            </p>
            <span>
                <span class="DetailSummaryLeaseRent_price__yITp6">
                    <font style="vertical-align: inherit;">
                        <font style="vertical-align: inherit;">18.01 million won</font>
                    </font>
                </span>
            </span>
        </li>
        <li>
            <p>
                <font style="vertical-align: inherit;">
                    <font style="vertical-align: inherit;">Vehicle price</font>
                </font>
                <button type="button" data-enlog-dt-eventnamegroup="플로팅">
                    <span class="blind">
                        <font style="vertical-align: inherit;">
                            <font style="vertical-align: inherit;">View vehicle pricing details</font>
                        </font>
                    </span>
                    <span class="DetailSummaryLeaseRent_ico_question__QEonZ"></span>
                </button>
            </p>
            <span>
                <font style="vertical-align: inherit;">
                    <font style="vertical-align: inherit;">88.25 million won</font>
                </font>
            </span>
        </li>
    </ul>
    """
    
    print("📄 Testing deposit patterns...")
    
    # Test deposit patterns
    deposit_patterns = [
        r'Deposit.*?([\d,]+\.?[\d]*)\s*million\s*won',
        r'([\d,]+\.?[\d]*)\s*million\s*won.*?Deposit',
        r'acquisition\s+fee.*?([\d,]+\.?[\d]*)\s*million\s*won',
        r'([\d,]+\.?[\d]*)\s*million\s*won.*?acquisition\s+fee',
        r'([\d,]+\.?[\d]*)\s*million\s*won',
    ]
    
    for i, pattern in enumerate(deposit_patterns):
        match = re.search(pattern, html_content)
        if match:
            print(f"   ✅ Pattern {i+1} matched: {match.group(1)}")
        else:
            print(f"   ❌ Pattern {i+1} failed")
    
    print("\n📄 Testing monthly payment patterns...")
    
    # Test monthly patterns
    monthly_patterns = [
        r'Monthly\s+rent.*?([\d,]+\.?[\d]*)\s*million\s*won',
        r'([\d,]+\.?[\d]*)\s*million\s*won.*?Monthly\s+rent',
        r'([\d,]+\.?[\d]*)\s*million\s*won.*?months',
        r'([\d,]+\.?[\d]*)\s*million\s*won.*?months',
    ]
    
    for i, pattern in enumerate(monthly_patterns):
        match = re.search(pattern, html_content)
        if match:
            print(f"   ✅ Pattern {i+1} matched: {match.group(1)}")
        else:
            print(f"   ❌ Pattern {i+1} failed")
    
    print("\n📄 Testing lease term patterns...")
    
    # Test term patterns
    term_patterns = [
        r'(\d+)\s*months',
        r'(\d+)\s*month',
    ]
    
    for i, pattern in enumerate(term_patterns):
        match = re.search(pattern, html_content)
        if match:
            print(f"   ✅ Pattern {i+1} matched: {match.group(1)}")
        else:
            print(f"   ❌ Pattern {i+1} failed")
    
    print("\n📄 Testing true price patterns...")
    
    # Test true price patterns
    true_price_patterns = [
        r'Vehicle\s+price.*?([\d,]+\.?[\d]*)\s*million\s*won',
        r'([\d,]+\.?[\d]*)\s*million\s*won.*?Vehicle\s+price',
    ]
    
    for i, pattern in enumerate(true_price_patterns):
        match = re.search(pattern, html_content)
        if match:
            print(f"   ✅ Pattern {i+1} matched: {match.group(1)}")
        else:
            print(f"   ❌ Pattern {i+1} failed")
    
    print("\n📄 Looking for specific text in HTML...")
    
    # Look for specific text
    if "Deposit" in html_content:
        print("   ✅ Found 'Deposit' in HTML")
    else:
        print("   ❌ 'Deposit' not found in HTML")
        
    if "Monthly rent" in html_content:
        print("   ✅ Found 'Monthly rent' in HTML")
    else:
        print("   ❌ 'Monthly rent' not found in HTML")
        
    if "months" in html_content:
        print("   ✅ Found 'months' in HTML")
    else:
        print("   ❌ 'months' not found in HTML")
        
    if "Vehicle price" in html_content:
        print("   ✅ Found 'Vehicle price' in HTML")
    else:
        print("   ❌ 'Vehicle price' not found in HTML")

if __name__ == "__main__":
    debug_lease_patterns() 