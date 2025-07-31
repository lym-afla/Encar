# Filter Tools & Analysis Guide

## 🔍 **Overview**

The filter tools provide advanced analysis and filtering capabilities for the Encar monitoring system, allowing users to find specific vehicles, analyze market trends, and identify the best deals.

## 🛠️ **Core Tools**

### **1. Filter Tools (`encar_filter_tools.py`)**

Advanced filtering and analysis capabilities:

```python
# Main filtering functions
def filter_by_price_range(listings: List[Dict], min_price: int, max_price: int) -> List[Dict]
def filter_by_year_range(listings: List[Dict], min_year: int, max_year: int) -> List[Dict]
def filter_by_mileage(listings: List[Dict], max_mileage: int) -> List[Dict]
def filter_lease_only(listings: List[Dict]) -> List[Dict]
def filter_purchase_only(listings: List[Dict]) -> List[Dict]
def find_best_value(listings: List[Dict], include_lease: bool = True) -> List[Dict]
```

### **2. Quick Deals (`quick_deals.py`)**

Command-line interface for quick deal finding:

```bash
# Find lease vehicles
python quick_deals.py --filter lease_only

# Find best value (including lease costs)
python quick_deals.py --filter best_value_all

# Find purchase vehicles only
python quick_deals.py --filter purchase_only

# Find vehicles under 50 million won
python quick_deals.py --filter price_under_50m
```

### **3. Database Query Tools (`database_query_enhanced.py`)**

Database analysis and statistics:

```python
# Get system statistics
def get_statistics() -> Dict

# Get lease vehicle analysis
def get_lease_analysis() -> Dict

# Export data to CSV
def export_to_csv(filename: str = None) -> str
```

## 📊 **Filter Categories**

### **Price-Based Filters**

```python
# Filter by price range (in won)
filter_by_price_range(listings, 30000000, 80000000)  # 30M-80M won

# Filter by price range (in 만원)
filter_by_price_range(listings, 3000, 8000)  # 3,000-8,000만원

# Find vehicles under specific price
def filter_price_under(listings: List[Dict], max_price: int) -> List[Dict]:
    return [l for l in listings if l.get('true_price', l.get('price', 0)) <= max_price]
```

### **Year-Based Filters**

```python
# Filter by year range
filter_by_year_range(listings, 2021, 2023)  # 2021-2023 models

# Find recent models only
def filter_recent_models(listings: List[Dict], min_year: int = 2021) -> List[Dict]:
    return [l for l in listings if l.get('year', 0) >= min_year]
```

### **Mileage-Based Filters**

```python
# Filter by maximum mileage
filter_by_mileage(listings, 50000)  # Under 50,000 km

# Find low-mileage vehicles
def filter_low_mileage(listings: List[Dict], max_mileage: int = 30000) -> List[Dict]:
    return [l for l in listings if l.get('mileage', 0) <= max_mileage]
```

### **Lease vs Purchase Filters**

```python
# Filter lease vehicles only
def filter_lease_only(listings: List[Dict]) -> List[Dict]:
    return [l for l in listings if l.get('is_lease', False)]

# Filter purchase vehicles only
def filter_purchase_only(listings: List[Dict]) -> List[Dict]:
    return [l for l in listings if not l.get('is_lease', False)]
```

## 🎯 **Advanced Analysis**

### **Best Value Analysis**

```python
def find_best_value(listings: List[Dict], include_lease: bool = True) -> List[Dict]:
    """
    Find vehicles with best value for money.
    
    Args:
        listings: List of vehicle listings
        include_lease: Whether to include lease costs in comparison
    
    Returns:
        Sorted list by value (lowest cost first)
    """
    if include_lease:
        # Use true_price for lease vehicles
        return sorted(listings, key=lambda x: x.get('true_price', x.get('price', 0)))
    else:
        # Use listed price only
        return sorted(listings, key=lambda x: x.get('price', 0))
```

### **Cost Analysis**

```python
def analyze_costs(listings: List[Dict]) -> Dict:
    """Analyze cost distribution and statistics."""
    
    lease_vehicles = filter_lease_only(listings)
    purchase_vehicles = filter_purchase_only(listings)
    
    return {
        'total_vehicles': len(listings),
        'lease_vehicles': len(lease_vehicles),
        'purchase_vehicles': len(purchase_vehicles),
        'avg_lease_cost': sum(l.get('true_price', 0) for l in lease_vehicles) / max(len(lease_vehicles), 1),
        'avg_purchase_cost': sum(l.get('price', 0) for l in purchase_vehicles) / max(len(purchase_vehicles), 1),
        'min_lease_cost': min((l.get('true_price', 0) for l in lease_vehicles), default=0),
        'max_lease_cost': max((l.get('true_price', 0) for l in lease_vehicles), default=0),
        'min_purchase_cost': min((l.get('price', 0) for l in purchase_vehicles), default=0),
        'max_purchase_cost': max((l.get('price', 0) for l in purchase_vehicles), default=0)
    }
```

### **Market Trend Analysis**

```python
def analyze_market_trends(listings: List[Dict]) -> Dict:
    """Analyze market trends and patterns."""
    
    # Group by year
    by_year = {}
    for listing in listings:
        year = listing.get('year', 0)
        if year not in by_year:
            by_year[year] = []
        by_year[year].append(listing)
    
    # Calculate statistics by year
    year_stats = {}
    for year, year_listings in by_year.items():
        prices = [l.get('true_price', l.get('price', 0)) for l in year_listings]
        year_stats[year] = {
            'count': len(year_listings),
            'avg_price': sum(prices) / len(prices),
            'min_price': min(prices),
            'max_price': max(prices)
        }
    
    return year_stats
```

## 📈 **Usage Examples**

### **1. Find Best Deals**

```python
from encar_filter_tools import find_best_value, filter_by_price_range

# Get all listings
listings = get_all_listings()

# Filter by price range (30M-80M won)
affordable = filter_by_price_range(listings, 30000000, 80000000)

# Find best value (including lease costs)
best_deals = find_best_value(affordable, include_lease=True)

# Show top 5 deals
for i, deal in enumerate(best_deals[:5]):
    print(f"{i+1}. {deal['title']}")
    print(f"   Price: {deal['price']:,}원")
    if deal.get('is_lease'):
        print(f"   True Cost: {deal['true_price']:,}원")
    print()
```

### **2. Lease vs Purchase Analysis**

```python
from encar_filter_tools import filter_lease_only, filter_purchase_only

# Separate lease and purchase vehicles
lease_vehicles = filter_lease_only(listings)
purchase_vehicles = filter_purchase_only(listings)

# Compare costs
avg_lease_cost = sum(l['true_price'] for l in lease_vehicles) / len(lease_vehicles)
avg_purchase_cost = sum(l['price'] for l in purchase_vehicles) / len(purchase_vehicles)

print(f"Average lease cost: {avg_lease_cost:,}원")
print(f"Average purchase cost: {avg_purchase_cost:,}원")
print(f"Difference: {avg_lease_cost - avg_purchase_cost:,}원")
```

### **3. Market Analysis**

```python
from encar_filter_tools import analyze_market_trends

# Analyze market trends
trends = analyze_market_trends(listings)

for year, stats in sorted(trends.items()):
    print(f"Year {year}:")
    print(f"  Count: {stats['count']}")
    print(f"  Avg Price: {stats['avg_price']:,}원")
    print(f"  Price Range: {stats['min_price']:,}원 - {stats['max_price']:,}원")
    print()
```

## 🚀 **Command Line Usage**

### **Quick Deals Tool**

```bash
# Find all lease vehicles
python quick_deals.py --filter lease_only --limit 10

# Find best value deals
python quick_deals.py --filter best_value_all --limit 5

# Find vehicles under 50 million won
python quick_deals.py --filter price_under_50m

# Find recent models (2021+)
python quick_deals.py --filter recent_models

# Export results to CSV
python quick_deals.py --filter best_value_all --export deals.csv
```

### **Filter Tools**

```bash
# Run interactive filter session
python encar_filter_tools.py

# Run specific analysis
python encar_filter_tools.py --analysis cost_comparison

# Export filtered results
python encar_filter_tools.py --filter price_under_60m --export affordable.csv
```

## 📊 **Output Formats**

### **Console Output**

```
🚗 Mercedes-Benz GLE Coupe Analysis
====================================

📊 Summary:
   Total Vehicles: 45
   Lease Vehicles: 12
   Purchase Vehicles: 33

💰 Cost Analysis:
   Average Lease Cost: 95,500,000원
   Average Purchase Cost: 78,200,000원
   Cost Difference: +17,300,000원

🏆 Top 5 Best Value Deals:
1. GLE400d 4MATIC 쿠페 (2021)
   Price: 65,000,000원
   Mileage: 45,000km
   URL: https://fem.encar.com/cars/detail/12345678

2. GLE350d 4MATIC 쿠페 (2022)
   Price: 72,000,000원
   Mileage: 32,000km
   URL: https://fem.encar.com/cars/detail/87654321
```

### **CSV Export**

```csv
car_id,title,price,true_price,is_lease,year,mileage,listing_url
12345678,GLE400d 4MATIC 쿠페,65000000,65000000,false,2021,45000,https://fem.encar.com/cars/detail/12345678
87654321,GLE350d 4MATIC 쿠페,72000000,72000000,false,2022,32000,https://fem.encar.com/cars/detail/87654321
```

## 🔧 **Configuration**

### **Filter Settings**

```yaml
filters:
  default_price_max: 80000000  # 80M won
  default_year_min: 2021
  default_mileage_max: 100000  # 100k km
  include_lease_in_comparison: true
  sort_by_value: true
```

### **Output Settings**

```yaml
output:
  format: console  # console, csv, json
  include_urls: true
  include_lease_details: true
  max_results: 20
```

## 🚨 **Common Issues**

### **1. No Results Found**

**Problem**: Filter returns no results
**Solution**: 
- Check filter criteria (price, year, mileage)
- Verify database has data
- Try broader filter ranges

### **2. Incorrect Cost Comparison**

**Problem**: Lease vs purchase cost comparison seems wrong
**Solution**:
- Ensure `include_lease=True` for lease cost comparison
- Check that lease vehicles have `true_price` calculated
- Verify monetary unit handling

### **3. Performance Issues**

**Problem**: Filter operations are slow
**Solution**:
- Limit result set size
- Use database indexes
- Cache frequently used filters

## 📚 **Best Practices**

1. **Use appropriate price ranges** for Korean market
2. **Include lease costs** in value comparisons
3. **Export results** for further analysis
4. **Test filters** with known data sets
5. **Monitor performance** for large datasets
6. **Document custom filters** for team use

## 🔍 **Advanced Features**

### **Custom Filters**

```python
# Create custom filter function
def filter_custom(listings: List[Dict], **kwargs) -> List[Dict]:
    """Custom filter with multiple criteria."""
    filtered = listings
    
    if 'max_price' in kwargs:
        filtered = filter_by_price_range(filtered, 0, kwargs['max_price'])
    
    if 'min_year' in kwargs:
        filtered = filter_by_year_range(filtered, kwargs['min_year'], 9999)
    
    if 'lease_only' in kwargs and kwargs['lease_only']:
        filtered = filter_lease_only(filtered)
    
    return filtered
```

### **Statistical Analysis**

```python
# Calculate price statistics
def price_statistics(listings: List[Dict]) -> Dict:
    prices = [l.get('true_price', l.get('price', 0)) for l in listings]
    return {
        'mean': sum(prices) / len(prices),
        'median': sorted(prices)[len(prices)//2],
        'min': min(prices),
        'max': max(prices),
        'std_dev': calculate_std_dev(prices)
    }
```

---

**Last Updated**: July 2025  
**Version**: 2.0  
**Status**: Production Ready ✅ 