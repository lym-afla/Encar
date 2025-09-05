#!/bin/bash
# Stop script for Encar Monitor

echo "🛑 Stopping Encar Monitor..."

if sudo systemctl is-active --quiet encar-monitor; then
    sudo systemctl stop encar-monitor
    echo "✅ Service stopped successfully!"
else
    echo "ℹ️  Service was not running."
fi

sudo systemctl status encar-monitor --no-pager
