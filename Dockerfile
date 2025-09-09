# Use Maven + JDK 11 base
FROM maven:3.8.6-openjdk-11

# Install Python3 and pip
RUN apt-get update && apt-get install -y python3 python3-pip

# Install required Python packages
RUN pip3 install pandas matplotlib seaborn

# Create app directory
WORKDIR /usr/src/app

# Copy the project files
COPY . .

# Build Java project (skip tests)
RUN mvn clean install -DskipTests

# Default command
CMD ["mvn", "test"]
