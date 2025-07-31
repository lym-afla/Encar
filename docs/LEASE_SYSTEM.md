# Lease Vehicle Detection & Analysis System

## 🚗 **Overview**

The lease vehicle detection system identifies and analyzes lease vehicles on Encar.com, providing accurate cost calculations and true price analysis.

## 💰 **Lease Vehicle Characteristics**

### **Korean Lease Structure**
- **Deposit (인수금)**: Large upfront payment (e.g., 1,476만원)
- **Monthly Payment (월리스료)**: Monthly lease fee (e.g., 180만원)
- **Term (계약기간)**: Lease duration in months (e.g., 25개월)
- **Total Cost**: Deposit + (Monthly × Term)

### **Example Lease Vehicle**
```
Car ID: 39923210
Listed Price: 8,000만원
Actual Lease Terms:
├── Deposit: 1,476만원 (14,760,000원)
├── Monthly: 180만원 (1,800,000원)
├── Term: 25 months
└── Total Cost: 11,001만원 (110,010,000원)
```

## 🔍 **Detection Methods**

### **1. API-Based Detection (Phase 1)**

```python
def detect_lease_vehicle(self, item: dict) -> bool:
    # Manual overrides for known lease vehicles
    known_lease_vehicles = {
        '39743923': True,
        '39923210': True
    }
    
    # Heuristic 1: Recent cars with moderate prices
    if year >= 2021 and 4000 <= price <= 8000:
        return True
    
    # Heuristic 2: Check SellType field
    if any(keyword in sell_type for keyword in ['리스', '렌트']):
        return True
    
    # Heuristic 3: Very new cars (2023+)
    if year >= 2023 and 4000 <= price <= 8000:
        return True
```

### **2. Browser-Based Confirmation (Phase 2)**

```python
async def extract_lease_terms_from_page(self, page) -> Optional[dict]:
    # Check for lease keywords
    lease_keywords = ["리스", "렌트", "월 납입금", "보증금", "리스료"]
    
    # Extract deposit (인수금)
    deposit_patterns = [
        r'인수금[^0-9]*([0-9,]+)만원',
        r'인수금[^0-9]*\(판매자에게 지급\)[^0-9]*([0-9,]+)만원'
    ]
    
    # Extract monthly payment (월리스료)
    monthly_patterns = [
        r'월리스료\s*([0-9,]+)만원',
        r'월<span[^>]*>([0-9,]+)</span>만원',
        r'월\s*([0-9,]+)만원.*?개월'
    ]
    
    # Extract term (계약기간)
    term_patterns = [
        r'월리스료[^0-9]*([0-9]+)개월',
        r'([0-9]+)개월.*?월리스료'
    ]
```

## 💱 **Monetary Unit Handling**

### **Korean Won Conversion**

```python
# Convert 만원 to 원 (10,000 won units)
def convert_manwon_to_won(manwon_value: Union[int, float, str]) -> int:
    # 180만원 → 1,800,000원
    return int(float(manwon_value) * 10000)

# Convert 원 to 만원
def convert_won_to_manwon(won_amount: int) -> float:
    # 1,800,000원 → 180.0만원
    return won_amount / 10000.0
```

### **Price Parsing**

```python
def parse_korean_price(price_value: Union[str, int, float]) -> Optional[int]:
    # Handle various formats:
    # "180만원" → 1,800,000
    # "1,800,000원" → 1,800,000
    # 180 → 1,800,000 (assumes 만원)
```

## 📊 **Database Schema**

### **Lease-Related Columns**

```sql
CREATE TABLE listings (
    -- Standard fields
    car_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    price TEXT,
    price_numeric REAL,
    
    -- Lease-specific fields
    is_lease BOOLEAN DEFAULT 0,
    true_price REAL,  -- Total cost for leases
    lease_deposit REAL,  -- Initial deposit
    lease_monthly_payment REAL,  -- Monthly payment
    lease_term_months INTEGER,  -- Lease term
    lease_total_monthly_cost REAL  -- Total monthly payments
);
```

### **Data Storage**

```python
# Store lease data in won amounts
lease_info = {
    'deposit': 14760000,  # 1,476만원 in won
    'monthly_payment': 1800000,  # 180만원 in won
    'lease_term_months': 25,
    'total_cost': 110010000  # 11,001만원 in won
}
```

## 🔧 **System Integration**

### **Hybrid Approach**

```python
# Phase 1: API detection
is_lease = api_client.detect_lease_vehicle(item)
if is_lease:
    lease_info = api_client.extract_lease_info(item)

# Phase 2: Browser confirmation
if is_lease:
    actual_lease_info = await scraper.extract_lease_terms_from_page(page)
    if actual_lease_info:
        lease_info = actual_lease_info  # Use browser data
```

### **Cost Calculation**

```python
# Calculate true cost for lease vehicles
if is_lease and lease_info:
    true_price = lease_info['total_cost']
else:
    true_price = price  # Use listed price for purchases
```

## 📈 **Analysis Tools**

### **Filter Tools**

```python
# Filter by lease status
def filter_lease_only(listings: List[Dict]) -> List[Dict]:
    return [l for l in listings if l.get('is_lease', False)]

def filter_purchase_only(listings: List[Dict]) -> List[Dict]:
    return [l for l in listings if not l.get('is_lease', False)]

# Find best value (including lease costs)
def find_best_value(listings: List[Dict], include_lease: bool = True) -> List[Dict]:
    if include_lease:
        # Use true_price for comparison
        return sorted(listings, key=lambda x: x.get('true_price', x.get('price', 0)))
    else:
        # Use listed price only
        return sorted(listings, key=lambda x: x.get('price', 0))
```

### **Quick Deals Tool**

```bash
# Find lease vehicles
python quick_deals.py --filter lease_only

# Find best value (including lease costs)
python quick_deals.py --filter best_value_all

# Find purchase vehicles only
python quick_deals.py --filter purchase_only
```

## 🎯 **Use Cases**

### **1. Lease Vehicle Identification**

```python
# Detect lease vehicles during monitoring
for listing in listings:
    if listing.get('is_lease', False):
        print(f"Lease vehicle found: {listing['title']}")
        print(f"  Listed: {listing['price']:,}원")
        print(f"  True Cost: {listing['true_price']:,}원")
```

### **2. Cost Comparison**

```python
# Compare lease vs purchase costs
lease_vehicles = filter_lease_only(listings)
purchase_vehicles = filter_purchase_only(listings)

avg_lease_cost = sum(l['true_price'] for l in lease_vehicles) / len(lease_vehicles)
avg_purchase_cost = sum(l['price'] for l in purchase_vehicles) / len(purchase_vehicles)
```

### **3. Deal Analysis**

```python
# Find vehicles with significant cost differences
for listing in listings:
    if listing.get('is_lease', False):
        listed = listing.get('price', 0)
        true_cost = listing.get('true_price', 0)
        difference = true_cost - listed
        
        if difference > 20000000:  # 20 million won
            print(f"High lease cost: {listing['title']}")
            print(f"  Additional cost: {difference:,}원")
```

## 🚨 **Common Issues**

### **1. False Positives**

**Problem**: Non-lease vehicles flagged as lease
**Solution**: Refine heuristics and add manual overrides

```python
# Add to known non-lease vehicles
known_non_lease_vehicles = {
    '12345678': False,
    '87654321': False
}
```

### **2. Missing Lease Terms**

**Problem**: Lease vehicle detected but terms not extracted
**Solution**: Improve regex patterns and add fallbacks

```python
# Add more regex patterns
monthly_patterns = [
    r'월리스료\s*([0-9,]+)만원',
    r'월<span[^>]*>([0-9,]+)</span>만원',
    r'월\s*([0-9,]+)만원.*?개월',
    r'월렌트료[^0-9]*([0-9,]+)만원',
    r'월\s*([0-9,]+)만원'  # Fallback pattern
]
```

### **3. Monetary Conversion Errors**

**Problem**: Incorrect won/만원 conversion
**Solution**: Use monetary utilities consistently

```python
# Always use monetary utilities
from monetary_utils import convert_manwon_to_won, parse_korean_price

# Don't do manual conversion
# price_won = price_manwon * 10000  # ❌ Wrong

# Use utilities
price_won = convert_manwon_to_won(price_manwon)  # ✅ Correct
```

## 📊 **Performance Metrics**

### **Detection Accuracy**

```python
# Track detection success rate
total_lease_vehicles = len([l for l in listings if l.get('is_lease', False)])
confirmed_lease_vehicles = len([l for l in listings if l.get('lease_info')])
accuracy = confirmed_lease_vehicles / total_lease_vehicles
```

### **Cost Analysis**

```python
# Calculate average cost differences
lease_vehicles = filter_lease_only(listings)
cost_differences = []

for vehicle in lease_vehicles:
    listed = vehicle.get('price', 0)
    true_cost = vehicle.get('true_price', 0)
    difference = true_cost - listed
    cost_differences.append(difference)

avg_difference = sum(cost_differences) / len(cost_differences)
```

## 🔍 **Testing**

### **Test Lease Detection**

```bash
# Test with specific vehicle
python -c "
from encar_api_client import EncarAPIClient
import yaml

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

client = EncarAPIClient(config)
# Test lease detection for car ID 39923210
"
```

### **Test Lease Extraction**

```bash
# Test browser-based extraction
python -c "
from encar_scraper_api import EncarScraperAPI
import yaml

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

scraper = EncarScraperAPI(config)
# Test lease extraction for car ID 39923210
"
```

## 📚 **Best Practices**

1. **Always use monetary utilities** for Korean won conversion
2. **Test with known lease vehicles** to verify detection
3. **Implement fallbacks** for missing lease terms
4. **Track detection accuracy** and refine heuristics
5. **Use true cost** for lease vehicle comparisons
6. **Document manual overrides** for known vehicles

## 🚨 **Troubleshooting**

### **Lease Detection Not Working**

1. Check API connectivity
2. Verify heuristics are appropriate
3. Add manual overrides for known vehicles
4. Test with browser fallback

### **Lease Terms Not Extracted**

1. Check page content for lease keywords
2. Verify regex patterns match page format
3. Test with different vehicle examples
4. Add more fallback patterns

### **Monetary Conversion Errors**

1. Verify input format (만원 vs 원)
2. Use monetary utilities consistently
3. Check for non-numeric characters
4. Test conversion functions

---

**Last Updated**: July 2025  
**Version**: 2.0  
**Status**: Production Ready ✅ 