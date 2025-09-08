#!/bin/bash

# Ensure the script is run with root privileges
if [[ "$EUID" -ne 0 ]]; then
  echo "Please run this script with sudo:"
  echo "sudo $0"
  exit 1
fi

# Create test directory in home path
echo "Creating test directory in home path..."
mkdir -p ~/test

# Update package lists
echo "Updating package lists..."
apt-get update

# Install required packages
echo "Installing required packages..."
apt-get install -y \
  python3 \
  python3-pip \
  python3-watchdog \
  postgresql-client \
  git \
  curl \
  jq \
  sqlite3 \
  unzip \
  ca-certificates

# Check if all packages were installed successfully
for pkg in python3 python3-pip python3-watchdog postgresql-client git curl jq sqlite3 unzip ca-certificates; do
  if dpkg -s "$pkg" >/dev/null 2>&1; then
    echo "$pkg installed successfully."
  else
    echo "Failed to install $pkg."
    exit 1
  fi
done

# Clone or update the imagepick repository
echo "Ensuring imagepick repository is present..."
REPO_URL="https://github.com/miuractech/imagepick"
DEST_DIR="/opt/imagepick"

# If we're already in a git repo, skip cloning
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Current directory is a git repository. Skipping clone."
else
  if [ -d "$DEST_DIR/.git" ]; then
    echo "Repository already exists at $DEST_DIR. Pulling latest changes..."
    git -C "$DEST_DIR" fetch --all
    git -C "$DEST_DIR" pull --ff-only
  elif [ -d "$DEST_DIR" ]; then
    echo "Directory $DEST_DIR exists but is not a git repository. Skipping clone."
  else
    echo "Cloning repository to $DEST_DIR..."
    mkdir -p "/opt"
    mkdir -p "~/test"
    git clone "$REPO_URL" "$DEST_DIR"
  fi
fi

# Copy service file to systemd directory
echo "Installing systemd service..."
cp /opt/imagepick/folder_watecher.service /etc/systemd/system/folder-watcher.service

chown root:root /opt/imagepick/listner.py
chmod +x /opt/imagepick/listner.py
chown root:root /opt/imagepick/folder_watecher.service
chmod +x /opt/imagepick/folder_watecher.service
chown root:root /opt/imagepick/test_execute.py
chmod +x /opt/imagepick/test_execute.py
systemctl daemon-reload
systemctl enable folder-watcher.service
systemctl start folder-watcher.service
systemctl daemon-reload


