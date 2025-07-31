# API-Based System Guide

## 🚀 **Overview**

The API-based system provides fast, reliable data retrieval from Encar.com using direct API calls combined with browser automation for complex detail extraction.

## 🔧 **Architecture**

### **Core Components**

```
API-BASED SYSTEM:
├── encar_api_client.py (API calls)
├── encar_scraper_api.py (Hybrid: API + Browser details)
├── encar_monitor_api.py (Monitoring)
├── data_storage.py (Database)
├── monetary_utils.py (Korean won handling)
├── encar_filter_tools.py (Filtering)
└── quick_deals.py (CLI tools)
```

### **Data Flow**

1. **API Client** (`encar_api_client.py`)
   - Extracts authentication from browser session
   - Makes direct HTTP requests to Encar API
   - Converts API responses to internal format
   - Handles Korean monetary units (만원 → 원)

2. **Hybrid Scraper** (`encar_scraper_api.py`)
   - Uses API for bulk data retrieval
   - Uses browser for complex detail extraction
   - Extracts views, registration dates, lease terms
   - Handles lease vehicle detection

3. **Monitor** (`encar_monitor_api.py`)
   - Orchestrates the monitoring process
   - Manages scheduling and notifications
   - Handles database updates
   - Provides system status

## 📊 **Performance Benefits**

| Aspect | Legacy Browser | API System | Improvement |
|--------|---------------|-------------|-------------|
| **Speed** | ~30s/page | ~5s/page | **6x faster** |
| **Reliability** | Medium | High | **More stable** |
| **Resource Usage** | High (browser) | Low (HTTP) | **Efficient** |
| **Maintenance** | High | Low | **Easier** |

## 🔍 **API Client Details**

### **Authentication Process**

```python
# 1. Browser session to extract cookies/headers
async def extract_authentication(self) -> bool:
    # Navigate to search page
    # Extract cookies and headers
    # Set auth validity period

# 2. HTTP requests with authentication
async def make_api_request(self, endpoint: str, params: dict):
    # Use extracted cookies/headers
    # Make authenticated HTTP requests
    # Handle 407 (auth failure) gracefully
```

### **Query Building**

```python
# Base query for Mercedes-Benz GLE Coupes
base_query = "(And.Hidden.N._.(C.CarType.N._.(C.Manufacturer.벤츠._.ModelGroup.GLE-클래스.))"

# Add filters
filters = {
    'year_min': '2021',
    'price_max': '9000',  # 90 million KRW
    'mileage_max': '100000'
}
```

### **Data Conversion**

```python
# Convert API response to internal format
def convert_api_item_to_listing(self, item: dict):
    # Extract basic info (ID, model, price, etc.)
    # Convert prices from 만원 to 원
    # Detect lease vehicles
    # Build listing URL
    # Return standardized format
```

## 🌐 **Hybrid Scraper Details**

### **API + Browser Approach**

```python
# Phase 1: API for bulk data
listings = await api_client.get_listings(limit=20)

# Phase 2: Browser for details
for listing in listings:
    views, reg_date, lease_info = await get_views_and_registration_efficient(
        listing['listing_url'], listing
    )
```

### **Detail Extraction**

```python
# Extract views count
views = await page.query_selector('.DetailCarPhotoPc_info__0IA0t')

# Extract registration date
await page.click('button:has-text("조회수 자세히보기")')
tooltip = await page.wait_for_selector('.TooltipPopper_area__iKVzy')

# Extract lease terms
lease_info = await extract_lease_terms_from_page(page)
```

## 💰 **Monetary Handling**

### **Korean Won Conversion**

```python
# Convert 만원 to 원
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
# Handle various Korean price formats
def parse_korean_price(price_value: Union[str, int, float]) -> Optional[int]:
    # "180만원" → 1,800,000
    # "1,800,000원" → 1,800,000
    # 180 → 1,800,000 (assumes 만원)
```

## 🚗 **Lease Vehicle Detection**

### **API-Based Detection**

```python
def detect_lease_vehicle(self, item: dict) -> bool:
    # Manual overrides for known lease vehicles
    # Heuristic 1: Recent cars with moderate prices
    # Heuristic 2: Check SellType field
    # Heuristic 3: Very new cars (2023+)
```

### **Browser-Based Confirmation**

```python
async def extract_lease_terms_from_page(self, page) -> Optional[dict]:
    # Check for lease keywords
    # Extract deposit (인수금)
    # Extract monthly payment (월리스료)
    # Extract term (계약기간)
    # Calculate total cost
```

## 🔧 **Configuration**

### **API Settings**

```yaml
api_integration:
  auth_timeout_hours: 1
  request_timeout_seconds: 30
  max_retries: 3
  fallback_to_browser: true
```

### **Browser Settings**

```yaml
browser:
  headless: true
  timeout: 30
  wait_time: 3
```

## 🚨 **Error Handling**

### **API Failures**

```python
# Handle 407 (authentication failure)
if response.status == 407:
    self.auth_valid_until = None  # Force re-auth
    return None

# Handle timeouts
async with self.http_session.get(endpoint, timeout=30) as response:
    # Process response
```

### **Browser Fallbacks**

```python
# If API fails, fall back to browser
if not api_data:
    self.logger.warning("API failed, using browser fallback")
    return await self.browser_scrape()
```

## 📈 **Monitoring**

### **System Status**

```python
async def get_system_status(self) -> Dict:
    return {
        'api_working': await self.test_api_connectivity(),
        'total_vehicles': await self.get_total_count(),
        'auth_valid': await self.is_auth_valid(),
        'last_check': self.last_check,
        'new_listings_found': self.new_listings_found
    }
```

### **Performance Metrics**

```python
# Track scan times
self.scan_times.append(datetime.now() - start_time)

# Calculate success rate
self.api_success_rate = successful_requests / total_requests
```

## 🔍 **Testing**

### **API Connectivity Test**

```bash
python encar_api_client.py
```

### **Hybrid Scraper Test**

```bash
python encar_scraper_api.py
```

### **Monitor Test**

```bash
python encar_monitor_api.py --test
```

## 📚 **Best Practices**

1. **Use API for bulk operations**
2. **Use browser only for complex detail extraction**
3. **Handle Korean monetary units consistently**
4. **Implement proper error handling and fallbacks**
5. **Monitor system performance and success rates**
6. **Keep authentication tokens fresh**

## 🚨 **Troubleshooting**

### **Common Issues**

1. **API Authentication Failed**
   - Check network connectivity
   - Verify browser session extraction
   - Increase timeout values

2. **Browser Fallback Not Working**
   - Check Playwright installation
   - Verify headless mode settings
   - Check for page element changes

3. **Monetary Conversion Errors**
   - Verify input format (만원 vs 원)
   - Check for non-numeric characters
   - Use monetary utilities consistently

### **Debug Mode**

```python
# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Test individual components
await api_client.test_api_connectivity()
await scraper.test_browser_extraction()
```

---

**Last Updated**: July 2025  
**Version**: 2.0  
**Status**: Production Ready ✅ 