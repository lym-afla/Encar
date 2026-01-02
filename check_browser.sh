#!/bin/bash
# Browser Detection and Launch Script for Remote X11 Access
# Usage: ./check_browser.sh

echo "========================================="
echo "Browser Detection Script"
echo "========================================="
echo ""

# Check if X11 is working
echo "1. Checking X11 Forwarding..."
if [ -z "$DISPLAY" ]; then
    echo "   ❌ X11 forwarding NOT working - DISPLAY variable is empty"
    echo "   → Reconnect with: ssh -X username@server"
    exit 1
else
    echo "   ✅ X11 forwarding working - DISPLAY=$DISPLAY"
fi
echo ""

# Check for browsers
echo "2. Checking installed browsers..."
BROWSER_FOUND=""

# Check Chromium
if command -v chromium-browser &> /dev/null; then
    echo "   ✅ chromium-browser found: $(which chromium-browser)"
    BROWSER_FOUND="chromium-browser"
elif command -v chromium &> /dev/null; then
    echo "   ✅ chromium found: $(which chromium)"
    BROWSER_FOUND="chromium"
else
    echo "   ❌ Chromium not found"
fi

# Check Chrome
if command -v google-chrome &> /dev/null; then
    echo "   ✅ google-chrome found: $(which google-chrome)"
    [ -z "$BROWSER_FOUND" ] && BROWSER_FOUND="google-chrome"
elif command -v google-chrome-stable &> /dev/null; then
    echo "   ✅ google-chrome-stable found: $(which google-chrome-stable)"
    [ -z "$BROWSER_FOUND" ] && BROWSER_FOUND="google-chrome-stable"
else
    echo "   ❌ Google Chrome not found"
fi

# Check Firefox
if command -v firefox &> /dev/null; then
    echo "   ✅ firefox found: $(which firefox)"
    [ -z "$BROWSER_FOUND" ] && BROWSER_FOUND="firefox"
else
    echo "   ❌ Firefox not found"
fi

echo ""

# Check Playwright browsers
echo "3. Checking Playwright browsers..."
if [ -d "$HOME/.local/share/ms-playwright" ]; then
    echo "   ✅ Playwright directory found:"
    ls -1 "$HOME/.local/share/ms-playwright" | grep -E "chromium|firefox|webkit"
else
    echo "   ❌ Playwright browsers not found in ~/.local/share/ms-playwright"
fi

echo ""
echo "========================================="

# Launch browser if found
if [ -n "$BROWSER_FOUND" ]; then
    echo "Selected browser: $BROWSER_FOUND"
    echo ""
    read -p "Launch $BROWSER_FOUND now? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Launching $BROWSER_FOUND..."

        # Launch with appropriate flags
        if [[ "$BROWSER_FOUND" == *"chromium"* ]] || [[ "$BROWSER_FOUND" == *"chrome"* ]]; then
            $BROWSER_FOUND --no-sandbox &
        else
            $BROWSER_FOUND &
        fi

        echo "✅ Browser launched in background (PID: $!)"
        echo "   To close: killall $BROWSER_FOUND"
    fi
else
    echo "❌ No browser found!"
    echo ""
    echo "Install one with:"
    echo "  sudo apt install chromium-browser -y"
    echo "  OR"
    echo "  sudo apt install firefox -y"
fi

echo "========================================="
