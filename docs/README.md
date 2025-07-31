# Encar Mercedes-Benz GLE Coupe Monitoring System

A comprehensive monitoring system for tracking new Mercedes-Benz GLE Coupe listings on the South Korean automotive website Encar.com.

## 🚗 **System Overview**

This system monitors Encar.com for new Mercedes-Benz GLE Coupe listings using a hybrid approach:
- **Fast API-based bulk data retrieval**
- **Browser automation for complex detail extraction**
- **Advanced lease vehicle detection and cost analysis**
- **Real-time notifications and alerts**

## 📋 **Quick Start**

### 1. Environment Setup
```bash
# Create virtual environment
python -m venv encar_venv

# Activate (Windows)
.\encar_venv\Scripts\activate.ps1

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

### 2. Configuration
Edit `config.yaml` to customize:
- Search parameters (year, price, model)
- Monitoring intervals
- Notification settings
- Database settings

### 3. Run the System
```bash
# Start continuous monitoring
python encar_monitor_api.py

# Quick scan for deals
python quick_deals.py

# Filter and analyze data
python encar_filter_tools.py
```

## 🔧 **Core Components**

### **API-Based System (Recommended)**
- `encar_api_client.py` - API client with authentication
- `encar_scraper_api.py` - Hybrid scraper (API + browser details)
- `encar_monitor_api.py` - API-based monitoring system

### **Database & Storage**
- `data_storage.py` - SQLite database management
- `notification.py` - Alert system

### **Utilities**
- `monetary_utils.py` - Korean won conversion utilities
- `encar_filter_tools.py` - Advanced filtering tools
- `quick_deals.py` - Command-line deal finder

## 🎯 **Key Features**

### **Smart Filtering**
- Filters for "쿠페" (Coupe) models
- Excludes accident/flood damaged vehicles
- Configurable price and year ranges

### **Lease Vehicle Detection**
- Automatic detection of lease vehicles
- True cost calculation (deposit + monthly payments)
- Korean monetary unit handling (만원 ↔ 원)

### **Real-time Monitoring**
- Continuous monitoring with configurable intervals
- View count analysis for "fresh" listings
- Registration date extraction from tooltips

### **Data Analysis**
- Export to CSV for analysis
- Advanced filtering and sorting
- Cost comparison tools

## 📊 **Performance**

| Aspect | Performance |
|--------|-------------|
| **Speed** | ~5 seconds per page (API) |
| **Reliability** | High (with fallbacks) |
| **Resource Usage** | Low (HTTP + minimal browser) |
| **Data Accuracy** | High (hybrid approach) |

## 📚 **Documentation**

- **[API Guide](API_GUIDE.md)** - API-based system documentation
- **[Lease System](LEASE_SYSTEM.md)** - Lease vehicle detection and analysis
- **[Filter Tools](FILTER_TOOLS.md)** - Advanced filtering and analysis tools
- **[Configuration](CONFIGURATION.md)** - System configuration guide

## 🚨 **Legacy System**

The original browser-only system (`encar_scraper.py`, `encar_monitor.py`) is kept for fallback but is **not recommended** for new deployments.

## 📈 **System Evolution**

1. **Phase 1**: Browser-only scraping
2. **Phase 2**: API-based bulk retrieval
3. **Phase 3**: Hybrid approach (API + browser details)
4. **Current**: Optimized with lease detection and monetary fixes

## 🤝 **Contributing**

When contributing to this system:
1. Use the API-based approach for new features
2. Follow the monetary utilities for Korean won handling
3. Test with both lease and purchase vehicles
4. Update documentation for any changes

## 📞 **Support**

For issues or questions:
1. Check the configuration guide
2. Review the API documentation
3. Test with the quick deals tool
4. Check the monitoring logs

---

**Last Updated**: July 2025  
**Version**: 2.0 (API-based system)  
**Status**: Production Ready ✅ 