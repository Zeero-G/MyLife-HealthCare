#!/bin/bash

echo "==========================================="
echo "🔄 REDEPLOYING MYLIFE SERVICES"
echo "==========================================="

# 1. Stop current containers
echo "Stopping existing containers..."
docker-compose down

# 2. Build and run updated services
echo "Building and starting containers in background..."
docker-compose up --build -d

# 3. Check status
echo "Current container status:"
docker ps

echo "==========================================="
echo "🚀 Redeployment completed successfully!"
echo "==========================================="
