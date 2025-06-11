# Dockerfile
# 使用基於 OpenJDK 17 的官方 Maven 映像檔作為構建應用程式的基礎
#FROM maven:3.9.6-openjdk-17 AS build
FROM maven:3-openjdk-17 AS build

# 設定容器內的工作目錄
WORKDIR /app

# 將 Maven 專案的核心檔案 (pom.xml) 複製到容器中
# 這樣 Maven 可以在構建前下載依賴，如果 pom.xml 沒有改變，可以利用 Docker 的快取層
COPY pom.xml .

# 將專案的原始碼複製到容器中
COPY src ./src

# 打包 Spring Boot 應用程式為一個可執行的 JAR 檔案
# -Dmaven.test.skip=true 會跳過專案中的所有測試
RUN mvn clean install -Dmaven.test.skip=true

# --- 第二階段：運行應用程式 ---
# 使用一個更輕量級的 OpenJDK 17 JRE 映像檔作為運行時的基礎
# 這個映像檔只包含運行 Java 應用程式所需的最小環境，減小最終映像檔大小
#  FROM openjdk:17-jre-slim
FROM openjdk:17-slim-buster

# 設定容器啟動後的工作目錄
WORKDIR /app

# 將第一階段構建好的 JAR 檔案複製到當前映像檔中
# 假設你的 JAR 檔案名會以 .jar 結尾
COPY --from=build /app/target/*.jar app.jar

# 定義容器啟動時執行的命令
# 這會運行你的 Spring Boot 應用程式
ENTRYPOINT ["java", "-jar", "app.jar"]

# 暴露應用程式監聽的埠號 (與 application.yml 中的 server.port 匹配)
EXPOSE 8080