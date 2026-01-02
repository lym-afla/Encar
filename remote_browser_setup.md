# X11 Forwarding Browser Access - Step by Step Guide

## Part 1: Setup on Your Local Machine (Windows/Mac/Linux)

### **For Windows:**
1. **Download and install VcXsrv:**
   - Download from: https://sourceforge.net/projects/vcxsrv/
   - Install with default settings

2. **Launch VcXsrv (XLaunch):**
   - Start XLaunch from Start Menu
   - Choose "Multiple windows" → Next
   - Choose "Start no client" → Next
   - **IMPORTANT:** Check "Disable access control" → Next
   - Click Finish
   - VcXsrv will run in system tray

3. **Connect with SSH X11 forwarding:**
   - **If using Termius:** X11 forwarding is not well supported, switch to another client
   - **Recommended:** Use Windows PowerShell or Command Prompt:
     ```
     ssh -X your_username@your_server_ip
     ```
   - **OR use PuTTY:**
     - Download PuTTY from: https://www.putty.org/
     - Connection → SSH → X11 → Enable "X11 forwarding"
     - Session → Enter server IP → Open

### **For Mac:**
1. **Install XQuartz:**
   - Download from: https://www.xquartz.org/
   - Install and restart your Mac

2. **Connect with SSH:**
   - Open Terminal
   - Run:
     ```
     ssh -X your_username@your_server_ip
     ```
   - OR with compression for better performance:
     ```
     ssh -XC your_username@your_server_ip
     ```

### **For Linux:**
Works out of the box! Just use:
```bash
ssh -X your_username@your_server_ip
```

---

## Part 2: Commands to Run on Remote Ubuntu 22.04 Server

### **Step 1: Check what browsers are already installed**

Copy and paste these commands in your SSH session:

```bash
# Check for Chromium
which chromium-browser
which chromium

# Check for Chrome
which google-chrome
which google-chrome-stable

# Check for Firefox
which firefox

# Check Playwright browsers
ls -la ~/.local/share/ms-playwright/ 2>/dev/null || echo "Playwright browsers not in home directory"

# If using venv, check there too
if [ -d "encar_venv" ]; then
    echo "Checking Playwright in venv..."
    source encar_venv/bin/activate
    python -c "import playwright; print('Playwright installed in venv')" 2>/dev/null || echo "Playwright not in venv"
    playwright --version 2>/dev/null || echo "Playwright CLI not available"
fi
```

### **Step 2: Install browser if needed**

**If no browser found, install Chromium:**
```bash
sudo apt update
sudo apt install chromium-browser -y
```

**OR install Firefox (lighter for X11):**
```bash
sudo apt install firefox -y
```

### **Step 3: Test X11 connection**

Before launching browser, test if X11 is working:
```bash
# This should show your DISPLAY variable
echo $DISPLAY

# If empty, X11 forwarding is not working
# If shows something like "localhost:10.0", it's working!

# Quick test with a simple GUI app
xeyes &
# You should see eyes following your mouse cursor
# Press Ctrl+C to close
```

### **Step 4: Launch browser**

**For Chromium:**
```bash
chromium-browser --no-sandbox &
# OR
chromium --no-sandbox &
```

**For Firefox:**
```bash
firefox &
```

**For Chrome (if installed):**
```bash
google-chrome --no-sandbox &
```

**Note:** The `&` at the end runs it in background so you can still use the terminal.

---

## Part 3: Troubleshooting

### **If DISPLAY variable is empty:**
```bash
# Check SSH connection
echo $SSH_CONNECTION

# Reconnect with explicit X11 forwarding
exit
# Then reconnect with: ssh -X username@server
```

### **If you get "cannot open display" error:**
```bash
# Install X11 apps package
sudo apt install x11-apps -y

# Check if X11 forwarding is enabled in SSH config
sudo nano /etc/ssh/sshd_config
# Make sure these lines exist and are uncommented:
#   X11Forwarding yes
#   X11DisplayOffset 10
#   X11UseLocalhost yes

# If you changed config, restart SSH
sudo systemctl restart sshd
```

### **If browser is too slow:**
```bash
# Reconnect with compression
exit
# Then: ssh -XC username@server
# The -C flag compresses data for faster rendering
```

### **If you get sandbox errors:**
Always use `--no-sandbox` flag when launching Chromium/Chrome over SSH, as sandboxing doesn't work well with X11 forwarding.

---

## Part 4: Using Playwright's Chromium

If you want to use the Chromium that Playwright installed:

```bash
# Activate your venv
cd /path/to/your/encar/app
source encar_venv/bin/activate

# Find Playwright's Chromium executable
playwright_chromium=$(python3 -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); print(p.chromium.executable_path); p.stop()")

# Launch it
$playwright_chromium --no-sandbox &
```

---

## Quick Reference Commands

**On local machine (before connecting):**
- Windows: Start VcXsrv
- Mac: XQuartz runs automatically after install
- Linux: Nothing needed

**Connect to server:**
```bash
ssh -XC your_username@your_server_ip
```

**On remote server (after connected):**
```bash
# Test X11
echo $DISPLAY

# Launch browser
chromium-browser --no-sandbox &
# OR
firefox &
```

**Close browser:**
```bash
# Find process
ps aux | grep chromium
# OR
ps aux | grep firefox

# Kill it
killall chromium-browser
# OR
killall firefox
```
