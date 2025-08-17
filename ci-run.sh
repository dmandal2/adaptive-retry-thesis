#!/bin/bash
# ------------------------------
# CI/CD Simulation Script
# ------------------------------

cd ~/adaptive-retry-thesis

echo "===== [CI/CD Simulation Started at $(date)] ====="

# Step 1: Pull latest code
git pull origin main

# Step 2: Build project with Maven
mvn clean install -DskipTests

# Step 3: Run tests inside Docker
docker build -t retry-thesis .
docker run --rm retry-thesis

echo "===== [CI/CD Simulation Finished at $(date)] ====="
