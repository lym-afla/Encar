#!/bin/bash
# Encar Monitor Installation Script for Ubuntu Server
# Run with: chmod +x install.sh && ./install.sh

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="encar-monitor"
INSTALL_DIR="/opt/${APP_NAME}"
SERVICE_USER="$USER"
PYTHON_VERSION="3.10"

echo -e "${BLUE}🚀 Starting Encar Monitor Installation...${NC}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Update system packages
print_status "Updating system packages..."
sudo apt update
# sudo apt upgrade -y # Takes a long time to download and install

# Install system dependencies
print_status "Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    nginx \
    supervisor \
    chromium-browser \
    chromium-chromedriver \
    curl \
    wget \
    unzip

# Create application directory
print_status "Creating application directory..."
sudo mkdir -p "${INSTALL_DIR}"/{logs,data,backups}
sudo chown -R $USER:$USER "${INSTALL_DIR}"

# Copy application files
print_status "Copying application files..."
cp -r . "${INSTALL_DIR}/"
cd "${INSTALL_DIR}"

# Create Python virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
print_status "Installing Playwright browsers..."
playwright install chromium
playwright install chromium-headless-shell

# Setup configuration files
print_status "Setting up configuration files..."

# Copy environment template if .env doesn't exist
if [ ! -f .env ]; then
    if [ -f env.template ]; then
        cp env.template .env
        print_warning "Please edit .env file with your actual credentials"
    else
        print_error "env.template not found!"
        exit 1
    fi
fi

# Copy config template if config.yaml doesn't exist
if [ ! -f config.yaml ]; then
    if [ -f config.template.yaml ]; then
        cp config.template.yaml config.yaml
        print_status "Configuration file created from template"
    else
        print_error "config.template.yaml not found!"
        exit 1
    fi
fi

# Create systemd service file
print_status "Creating systemd service..."

# Copy systemd service file if it exists
if [ -f "scripts/systemd/${APP_NAME}.service" ]; then
    sudo cp "scripts/systemd/${APP_NAME}.service" "/etc/systemd/system/${APP_NAME}.service"
    print_status "Systemd service file copied from template"
else
    # Create service file from scratch
    sudo tee /etc/systemd/system/${APP_NAME}.service > /dev/null << EOF
[Unit]
Description=Encar Monitor Service
After=network.target

[Service]
Type=simple
User=${SERVICE_USER}
WorkingDirectory=${INSTALL_DIR}
Environment=PATH=${INSTALL_DIR}/venv/bin
EnvironmentFile=${INSTALL_DIR}/.env
ExecStart=${INSTALL_DIR}/venv/bin/python encar_monitor_api.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
fi

# Set permissions
print_status "Setting file permissions..."
chmod +x "${INSTALL_DIR}"/*.py
chmod 600 "${INSTALL_DIR}/.env"  # Protect environment file
sudo chown -R $USER:$USER "${INSTALL_DIR}"

# Reload systemd and enable service
print_status "Configuring systemd service..."
sudo systemctl daemon-reload
sudo systemctl enable ${APP_NAME}

# Create log rotation
print_status "Setting up log rotation..."
sudo tee /etc/logrotate.d/${APP_NAME} > /dev/null << EOF
${INSTALL_DIR}/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    su ${SERVICE_USER} ${SERVICE_USER}
}
EOF

print_status "Installation completed successfully!"

echo -e "\n${BLUE}📋 Next Steps:${NC}"
echo -e "${YELLOW}1.${NC} Edit configuration: nano ${INSTALL_DIR}/.env"
echo -e "${YELLOW}2.${NC} Add your Telegram bot token and chat ID"
echo -e "${YELLOW}3.${NC} Review config: nano ${INSTALL_DIR}/config.yaml"
echo -e "${YELLOW}4.${NC} Start the service: sudo systemctl start ${APP_NAME}"
echo -e "${YELLOW}5.${NC} Check status: sudo systemctl status ${APP_NAME}"
echo -e "${YELLOW}6.${NC} View logs: sudo journalctl -u ${APP_NAME} -f"

echo -e "\n${GREEN}🎉 Installation Complete!${NC}"
echo -e "${BLUE}📁 Application installed to: ${INSTALL_DIR}${NC}"
echo -e "${BLUE}🔧 Service name: ${APP_NAME}${NC}"
