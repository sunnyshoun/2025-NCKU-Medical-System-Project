# REST API 文件

## 概述

本文件描述了視力檢查系統的 REST API，提供使用者身份驗證、個人資料管理、視力記錄管理以及聊天機器人功能。

### 基本資訊

- **Base URL**: `/api`
- **Content-Type**: `application/json`
- **Authentication**: Bearer Token (JWT)
- **Date Format**: ISO 8601 (`YYYY-MM-DDTHH:mm:ss.ssssss`)

### 通用響應格式

所有 API 響應均遵循以下格式：

```json
{
    "status": "success|error",
    "message": "描述訊息",
    "data": {} // 回傳資料或 null
}
```

### HTTP 狀態碼

- `200 OK` - 請求成功
- `201 Created` - 資源創建成功
- `400 Bad Request` - 請求格式錯誤
- `401 Unauthorized` - 未授權或 Token 無效
- `404 Not Found` - 資源不存在
- `409 Conflict` - 資源衝突

---

## 身份驗證 API

### 使用者註冊

註冊新的使用者帳戶。

**Endpoint**: `POST /api/auth/register`

**Request Body**:
```json
{
    "username": "string",      // 必填，使用者名稱
    "password": "string",      // 必填，密碼
    "email": "string"          // 必填，電子郵件
}
```

**Response**:

- **201 Created** - 註冊成功
```json
{
    "status": "success",
    "message": "註冊成功",
    "data": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
}
```

- **400 Bad Request** - 資料格式錯誤
```json
{
    "status": "error",
    "message": "資料格式錯誤",
    "data": null
}
```

- **409 Conflict** - 使用者名稱或 Email 已存在
```json
{
    "status": "error",
    "message": "使用者名稱或 email 已存在",
    "data": null
}
```

### 使用者登入

使用帳號密碼進行登入驗證。

**Endpoint**: `POST /api/auth/login`

**Request Body** (可使用 username 或 email):
```json
{
    "username": "string",      // 使用者名稱 (與 email 二選一)
    "email": "string",         // 電子郵件 (與 username 二選一)
    "password": "string"       // 必填，密碼
}
```

**Response**:

- **200 OK** - 登入成功
```json
{
    "status": "success",
    "message": "登入成功",
    "data": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
}
```

- **400 Bad Request** - 缺少必要欄位
- **401 Unauthorized** - 密碼錯誤
- **404 Not Found** - 使用者不存在

### 使用者登出

登出並註銷 Refresh Token。

**Endpoint**: `POST /api/auth/logout`

**Headers**:
```
Authorization: Bearer <refresh_token>
```

**Response**:

- **200 OK** - 登出成功
```json
{
    "status": "success",
    "message": "登出成功",
    "data": null
}
```

- **401 Unauthorized** - Token 無效或已過期

### 更新 Access Token

使用 Refresh Token 更新 Access Token。

**Endpoint**: `POST /api/auth/refresh`

**Headers**:
```
Authorization: Bearer <refresh_token>
```

**Response**:

- **200 OK** - Token 更新成功
```json
{
    "status": "success",
    "message": "Token 更新成功",
    "data": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
}
```

- **401 Unauthorized** - Refresh Token 無效或已過期

---

## 使用者管理 API

> **注意**: 以下 API 均需要在 Header 中提供有效的 Access Token
>
> **Headers**:
> ```
> Authorization: Bearer <access_token>
> ```

### 取得個人資料

取得目前登入使用者的個人資料。

**Endpoint**: `GET /api/user/profile`

**Response**:

- **200 OK** - 成功取得個人資料
```json
{
    "status": "success",
    "message": "成功取得個人資料",
    "data": {
        "username": "testuser",
        "email": "test@example.com",
        "age": 20,
        "gender": "male",          // male | female | other
        "job": "student"
    }
}
```

- **401 Unauthorized** - Access Token 無效

### 更新個人資料

更新目前登入使用者的個人資料。

**Endpoint**: `PUT /api/user/profile`

**Request Body**:
```json
{
    "username": "string",      // 選填，使用者名稱
    "email": "string",         // 選填，電子郵件
    "age": 20,                 // 選填，年齡 (必須 > 0)
    "gender": "string",        // 選填，性別 (male|female|other)
    "job": "string"            // 選填，職業
}
```

**Response**:

- **200 OK** - 個人資料更新成功
```json
{
    "status": "success",
    "message": "個人資料更新成功",
    "data": null
}
```

- **400 Bad Request** - 欄位格式錯誤
- **401 Unauthorized** - Access Token 無效

---

## 視力記錄 API

> **注意**: 以下 API 均需要在 Header 中提供有效的 Access Token
>
> **Headers**:
> ```
> Authorization: Bearer <access_token>
> ```

### 取得視力記錄

取得目前登入使用者的所有視力檢查記錄。

**Endpoint**: `GET /api/user/records`

**Response**:

- **200 OK** - 成功取得視力記錄
```json
{
    "status": "success",
    "message": "成功取得視力記錄",
    "data": [
        {
            "record_id": "6108738f-cfd7-4e75-8a47-ea2688e89ce3",
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "corr_l": "1.0",           // 左眼矯正視力
            "corr_r": "0.9",           // 右眼矯正視力
            "diopter_l": "1.5D",       // 左眼度數
            "diopter_r": "1.5D",       // 右眼度數
            "unco_l": "0.5",           // 左眼裸視視力
            "unco_r": "0.4",           // 右眼裸視視力
            "created_at": "2025-06-14T11:31:08.782619",
            "updated_at": "2025-06-14T11:31:08.782634"
        }
    ]
}
```

- **401 Unauthorized** - Access Token 無效

### 新增視力記錄

新增視力檢查記錄至目前登入使用者。

**Endpoint**: `POST /api/user/records`

**Request Body**:
```json
{
    "corr_l": "string",        // 必填，左眼矯正視力
    "corr_r": "string",        // 必填，右眼矯正視力
    "diopter_l": "string",     // 必填，左眼度數
    "diopter_r": "string",     // 必填，右眼度數
    "unco_l": "string",        // 必填，左眼裸視視力
    "unco_r": "string",        // 必填，右眼裸視視力
    "created_at": "string"     // 選填，記錄時間 (ISO 8601 格式)
}
```

**Response**:

- **200 OK** - 視力記錄上傳成功
```json
{
    "status": "success",
    "message": "視力記錄上傳成功",
    "data": null
}
```

- **400 Bad Request** - 資料格式錯誤
- **401 Unauthorized** - Access Token 無效

---

## 聊天機器人 API

> **注意**: 以下 API 均需要在 Header 中提供有效的 Access Token
>
> **Headers**:
> ```
> Authorization: Bearer <access_token>
> ```

### 發送訊息

向聊天機器人發送訊息並取得回覆。

**Endpoint**: `POST /api/chat`

**Request Body**:
```json
{
    "content": "string"        // 必填，訊息內容 (最多 300 字元)
}
```

**Response**:

- **200 OK** - 成功取得回覆
```json
{
    "status": "success",
    "message": "",
    "data": {
        "content": "機器人回覆內容...",
        "tags": [
            "標籤1",
            "標籤2"
        ],
        "source": [
            "https://example.com/source1",
            "https://example.com/source2"
        ]
    }
}
```

- **400 Bad Request** - 訊息內容格式錯誤或超過字元限制
- **401 Unauthorized** - Access Token 無效

### 結束對話

結束對話並清除使用者的對話上下文。

**Endpoint**: `DELETE /api/chat`

**Response**:

- **200 OK** - 對話結束成功
```json
{
    "status": "success",
    "message": "",
    "data": null
}
```

- **401 Unauthorized** - Access Token 無效
- **404 Not Found** - 對話不存在
```json
{
    "status": "CONVERSATION_NOT_FOUND",
    "message": "對話不存在",
    "data": null
}
```

---

## 錯誤處理

### 常見錯誤響應

**401 Unauthorized** - Token 相關錯誤
```json
{
    "status": "error",
    "message": "無效的 access token",
    "data": null
}
```

**400 Bad Request** - 請求格式錯誤
```json
{
    "status": "error",
    "message": "缺少必要欄位",
    "data": null
}
```

**404 Not Found** - 資源不存在
```json
{
    "status": "error",
    "message": "使用者不存在",
    "data": null
}
```

### 特殊狀態碼

某些 API 可能回傳特殊的 status 值：
- `CONVERSATION_NOT_FOUND` - 聊天對話不存在

---

## 驗證規則

### Token 管理

- **Access Token**: 用於 API 存取驗證，有效期為 15 分鐘
- **Refresh Token**: 用於更新 Access Token，有效期為 30 日
- 當 Access Token 過期時，使用 Refresh Token 呼叫 `/api/auth/refresh` 取得新的 Token 組合

### 資料驗證

- **Age**: 必須在 1 ~ 120 之間
- **Chat Content**: 最多 300 字元
- **Email**: 必須符合標準 Email 格式

### 安全注意事項

- 所有需要身份驗證的 API 都必須在 Header 中提供 `Authorization: Bearer <token>`
- Token 過期時會回傳 401 狀態碼，前端應自動導向登入頁面或嘗試更新 Token
- 密碼等敏感資訊不會在 Response 中回傳