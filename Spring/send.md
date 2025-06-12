## API 功能測試 (Postman)

Docker服務成功啟動，後端應用程式會在 `http://localhost:8080` 上監聽請求。

測試API：

### ** 測試 1：註冊 (`POST /api/auth/register`)**

-   **Method:** `POST`
-   **URL:** `http://localhost:8080/api/auth/register`
-   **Headers:** `Content-Type: application/json`
-   **Body (raw, JSON):**
    ```json
    {
        "email": "testuser1@example.com",  
        "username": "testuser1",             
        "password": "testuser1pass",      
        "age": "20",                          
        "gender": "Female",
        "job": "Student"
    }
    ```
-   **預期回應:** `Status: 201 Created`, `Body: {"status": "ok", "jwt": "eyJ..."}`
-   **操作:** **複製此回應中的 JWT Token** 後續測試使用。

### ** 測試 2：用戶登入 (`POST /api/auth/login`)**

-   **Method:** `POST`
-   **URL:** `http://localhost:8080/api/auth/login`
-   **Headers:** `Content-Type: application/json`
-   **Body (raw, JSON):**
    ```json
    {
        "username": "testuser1",  
        "password": "testuser1pass"       
    }
    ```
-   **預期回應:** `Status: 200 OK`, `Body: {"status": "ok", "jwt": "eyJ..."}`
-   **操作:** **複製此回應中的 JWT Token**，這是登入後獲取的新Token，用於訪問所有受保護 API。

### ** 測試 3：新增一條視力檢查記錄 (`POST /api/user/records`)**

-   **Method:** `POST`
-   **URL:** `http://localhost:8080/api/user/records`
-   **Headers:**
    -   `Content-Type: application/json`
    -   `Authorization: Bearer [從測試 2 獲取的 JWT Token]` (注意 "Bearer " 後有一個空格)
-   **Body (raw, JSON):**
    ```json
    {
        "corrL": "1.1", "diopterL": "-0.2", "corrR": "2.2", "diopterR": "-0.0",
        "uncoL": "2.0", "uncoR": "2.0"
    }
    ```
-   **預期回應:** `Status: 201 Created`

### ** 測試 4：獲取當前登入用戶的所有視力檢查紀錄 (`GET /api/user/records`)**

-   **Method:** `GET`
-   **URL:** `http://localhost:8080/api/user/records`
-   **Headers:**
    -   `Authorization: Bearer [從測試 2 獲取的 JWT Token]`
-   **Body:** 無需設定。
-   **預期回應:** `Status: 200 OK`, `Body` 為包含新增記錄的json陣列。

### ** 測試 5：根據 ID 獲取知識資料 (`GET /api/knowledge/{id}`)**

-   **Method:** `GET`
-   **URL:** `http://localhost:8080/api/knowledge/initial-knowledge-1` (替換為您新增的知識 ID)
-   **Headers:**
    -   `Authorization: Bearer [從測試 2 獲取的 JWT Token]`
-   **預期回應:** `Status: 200 OK`, `Body` 為對應知識資料的json物件。
