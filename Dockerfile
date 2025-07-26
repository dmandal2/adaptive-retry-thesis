# Use official Maven image with Java 11
FROM maven:3.8.6-openjdk-11

# Set working directory
WORKDIR /usr/src/app

# Copy the whole project into the container
COPY . .

# Build the project
RUN mvn clean install

# Run tests
CMD ["mvn", "test"]
