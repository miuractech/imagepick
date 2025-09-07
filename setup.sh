#!/bin/bash

# Ensure the script is run with root privileges
if [[ "$EUID" -ne 0 ]]; then
  echo "Please run this script with sudo:"
  echo "sudo $0"
  exit 1
fi

# Update package lists
echo "Updating package lists..."
apt-get update

# Install required packages
echo "Installing required packages..."
apt-get install -y \
  python3-watchdog \
  postgresql-client \
  git \
  curl \
  jq \
  sqlite3 \
  unzip \
  ca-certificates \

# Check if all packages were installed successfully
for pkg in python3-watchdog postgresql-client git curl jq sqlite3 unzip ca-certificates python3-venv python3-pip; do
  if dpkg -s "$pkg" >/dev/null 2>&1; then
    echo "$pkg installed successfully."
  else
    echo "Failed to install $pkg."
    exit 1
  fi
done
