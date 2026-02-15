#!/bin/bash

# Tyboo Studio v1.0 - One-Click Deployment Script
# This script builds and starts the entire stack using Docker Compose.

echo "🚀 Starting Tyboo Studio Deployment..."

# 1. Check for required tools
if ! [ -x "$(command -v docker)" ]; then
  echo '❌ Error: docker is not installed.' >&2
  exit 1
fi

if ! [ -x "$(command -v docker-compose)" ]; then
  echo '❌ Error: docker-compose is not installed.' >&2
  exit 1
fi

# 2. Build and start services
echo "📦 Building containers (this may take a few minutes)..."
docker-compose up -d --build

echo "✅ Deployment Successful!"
echo "------------------------------------------------"
echo "🌐 Frontend: http://localhost:3000"
echo "🛠️  API Hub:  http://localhost:8000"
echo "📊 Monitoring: Use 'docker-compose logs -f' to see real-time logs"
echo "------------------------------------------------"
echo "Happy Automating! 🤖✨"
