#!/usr/bin/env python3
"""
Test Lease Patterns
Test the lease extraction patterns with actual HTML content
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
from monetary_utils import extract_lease_components_from_page_content

# Test with the exact HTML provided by the user
html_content = """
<div class="DetailLeadBottomPc_box__2Q7xi"><div class="ResponsiveTemplete_box_type__10yIs" data-impression="리스렌트정보" data-impression-index="10"><ul class="DetailSummaryLeaseRent_list__kS+K3"><li><p>인수금<button type="button" data-enlog-dt-eventnamegroup="플로팅"><span class="blind">인수금자세히 보기</span><span class="DetailSummaryLeaseRent_ico_question__QEonZ"></span></button></p><span><span class="DetailSummaryLeaseRent_price__yITp6">1,801 만원</span></span></li><li><p>차량가격<button type="button" data-enlog-dt-eventnamegroup="플로팅"><span class="blind">차량 가격 자세히 보기</span><span class="DetailSummaryLeaseRent_ico_question__QEonZ"></span></button></p><span>8,825 만원</span></li></ul></div></div>

<ul class="DetailLeaseRent_list_leaserent__nzGzL"><li><strong class="DetailLeaseRent_tit__q3gJK">차량 계약 시 비용</strong><span class="DetailLeaseRent_txt__70-lf">인수금 (판매자에게 지급)</span><span class="DetailLeaseRent_price__DxyTw">1,801만원</span></li><li><strong class="DetailLeaseRent_tit__q3gJK">운행기간 동안 비용</strong><span class="DetailLeaseRent_txt__70-lf"><span class="DetailLease_txt__KidB6">월리스료 165만원<span class="DetailLease_ico_x__hygNL"></span>26개월</span></span><span class="DetailLeaseRent_price__DxyTw">4,290만원</span></li><li><strong class="DetailLeaseRent_tit__q3gJK"><label for="rentPrice01">리스 만기 후 비용</label><button type="button" data-enlog-dt-eventnamegroup="리스렌트정보"><span class="blind">리스 만기 후 비용</span><span class="DetailLeaseRent_ico_question__QZ91a"></span></button></strong><span class="DetailLeaseRent_txt__70-lf"><div class="DetailLease_txt__KidB6 SelectBox_uiselect_size_h40__cLgHK"><select name="leasePrice" id="leasePrice" class="SelectBox_uiselectbox_drop__JnVWV"><option value="001">구매 (리스사에게 지급)</option><option value="002">반납 (보증금 환급)</option></select></div></span><span class="DetailLeaseRent_price__DxyTw">2,301만원</span></li></ul>
"""

print("Testing lease extraction with exact HTML provided by user...")
print("=" * 60)



result = extract_lease_components_from_page_content(html_content)

print("\nExtraction Results:")
print(f"Deposit: {result.get('deposit')}만원")
print(f"Monthly Payment: {result.get('monthly_payment')}만원")
print(f"Lease Term: {result.get('lease_term_months')}개월")
print(f"True Price: {result.get('true_price')}만원")
print(f"Total Cost: {result.get('total_cost')}만원")
print(f"Is Lease: {result.get('is_lease')}")

print("\nExpected Results:")
print("Deposit: 18.01만원")
print("Monthly Payment: 1.65만원")
print("Lease Term: 26개월")
print("True Price: 88.25만원")
print("Is Lease: True") 