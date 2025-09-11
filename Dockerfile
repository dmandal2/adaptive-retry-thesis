# Use Maven with JDK 11
FROM maven:3.8.6-openjdk-11

# Install Python and plotting libs for analysis
RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install --no-cache-dir pandas matplotlib

# Create app directory
WORKDIR /usr/src/app

# Copy the Maven project files
COPY . .

# Install dependencies and compile code (skip tests here)
RUN mvn clean install -DskipTests

# Run tests at runtime (allows us to see retry logic)
CMD ["mvn", "test"]
