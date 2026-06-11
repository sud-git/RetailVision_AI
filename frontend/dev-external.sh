#!/bin/bash
# Frontend Development Server - External Access Configuration
# This script starts the Next.js dev server with proper host binding

set -e

echo "🚀 Starting RetailVision AI Frontend - External Access Mode"
echo "=========================================================="
echo ""

# Detect local IP address
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  LOCAL_IP=$(ifconfig | grep -A 5 "en0" | grep "inet " | awk '{print $2}')
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
  # Linux
  LOCAL_IP=$(hostname -I | awk '{print $1}')
else
  # Windows/Git Bash
  LOCAL_IP="localhost"
fi

# Fallback to localhost if IP detection fails
if [ -z "$LOCAL_IP" ]; then
  LOCAL_IP="localhost"
fi

echo "📍 Access Points:"
echo "   Local:    http://localhost:3000"
echo "   Network:  http://$LOCAL_IP:3000"
echo ""

# Start development server with 0.0.0.0 binding
echo "📦 Starting Next.js dev server..."
echo ""
npm run dev
