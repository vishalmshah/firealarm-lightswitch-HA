#!/bin/bash
set -e

# ---- Must run as root ----
if [ "$EUID" -ne 0 ]; then
    echo "Error: run this script with sudo."
    echo "  sudo bash setup.sh"
    exit 1
fi

DIR="$(pwd)"
SYS_DIR="$DIR/system"

echo "========================================"
echo " Starting Fire Alarm Node Setup"
echo "========================================"

# 1. Install OS Dependencies
echo "Installing python3-venv..."
apt-get update -y
apt-get install -y python3-venv

# 2. Setup Python Virtual Environment
echo "Setting up Python Virtual Environment..."
if [ ! -d "$DIR/venv" ]; then
    python3 -m venv --system-site-packages "$DIR/venv"
fi
"$DIR/venv/bin/pip" install -r "$DIR/requirements.txt"

# 3. Apply Wi-Fi Configuration
echo "Applying NetworkManager Wi-Fi config..."
mkdir -p /etc/NetworkManager/conf.d
cp "$SYS_DIR/wifi_powersave.conf" /etc/NetworkManager/conf.d/99-disable-wifi-powersave.conf
systemctl restart NetworkManager || true

# 4. Apply Watchdog Configuration
echo "Applying Systemd Watchdog config..."
mkdir -p /etc/systemd/system.conf.d
cp "$SYS_DIR/watchdog.conf" /etc/systemd/system.conf.d/watchdog.conf

echo "Applying hardware boot configuration..."
BOOT_DIR="/boot"
[ -d "/boot/firmware" ] && BOOT_DIR="/boot/firmware"
cp "$SYS_DIR/usercfg.txt" "$BOOT_DIR/usercfg.txt"

# 5. Apply and Start Systemd Service
echo "Applying Fire Alarm service..."
# Read template, replace {{PROJECT_ROOT}} with $DIR, and write directly to systemd
sed "s|{{PROJECT_ROOT}}|$DIR|g" "$SYS_DIR/firealarm.service.template" > /etc/systemd/system/firealarm.service

systemctl daemon-reload
systemctl enable firealarm.service
systemctl restart firealarm.service

echo ""
echo "========================================"
echo " Setup complete! Node is fully configured."
echo "========================================"
echo "Useful commands:"
echo "  sudo systemctl status firealarm   — check process status"
echo "  sudo journalctl -u firealarm -f   — view live streaming logs"
echo ""