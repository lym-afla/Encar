# 🚀 Encar Monitor - Server Deployment Guide

Deploy the Encar Monitor service on Ubuntu 22.04 LTS server with automated setup and systemd service management.

## 📋 Prerequisites

- **Server**: Ubuntu 22.04.5 LTS or newer
- **User**: Non-root user with sudo privileges
- **Resources**: Minimum 1GB RAM, 2GB storage
- **Network**: Internet access for package installation
- **Telegram**: Bot token and chat ID (see setup below)

## 🏗️ Quick Installation

### 1. **Clone Repository**

**Start from any directory** (e.g., `/home/ubuntu` or `/tmp`):
```bash
# Clone the repository
git clone https://github.com/lym-afla/Encar.git encar-monitor
cd encar-monitor
```

### 2. **Run Installation Script**
```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

The script will automatically:
- ✅ Install system dependencies
- ✅ Create Python virtual environment
- ✅ Install Python packages
- ✅ Setup Playwright browsers
- ✅ Create systemd service
- ✅ Configure log rotation
- ✅ Set file permissions

### 3. **Configure Environment**
```bash
# Edit environment variables
nano /opt/encar-monitor/.env

# Add your Telegram credentials:
TELEGRAM_BOT_TOKEN=your_actual_bot_token
TELEGRAM_CHAT_ID=your_actual_chat_id
```

### 4. **Start Service**
```bash
sudo systemctl start encar-monitor
sudo systemctl status encar-monitor
```

## 🤖 Telegram Bot Setup

### **Create Bot**
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot`
3. Choose a name: `Encar Monitor Bot`
4. Choose a username: `your_encar_monitor_bot`
5. Save the **bot token** (format: `123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### **Get Chat ID**
1. Message your bot first
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Find your **chat ID** in the response (usually a number like `404346140`)

### **Test Connection**
```bash
cd /opt/encar-monitor
source venv/bin/activate
python -c "
from notification import NotificationManager
import asyncio

async def test():
    nm = NotificationManager()
    await nm.test_telegram_connection()

asyncio.run(test())
"
```

## 📁 File Structure

```
/opt/encar-monitor/
├── 📁 venv/                    # Python virtual environment
├── 📁 logs/                    # Application logs
├── 📁 data/                    # SQLite database
├── 📁 backups/                 # Database backups
├── 📁 scripts/                 # Deployment scripts
│   ├── 🚀 install.sh           # Installation script
│   ├── ▶️ start.sh             # Start service script
│   ├── ⏹️ stop.sh              # Stop service script
│   ├── 📊 check_status.sh      # Status check script
│   ├── 🐍 server_launch.py     # Server management interface
│   └── 📁 systemd/
│       └── 🔧 encar-monitor.service  # Systemd service template
├── 🔧 .env                     # Environment variables (sensitive)
├── ⚙️ config.yaml              # Application configuration
├── 🐍 *.py                     # Python source files
├── 📄 requirements.txt         # Python dependencies
└── 🚀 launch.py                # Local development launcher (not used in production)
```

## 🔐 Security Configuration

### **Environment Variables (.env)**

Copy `env.template` to `.env` and configure:

```bash
# Required - Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Optional - Paths (defaults provided)
DATABASE_PATH=/opt/encar-monitor/data/encar_listings.db
LOG_PATH=/opt/encar-monitor/logs/

# Optional - Monitoring intervals
CHECK_INTERVAL_MINUTES=15
QUICK_SCAN_INTERVAL_MINUTES=5
```

### **File Permissions**
```bash
# Environment file (sensitive)
chmod 600 .env

# Application directory
chown -R ubuntu:ubuntu /opt/encar-monitor

# Logs directory (writable)
chmod 755 logs/ data/
```

## 🚀 Service Management Options

### **Method 1: Systemd Service (Recommended for Production)**

The service runs automatically in the background:

### **Systemd Commands**
```bash
# Start service
sudo systemctl start encar-monitor

# Stop service
sudo systemctl stop encar-monitor

# Restart service
sudo systemctl restart encar-monitor

# Enable auto-start on boot
sudo systemctl enable encar-monitor

# Check status
sudo systemctl status encar-monitor

# View logs (real-time)
sudo journalctl -u encar-monitor -f

# View logs (last 100 lines)
sudo journalctl -u encar-monitor -n 100
```

### **Method 2: Interactive Server Management**

For interactive management, use the server launcher:

```bash
cd /opt/encar-monitor
python3 scripts/server_launch.py
```

**Features:**
- ✅ Interactive menu for service management
- ✅ Real-time log viewing
- ✅ Health checks and diagnostics
- ✅ Manual testing capabilities
- ✅ Configuration validation

### **Method 3: Quick Scripts**

For quick operations:

```bash
cd /opt/encar-monitor

# Quick start
./scripts/start.sh

# Quick stop  
./scripts/stop.sh

# Check status
./scripts/check_status.sh
```

### **Service Configuration**
- **User**: `ubuntu`
- **Working Directory**: `/opt/encar-monitor`
- **Auto-restart**: Yes (10 second delay)
- **Logging**: systemd journal + file logs

## 📊 Monitoring & Logs

### **Log Files**
```bash
# Application logs
tail -f /opt/encar-monitor/logs/encar_alerts.log

# Monitor logs  
tail -f /opt/encar-monitor/logs/encar_monitor.log

# System logs
sudo journalctl -u encar-monitor -f
```

### **Health Checks**
```bash
# Check service status
systemctl is-active encar-monitor

# Check process
ps aux | grep encar

# Check database
ls -la /opt/encar-monitor/data/

# Test Telegram
curl -X GET "https://api.telegram.org/bot<TOKEN>/getMe"
```

## 🔄 Updates & Maintenance

### **Update Code**
```bash
cd /opt/encar-monitor
git pull origin main
sudo systemctl restart encar-monitor
```

### **Update Dependencies**
```bash
cd /opt/encar-monitor
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart encar-monitor
```

### **Database Backup**
```bash
# Manual backup
cp /opt/encar-monitor/data/encar_listings.db \
   /opt/encar-monitor/backups/backup_$(date +%Y%m%d_%H%M%S).db

# Automated backup (add to cron)
0 2 * * * cp /opt/encar-monitor/data/encar_listings.db /opt/encar-monitor/backups/daily_$(date +%Y%m%d).db
```

## 🛠️ Troubleshooting

### **Common Issues**

#### **Service Won't Start**
```bash
# Check service status
sudo systemctl status encar-monitor

# Check configuration
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Check environment
cd /opt/encar-monitor && source venv/bin/activate && python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('TELEGRAM_BOT_TOKEN'))"
```

#### **Telegram Notifications Not Working**

If startup notifications aren't arriving on production:

```bash
# Quick test - run comprehensive Telegram debugging
cd /opt/encar-monitor
python debug_telegram_production.py

# Manual tests
# 1. Test bot token
curl -X GET "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"

# 2. Test message sending
curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/sendMessage" \
     -d "chat_id=<YOUR_CHAT_ID>&text=Test message"

# 3. Check environment variables in service context
sudo systemctl show encar-monitor | grep -E 'TELEGRAM|Environment'

# 4. Test notification system manually
source venv/bin/activate
python -c "
from notification import NotificationManager
nm = NotificationManager()
nm.send_monitoring_status('TEST', 'Manual test from production', send_to_telegram=True)
"

# 5. Check service logs for telegram errors
sudo journalctl -u encar-monitor -f | grep -i telegram
```

**Common Issues:**
- Environment variables not loaded in systemd context
- Bot token or chat ID incorrect in production `.env` file  
- Network connectivity issues from server
- Telegram API rate limiting

#### **Browser Issues**
```bash
# Install Chromium dependencies
sudo apt install -y chromium-browser chromium-chromedriver

# Test Playwright
cd /opt/encar-monitor
source venv/bin/activate
playwright install chromium
playwright install chromium-headless-shell
```

#### **Playwright Headless Shell Issues (Systemd Services)**

If the service fails with "Executable doesn't exist at .../headless_shell":

```bash
# Install headless shell specifically for systemd services
cd /opt/encar-monitor
source venv/bin/activate

# Install OS dependencies
sudo /opt/encar-monitor/venv/bin/playwright install-deps

# Install headless shell to app-local directory
PLAYWRIGHT_BROWSERS_PATH=/opt/encar-monitor/ms-playwright playwright install chromium-headless-shell

# Create required directories
sudo mkdir -p /opt/encar-monitor/.cache /opt/encar-monitor/ms-playwright
sudo chown -R user1:user1 /opt/encar-monitor  # Replace user1 with your actual user

# Update systemd service to use app-local browsers
sudo nano /etc/systemd/system/encar-monitor.service
```

Add these environment variables to the service file:
```ini
[Service]
# ... existing settings ...
Environment=PLAYWRIGHT_BROWSERS_PATH=/opt/encar-monitor/ms-playwright
Environment=XDG_CACHE_HOME=/opt/encar-monitor/.cache
Environment=PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true

# Update ReadWritePaths to include browser directories
ReadWritePaths=/opt/encar-monitor/logs /opt/encar-monitor/data /opt/encar-monitor/ms-playwright /opt/encar-monitor/.cache
```

Then reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart encar-monitor

# Verify environment is set
systemctl show encar-monitor | grep -E 'PLAYWRIGHT|XDG_CACHE_HOME'

# Verify binary exists
find /opt/encar-monitor/ms-playwright -name headless_shell -type f
```

#### **Permission Issues**
```bash
# Fix ownership (replace ubuntu with your actual user)
sudo chown -R ubuntu:ubuntu /opt/encar-monitor

# Fix permissions
chmod 600 /opt/encar-monitor/.env
chmod 755 /opt/encar-monitor/logs
chmod 755 /opt/encar-monitor/data
chmod 755 /opt/encar-monitor/ms-playwright
chmod 755 /opt/encar-monitor/.cache
```

### **Performance Optimization**

#### **Memory Usage**
```bash
# Monitor memory
free -h
ps aux --sort=-%mem | head

# Optimize browser settings in config.yaml
browser:
  headless: true
  timeout: 30
```

#### **Disk Space**
```bash
# Check disk usage
df -h
du -sh /opt/encar-monitor/*

# Clean old logs
find /opt/encar-monitor/logs -name "*.log" -mtime +30 -delete
```

## 📈 Scaling & Advanced Configuration

### **Multiple Instances**
```bash
# Copy to different directory
cp -r /opt/encar-monitor /opt/encar-monitor-2

# Create separate service
sudo cp /etc/systemd/system/encar-monitor.service \
        /etc/systemd/system/encar-monitor-2.service

# Edit service file
sudo nano /etc/systemd/system/encar-monitor-2.service
```

### **Nginx Reverse Proxy** (Optional)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /encar-status {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📞 Support

### **Useful Commands**
```bash
# Full system status
systemctl status encar-monitor
journalctl -u encar-monitor --since "1 hour ago"
tail -f /opt/encar-monitor/logs/*.log

# Environment check
cd /opt/encar-monitor && source venv/bin/activate && python -c "
import sys, yaml, os
from dotenv import load_dotenv
load_dotenv()
print(f'Python: {sys.version}')
print(f'Telegram Token: {\"✅\" if os.getenv(\"TELEGRAM_BOT_TOKEN\") else \"❌\"}')
print(f'Chat ID: {\"✅\" if os.getenv(\"TELEGRAM_CHAT_ID\") else \"❌\"}')
"
```

### **Log Analysis**
```bash
# Error patterns
grep -i error /opt/encar-monitor/logs/*.log | tail -20

# Telegram issues
grep -i telegram /opt/encar-monitor/logs/*.log | tail -10

# Database issues
grep -i database /opt/encar-monitor/logs/*.log | tail -10
```

---

## 🎉 Success!

Your Encar Monitor should now be running and sending notifications to Telegram. The service will:

- ✅ **Auto-start** on server boot
- ✅ **Auto-restart** if it crashes
- ✅ **Monitor continuously** for new car listings
- ✅ **Send Telegram alerts** for new finds
- ✅ **Log all activity** for debugging
- ✅ **Rotate logs** automatically

**Next Steps:**
1. Monitor logs to ensure it's working: `sudo journalctl -u encar-monitor -f`
2. Wait for first Telegram notification
3. Check database growth: `ls -la /opt/encar-monitor/data/`

**Questions?** Check the troubleshooting section or examine the logs for specific error messages.
