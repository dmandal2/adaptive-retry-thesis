# Use Maven with JDK 11
FROM maven:3.8.6-openjdk-11

# Create app directory
WORKDIR /usr/src/app

# Copy the Maven project files
COPY . .

# Install dependencies and compile code (skip tests here)
RUN mvn clean install -DskipTests

# Run tests at runtime (allows us to see retry logic)
CMD ["mvn", "test"]
