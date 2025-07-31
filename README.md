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
# Start continuous monitoring (Recommended)
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
- `data_storage.py` - SQLite database management (consolidated)
- `notification.py` - Alert system

### **Utilities**
- `monetary_utils.py` - Korean won conversion utilities (updated to use 만원)
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
- Korean monetary unit handling (만원 format)

### **Real-time Monitoring**
- Continuous monitoring with configurable intervals
- View count analysis for "fresh" listings
- Registration date extraction from tooltips

### **Data Analysis**
- Export to CSV for analysis
- Advanced filtering and sorting
- Cost comparison tools

## 📊 **Performance**

| Aspect | Legacy Browser | Current API | Improvement |
|--------|---------------|-------------|-------------|
| **Speed** | ~30s/page | ~5s/page | **6x faster** |
| **Reliability** | Medium | High | **More stable** |
| **Resource Usage** | High | Low | **Efficient** |
| **Maintenance** | High | Low | **Easier** |

## 📚 **Documentation**

All documentation has been consolidated in the `/docs` folder:

- **[API Guide](docs/API_GUIDE.md)** - API-based system documentation
- **[Lease System](docs/LEASE_SYSTEM.md)** - Lease vehicle detection and analysis
- **[Filter Tools](docs/FILTER_TOOLS.md)** - Advanced filtering and analysis tools
- **[Configuration](docs/CONFIGURATION.md)** - System configuration guide
- **[Project Summary](docs/PROJECT_SUMMARY.md)** - Complete project overview

## ⚠️ **Legacy System Status**

The following modules are **deprecated** and will be removed in future versions:
- `encar_scraper.py` - Legacy browser-only scraper
- `encar_monitor.py` - Legacy browser-based monitor
- `lease_detail_scraper.py` - Legacy lease extraction
- `database_deals.py` - Legacy database operations
- `database_query_enhanced.py` - Legacy database queries

**Recommendation**: Use the API-based system for all new deployments.

## 💰 **Monetary System**

The system now uses **만원 (million won)** consistently throughout:
- All prices stored in 만원 format
- Database operations use 만원 units
- Display and calculations use 만원 format
- Legacy won support has been removed

## 🚀 **Getting Started**

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Configure system**: Edit `config.yaml`
3. **Start monitoring**: `python encar_monitor_api.py`
4. **Analyze data**: `python encar_filter_tools.py`

For detailed documentation, see the `/docs` folder.

---

**Last Updated**: July 2025  
**Version**: 2.0 (API-based system)  
**Status**: Production Ready ✅  
**Recommendation**: Use API-based system for all deployments