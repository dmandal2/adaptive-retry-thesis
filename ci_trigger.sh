#!/bin/bash

# 1️⃣ Set timestamp
TIMESTAMP=$(date +'%Y%m%d-%H%M%S')

# 2️⃣ Always rebuild (ensures fresh code)
echo "Rebuilding Docker image..."
docker-compose build --no-cache

# 3️⃣ Run tests inside fresh container
echo "Running tests inside container..."
docker-compose run --rm app mvn clean test

# 4️⃣ Save retry log with timestamp
echo "Saving retry log..."
cp logs/test-retry.log logs/test-retry-$TIMESTAMP.log

echo "✅ CI trigger finished! Logs saved to logs/test-retry-$TIMESTAMP.log"
