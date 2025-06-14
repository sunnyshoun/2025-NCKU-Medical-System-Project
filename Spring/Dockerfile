# Dockerfile
# Use official Maven image with Java 21 for building the application
FROM maven:3.9.9-eclipse-temurin-21 AS build

# Set the working directory in the container
WORKDIR /app

# Copy the Maven project file (pom.xml) to the container
# This allows Maven to download dependencies and leverage Docker's cache if pom.xml is unchanged
COPY pom.xml .

# Copy the project source code to the container
COPY src ./src

# Package the Spring Boot application as an executable JAR file
# Skip tests to speed up the build
RUN mvn clean install -Dmaven.test.skip=true

# --- Second stage: Run the application ---
# Use a lightweight Java 21 JRE image for the runtime
FROM eclipse-temurin:21-jre

# Set the working directory in the container
WORKDIR /app

# Copy the JAR file from the build stage to the runtime image
COPY --from=build /app/target/*.jar app.jar

# Define the command to run the application
ENTRYPOINT ["java", "-jar", "app.jar"]

# Expose the port the application listens on (matches server.port in application.yml)
EXPOSE 8080