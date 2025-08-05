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

# Install python3-watchdog and postgresql-client
echo "Installing python3-watchdog and postgresql-client..."
apt-get install -y python3-watchdog postgresql-client

# Check if both packages were installed successfully
for pkg in python3-watchdog postgresql-client; do
  if dpkg -s "$pkg" >/dev/null 2>&1; then
    echo "$pkg installed successfully."
  else
    echo "Failed to install $pkg."
    exit 1
  fi
done
