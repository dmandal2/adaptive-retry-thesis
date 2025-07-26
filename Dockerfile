# Use an official Maven image with JDK 17
FROM maven:3.9.4-eclipse-temurin-17

# Set working directory inside container
WORKDIR /app

# Copy everything from your local project to the container
COPY . .

# Build the Maven project (downloads dependencies and compiles)
RUN mvn clean install

# Run TestNG test suite
CMD ["mvn", "test"]
