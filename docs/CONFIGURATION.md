# Configuration Guide

## ⚙️ **Overview**

The Encar monitoring system uses `config.yaml` for all configuration settings, allowing easy customization without code changes.

## 📁 **Configuration File Structure**

```yaml
# config.yaml
search:
  manufacturer: "벤츠"
  model_group: "GLE-클래스"
  year_range: "202100.."
  price_range: "..9000"
  base_url: "http://www.encar.com/fc/fc_carsearchlist.do"
  car_type: "for"
  sort: "ModifiedDate"
  limit: 20

monitoring:
  check_interval_minutes: 10
  max_pages_to_scan: 5
  notification_threshold: 5
  quick_scan_interval_minutes: 2

browser:
  headless: true
  timeout: 30
  wait_time: 3

database:
  filename: "encar_listings.db"
  cleanup_days: 30

notification:
  enabled: true
  console_alerts: true
  log_alerts: true

filters:
  exclude_keywords:
    - "사고"
    - "침수"
    - "flood"
    - "accident"

new_listing_criteria:
  max_registration_age_days: 30
  max_views_for_new: 100
  immediate_alert_views: 10

api_integration:
  auth_timeout_hours: 1
  request_timeout_seconds: 30
  max_retries: 3
  fallback_to_browser: true

smart_monitoring_settings:
  dynamic_pagination: true
  adaptive_timeouts: true
  performance_tracking: true
```

## 🔍 **Search Configuration**

### **Basic Search Parameters**

```yaml
search:
  manufacturer: "벤츠"  # Mercedes-Benz in Korean
  model_group: "GLE-클래스"  # GLE-Class
  year_range: "202100.."  # 2021 and newer
  price_range: "..9000"  # Up to 90 million KRW
```

### **Advanced Search Options**

```yaml
search:
  # URL and pagination
  base_url: "http://www.encar.com/fc/fc_carsearchlist.do"
  car_type: "for"  # for sale
  sort: "ModifiedDate"  # Sort by modification date
  limit: 20  # Results per page
  
  # Additional filters
  fuel_type: "diesel"  # Optional fuel type filter
  transmission: "automatic"  # Optional transmission filter
```

## 📊 **Monitoring Configuration**

### **Basic Monitoring Settings**

```yaml
monitoring:
  check_interval_minutes: 10  # How often to check for new listings
  max_pages_to_scan: 5  # Maximum pages to scan per cycle
  notification_threshold: 5  # Alert if views < this number
  quick_scan_interval_minutes: 2  # Quick scan interval for urgent listings
```

### **Advanced Monitoring Options**

```yaml
monitoring:
  # Performance settings
  batch_size: 10  # Process listings in batches
  retry_attempts: 3  # Number of retry attempts
  timeout_seconds: 30  # Request timeout
  
  # Alert settings
  enable_immediate_alerts: true  # Alert for very fresh listings
  enable_daily_summary: true  # Send daily summary
  enable_weekly_report: true  # Send weekly report
```

## 🌐 **Browser Configuration**

### **Browser Settings**

```yaml
browser:
  headless: true  # Run browser in headless mode
  timeout: 30  # Page load timeout in seconds
  wait_time: 3  # Wait time after page load
  user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
```

### **Advanced Browser Options**

```yaml
browser:
  # Performance settings
  disable_images: true  # Don't load images for faster scraping
  disable_javascript: false  # Keep JavaScript enabled for dynamic content
  viewport_width: 1920
  viewport_height: 1080
  
  # Proxy settings (optional)
  proxy_server: ""  # Proxy server URL
  proxy_username: ""  # Proxy username
  proxy_password: ""  # Proxy password
```

## 💾 **Database Configuration**

### **Database Settings**

```yaml
database:
  filename: "encar_listings.db"  # SQLite database file
  cleanup_days: 30  # Remove listings older than 30 days
  backup_enabled: true  # Enable automatic backups
  backup_interval_days: 7  # Backup every 7 days
```

### **Advanced Database Options**

```yaml
database:
  # Performance settings
  connection_timeout: 30
  max_connections: 10
  
  # Data retention
  archive_old_data: true
  archive_after_days: 90
  
  # Backup settings
  backup_location: "./backups/"
  compression_enabled: true
```

## 🔔 **Notification Configuration**

### **Basic Notification Settings**

```yaml
notification:
  enabled: true  # Enable notifications
  console_alerts: true  # Show alerts in console
  log_alerts: true  # Log alerts to file
  email_enabled: false  # Email notifications (requires setup)
```

### **Advanced Notification Options**

```yaml
notification:
  # Email settings (if enabled)
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  email_username: "your-email@gmail.com"
  email_password: "your-app-password"
  email_recipients: ["recipient@example.com"]
  
  # Alert thresholds
  min_price_threshold: 50000000  # Alert for vehicles under 50M won
  max_mileage_threshold: 100000  # Alert for vehicles under 100k km
  
  # Alert formats
  include_urls: true
  include_images: false
  alert_format: "detailed"  # simple, detailed, summary
```

## 🚗 **Filter Configuration**

### **Exclusion Filters**

```yaml
filters:
  exclude_keywords:
    - "사고"  # Accident
    - "침수"  # Flood damage
    - "flood"
    - "accident"
    - "salvage"
    - "rebuilt"
  
  # Additional filters
  exclude_models:
    - "AMG"  # Exclude AMG models (optional)
  
  include_only_models:
    - "쿠페"  # Include only coupe models
```

### **Advanced Filter Options**

```yaml
filters:
  # Price filters
  min_price: 30000000  # 30M won minimum
  max_price: 80000000  # 80M won maximum
  
  # Year filters
  min_year: 2021
  max_year: 2024
  
  # Mileage filters
  max_mileage: 100000  # 100k km maximum
  
  # Lease filters
  include_lease_vehicles: true
  lease_cost_threshold: 100000000  # 100M won maximum lease cost
```

## 🆕 **New Listing Criteria**

### **Freshness Detection**

```yaml
new_listing_criteria:
  max_registration_age_days: 30  # Consider listings registered within 30 days as "new"
  max_views_for_new: 100  # Consider listings with <100 views as "new"
  immediate_alert_views: 10  # Immediate alert for listings with <10 views
  
  # Additional criteria
  min_price_for_alert: 50000000  # Alert for vehicles over 50M won
  max_mileage_for_alert: 50000  # Alert for vehicles under 50k km
```

### **Advanced New Listing Options**

```yaml
new_listing_criteria:
  # Time-based criteria
  check_registration_date: true
  check_view_count: true
  check_price_changes: true
  
  # Alert settings
  enable_urgent_alerts: true  # Alert for very fresh listings
  urgent_views_threshold: 5  # Urgent alert for <5 views
  urgent_age_hours: 24  # Urgent alert for listings <24 hours old
```

## 🔌 **API Integration Configuration**

### **API Settings**

```yaml
api_integration:
  auth_timeout_hours: 1  # Re-authenticate every hour
  request_timeout_seconds: 30  # API request timeout
  max_retries: 3  # Maximum retry attempts
  fallback_to_browser: true  # Use browser if API fails
  
  # Performance settings
  batch_size: 20  # Process 20 listings at a time
  concurrent_requests: 5  # Maximum concurrent API requests
  
  # Error handling
  retry_delay_seconds: 5  # Wait 5 seconds between retries
  exponential_backoff: true  # Use exponential backoff for retries
```

### **Advanced API Options**

```yaml
api_integration:
  # Authentication settings
  session_persistence: true  # Keep session alive between requests
  auto_refresh_auth: true  # Automatically refresh authentication
  
  # Rate limiting
  requests_per_minute: 60  # Maximum requests per minute
  requests_per_hour: 1000  # Maximum requests per hour
  
  # Monitoring
  track_success_rate: true
  alert_on_low_success_rate: true
  low_success_rate_threshold: 0.8  # Alert if success rate < 80%
```

## 🧠 **Smart Monitoring Settings**

### **Performance Optimization**

```yaml
smart_monitoring_settings:
  dynamic_pagination: true  # Adjust page count based on results
  adaptive_timeouts: true  # Adjust timeouts based on response time
  performance_tracking: true  # Track and optimize performance
  
  # Adaptive settings
  min_pages_to_scan: 1
  max_pages_to_scan: 10
  page_scan_threshold: 0.8  # Scan more pages if 80% of current pages have results
  
  # Performance thresholds
  slow_response_threshold: 10  # Seconds
  fast_response_threshold: 2  # Seconds
```

### **Advanced Smart Settings**

```yaml
smart_monitoring_settings:
  # Machine learning features
  predict_new_listings: true  # Use patterns to predict when new listings appear
  optimize_scan_times: true  # Optimize when to scan based on historical data
  
  # Adaptive behavior
  learn_from_errors: true  # Learn from failed requests
  adjust_strategy: true  # Adjust scraping strategy based on success rate
  
  # Resource management
  memory_optimization: true  # Optimize memory usage
  cpu_optimization: true  # Optimize CPU usage
```

## 🔧 **Environment-Specific Configuration**

### **Development Environment**

```yaml
# Development settings
browser:
  headless: false  # Show browser for debugging
  timeout: 60  # Longer timeouts for debugging

monitoring:
  check_interval_minutes: 1  # Frequent checks for testing
  max_pages_to_scan: 2  # Fewer pages for faster testing

notification:
  console_alerts: true
  log_alerts: true
  email_enabled: false  # Disable email in development
```

### **Production Environment**

```yaml
# Production settings
browser:
  headless: true  # Run headless for efficiency
  timeout: 30  # Standard timeouts

monitoring:
  check_interval_minutes: 10  # Normal check interval
  max_pages_to_scan: 5  # Standard page count

notification:
  console_alerts: false  # Disable console in production
  log_alerts: true
  email_enabled: true  # Enable email notifications
```

## 🚨 **Troubleshooting Configuration**

### **Common Issues**

1. **API Authentication Fails**
   ```yaml
   api_integration:
     auth_timeout_hours: 0.5  # Re-authenticate more frequently
     max_retries: 5  # Increase retry attempts
   ```

2. **Browser Timeouts**
   ```yaml
   browser:
     timeout: 60  # Increase timeout
     wait_time: 5  # Increase wait time
   ```

3. **Too Many Notifications**
   ```yaml
   notification:
     enabled: true
     console_alerts: false  # Disable console alerts
     log_alerts: true  # Keep log alerts
   ```

4. **Performance Issues**
   ```yaml
   monitoring:
     max_pages_to_scan: 3  # Reduce pages to scan
     check_interval_minutes: 15  # Increase interval
   ```

### **Debug Configuration**

```yaml
# Debug settings
browser:
  headless: false  # Show browser
  timeout: 120  # Very long timeout

monitoring:
  check_interval_minutes: 1  # Very frequent checks
  max_pages_to_scan: 1  # Scan only one page

notification:
  console_alerts: true
  log_alerts: true
  alert_format: "detailed"  # Detailed alerts
```

## 📋 **Configuration Best Practices**

1. **Start with Defaults**: Use default settings and adjust as needed
2. **Test Incrementally**: Make small changes and test each one
3. **Monitor Performance**: Track system performance after configuration changes
4. **Document Changes**: Keep notes of configuration changes and their effects
5. **Backup Configurations**: Save working configurations for different environments
6. **Validate Settings**: Use the configuration validator to check settings

## 🔍 **Configuration Validation**

The system includes built-in configuration validation:

```python
# Validate configuration
def validate_config(config: dict) -> List[str]:
    """Validate configuration and return list of issues."""
    issues = []
    
    # Check required fields
    required_fields = ['search', 'monitoring', 'browser', 'database']
    for field in required_fields:
        if field not in config:
            issues.append(f"Missing required field: {field}")
    
    # Check value ranges
    if config.get('monitoring', {}).get('check_interval_minutes', 0) < 1:
        issues.append("Check interval must be at least 1 minute")
    
    return issues
```

---

**Last Updated**: July 2025  
**Version**: 2.0  
**Status**: Production Ready ✅ 