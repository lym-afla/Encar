#!/bin/bash
# Quick start script for Encar Monitor

set -e

echo "🚀 Starting Encar Monitor..."

# Check if installed
if [ ! -d "/opt/encar-monitor" ]; then
    echo "❌ Encar Monitor not installed. Run install.sh first."
    exit 1
fi

# Check if service exists
if ! sudo systemctl list-unit-files | grep -q encar-monitor; then
    echo "❌ Systemd service not found. Run install.sh first."
    exit 1
fi

# Check configuration
if [ ! -f "/opt/encar-monitor/.env" ]; then
    echo "❌ Environment file not found. Please configure /opt/encar-monitor/.env"
    exit 1
fi

# Start service
echo "🔧 Starting systemd service..."
sudo systemctl start encar-monitor

# Check status
if sudo systemctl is-active --quiet encar-monitor; then
    echo "✅ Service started successfully!"
    echo "📊 Status:"
    sudo systemctl status encar-monitor --no-pager
    echo ""
    echo "📝 To view logs:"
    echo "   sudo journalctl -u encar-monitor -f"
else
    echo "❌ Service failed to start. Check logs:"
    echo "   sudo journalctl -u encar-monitor --no-pager"
    exit 1
fi
