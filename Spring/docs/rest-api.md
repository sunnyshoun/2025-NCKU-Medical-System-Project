# REST API 說明文件

本文檔提供了一個基於 REST 的 API 架構範例，涵蓋身份驗證 (AuthController) 和使用者相關功能 (UserController)。所有 API 均使用 JSON 格式進行 request 和 response，並遵循標準 HTTP 狀態碼。

## 基礎資訊
- **基礎 URL**: `/api`
- **Request 格式**: JSON
- **Response 格式**: JSON
- **身份驗證**: 部分 endpoint 需要在 request header 中包含 `Authorization: Bearer <JWT_TOKEN>`

## AuthController

### POST /api/auth/register
**描述**: 使用者註冊，創建新帳戶並返回 JWT Token。

**Request Body**:
```json
{
    "username": "testuser",
    "password": "password",
    "email": "test@example.com"
}
```

**Response**:
- **201 Created**:
```json
{
    "status": "success",
    "message": "註冊成功",
    "data": {
        "accessToken": "...",
        "refreshToken": "..."
    }
}
```
- **400 Bad Request** (資料格式錯誤或缺少欄位):
```json
{
    "status": "error",
    "message": "資料格式錯誤",
    "data": null
}
```
- **409 Conflict** (使用者名稱或 email 已存在):
```json
{
    "status": "error",
    "message": "使用者名稱或 email 已存在",
    "data": null
}
```

### POST /api/auth/login
**描述**: 使用者登入，根據提供的憑證返回 JWT Token。

**Request Body** (可使用 username 或 email):
```json
{
    "username": "testuser",
    "password": "password"
}
```
或
```json
{
    "email": "test@example.com",
    "password": "password"
}
```

**Response**:
- **200 OK**:
```json
{
    "status": "success",
    "message": "登入成功",
    "data": {
        "access_token": "...",
        "refresh_token": "..."
    }
}
```
- **400 Bad Request** (輸入格式錯誤):
```json
{
    "status": "error",
    "message": "缺少必要欄位",
    "data": null
}
```
- **401 Unauthorized** (密碼錯誤):
```json
{
    "status": "error",
    "message": "密碼錯誤",
    "data": null
}
```
- **404 Not Found** (使用者不存在):
```json
{
    "status": "error",
    "message": "使用者不存在",
    "data": null
}
```

### POST /api/auth/logout
**描述**: 註銷 refresh token，執行登出操作。

**Request Header**:
```json
{
    "Authorization": "Bearer ..."
}
```

**Request Body**: 無

**Response**:
- **200 OK**:
```json
{
    "status": "success",
    "message": "登出成功",
    "data": null
}
```
- **401 Unauthorized** (refresh token 遺失或無效):
```json
{
    "status": "error",
    "message": "無效的 refresh token",
    "data": null
}
```

### POST /api/auth/refresh
**描述**: 使用 refresh token 更新 JWT access token。

**Request Header**:
```json
{
    "Authorization": "Bearer ..."
}
```

**Request Body**: 無

**Response**:
- **200 OK**:
```json
{
    "status": "success",
    "message": "Token 更新成功",
    "data": {
        "access_token": "...",
        "refresh_token": "..."
    }
}
```
- **401 Unauthorized** (refresh token 遺失或無效):
```json
{
    "status": "error",
    "message": "無效的 refresh token",
    "data": null
}
```

## UserController

### GET /api/user/records
**描述**: 取得目前登入使用者的視力檢查紀錄。

**Request Header**:
```json
{
    "Authorization": "Bearer ..."
}
```

**Request Body**: 無

**Response**:
- **200 OK**:
```json
{
    "status": "success",
    "message": "成功取得視力紀錄",
    "data": [
        {
            "record_id": "6108738f-cfd7-4e75-8a47-ea2688e89ce3",
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "corr_l": "1.0",
            "corr_r": "0.9",
            "diopter_l": "1.5D",
            "diopter_r": "1.5D",
            "unco_l": "0.5",
            "unco_r": "0.4",
            "created_at": "2025-06-14T11:31:08.782619",
            "updated_at": "2025-06-14T11:31:08.782634"
        }
    ]
}
```
- **401 Unauthorized** (未提供或無效的 access token):
```json
{
    "status": "error",
    "message": "無效的 access token",
    "data": null
}
```

### POST /api/user/records
**描述**: 上傳目前登入使用者的視力檢查紀錄。

**Request Header**:
```json
{
    "Authorization": "Bearer ..."
}
```

**Request Body**:
```json
{
    "corr_l": "0.1",
    "diopter_l": "0.5D",
    "corr_r": "0.5",
    "diopter_r": "0.25D",
    "unco_l": "0.0",
    "unco_r": "0.0",
    "created_at": "2025-06-14T20:07:04.387183"
}
```

**Response**:
- **200 OK**:
```json
{
    "status": "success",
    "message": "視力紀錄上傳成功",
    "data": null
}
```
- **401 Unauthorized** (未提供或無效的 access token):
```json
{
    "status": "error",
    "message": "無效的 access token",
    "data": null
}
```

### GET /api/user/profile
**描述**: 取得目前登入使用者的個人資料。

**Request Header**:
```json
{
    "Authorization": "Bearer ..."
}
```

**Request Body**: 無

**Response**:
- **200 OK**:
```json
{
    "status": "success",
    "message": "成功取得個人資料",
    "data": {
        "username": "testuser",
        "email": "test@example.com",
        "age": 20,
        "gender": "male",
        "job": "student"
    }
}
```
- **401 Unauthorized** (未提供或無效的 access token):
```json
{
    "status": "error",
    "message": "無效的 access token",
    "data": null
}
```

### PUT /api/user/profile
**描述**: 更新目前登入使用者的個人資料。

**Request Header**:
```json
{
    "Authorization": "Bearer ..."
}
```

**Request Body**:
```json
{
    "username": "testuser",
    "email": "test@example.com",
    "age": 20,
    "gender": "male",
    "job": "student"
}
```

**Response**:
- **200 OK**:
```json
{
    "status": "success",
    "message": "個人資料更新成功",
    "data": null
}
```
- **400 Bad Request** (欄位格式錯誤):
```json
{
    "status": "error",
    "message": "欄位格式錯誤，例如 age 為負數",
    "data": null
}
```
- **401 Unauthorized** (未提供或無效的 access token):
```json
{
    "status": "error",
    "message": "無效的 access token",
    "data": null
}
```