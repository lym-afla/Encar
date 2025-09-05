#!/bin/bash
# Status check script for Encar Monitor

echo "📊 Encar Monitor Status Check"
echo "==============================="

# Service status
echo "🔧 Service Status:"
if sudo systemctl is-active --quiet encar-monitor; then
    echo "   ✅ Running"
else
    echo "   ❌ Stopped"
fi

sudo systemctl status encar-monitor --no-pager
echo ""

# File checks
echo "📁 File System:"
echo "   Config: $([ -f '/opt/encar-monitor/config.yaml' ] && echo '✅' || echo '❌')"
echo "   Environment: $([ -f '/opt/encar-monitor/.env' ] && echo '✅' || echo '❌')"
echo "   Database: $([ -f '/opt/encar-monitor/data/encar_listings.db' ] && echo '✅' || echo '❌')"
echo ""

# Disk usage
echo "💾 Disk Usage:"
du -sh /opt/encar-monitor/* 2>/dev/null | sort -hr
echo ""

# Recent logs
echo "📝 Recent Logs (last 10 lines):"
sudo journalctl -u encar-monitor -n 10 --no-pager
echo ""

# Memory usage
echo "🧠 Memory Usage:"
ps aux | grep "[e]ncar" | awk '{print $2, $4, $11}' | column -t
echo ""

echo "📈 For real-time logs: sudo journalctl -u encar-monitor -f"
