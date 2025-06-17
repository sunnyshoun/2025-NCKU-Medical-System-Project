# Dockerfile
# 多階段構建：構建階段
FROM maven:3.9.9-eclipse-temurin-21 AS build

# 設置工作目錄
WORKDIR /app

# 先複製 pom.xml 和 Maven wrapper（利用 Docker 緩存層）
COPY pom.xml ./
COPY mvnw ./
COPY .mvn .mvn

# 下載依賴（這一層會被緩存，除非 pom.xml 改變）
RUN mvn dependency:go-offline -B

# 複製源代碼
COPY src ./src

# 編譯應用程式
RUN mvn clean package -DskipTests -B

# 多階段構建：運行階段
FROM eclipse-temurin:21-jre-alpine

# 創建非 root 用戶
RUN addgroup -g 1000 spring && \
    adduser -u 1000 -G spring -s /bin/sh -D spring

# 設置工作目錄
WORKDIR /app

# 設置 JVM 參數優化
ENV JAVA_OPTS="-Xms512m -Xmx1024m -XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0"

# 從構建階段複製 JAR 檔案
COPY --from=build /app/target/*.jar app.jar

# 更改文件所有權
RUN chown spring:spring app.jar

# 切換到非 root 用戶
USER spring

# 健康檢查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/actuator/health || exit 1

# 暴露端口
EXPOSE 8080

# 啟動命令
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]