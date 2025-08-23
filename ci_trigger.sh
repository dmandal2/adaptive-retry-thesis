#!/bin/bash

# 1️⃣ Set timestamp
TIMESTAMP=$(date +'%Y%m%d-%H%M%S')

# 2️⃣ Run tests inside a fresh Docker container
echo "Running tests inside container..."
docker-compose run --rm app mvn clean test

# 3️⃣ Copy retry log to a timestamped file
echo "Saving retry log..."
cp logs/test-retry.log logs/test-retry-$TIMESTAMP.log

echo "CI trigger script finished! Logs saved to logs/test-retry-$TIMESTAMP.log"

