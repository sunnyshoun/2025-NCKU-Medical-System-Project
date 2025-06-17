# Vision Tester App

一個用於視力測試和記錄管理的 Flutter 行動應用程式，具備聊天功能和遠程控制特性。

## 📱 主要功能

- **用戶認證**: 基於 JWT token 的安全登入/註冊系統
- **視力記錄**: 查看和搜尋視力測試記錄，支援日期篩選
- **聊天系統**: 即時聊天功能，提供用戶支援
- **遠程控制**: 外部視力測試設備的控制介面
- **多語言支援**: 英文和繁體中文
- **用戶資料管理**: 更新個人資訊和偏好設定
- **設定功能**: 可自訂字體大小和語言偏好
- **離線快取**: 本地數據持久化，儲存用戶偏好設定

## 🏗️ 架構設計

應用程式採用清潔架構模式，關注點分離：

```
lib/
├── configs/           # 配置文件
│   └── app_localizations.dart
├── controllers/       # 業務邏輯 controllers
│   ├── cache_manager.dart
│   ├── chat_controller.dart
│   ├── record_controller.dart
│   ├── registration_controller.dart
│   └── settings_controller.dart
├── models/           # 數據模型
│   ├── cache_models.dart
│   ├── http_models.dart
│   ├── state_models.dart
│   ├── user_models.dart
│   └── wrappers.dart
├── networks/         # API 服務
│   └── spring.dart
├── views/           # UI 組件
│   ├── chat_page.dart
│   ├── home.dart
│   ├── records_page.dart
│   ├── registration_page.dart
│   ├── remote_page.dart
│   ├── settings.dart
│   └── update_profile.dart
└── main.dart        # 應用程式入口點
```

## 🚀 開始使用

### 系統需求

- Flutter SDK (>= 3.7.2)
- Dart SDK
- Android Studio / VS Code
- Android 設備/模擬器 或 iOS 設備/模擬器

### 安裝步驟

1. **複製 repository**
   ```bash
   git clone <repository-url>
   cd tester_app
   ```

2. **安裝相依套件**
   ```bash
   flutter pub get
   ```

3. **配置後端伺服器**
   
   在 `lib/networks/spring.dart` 中更新 API base URL：
   ```dart
   static String BASE_DOMAIN = 'your-server-ip:8080';
   ```

4. **執行應用程式**
   ```bash
   flutter run
   ```

## 🔧 配置設定

### Backend API

應用程式與 Spring Boot 後端伺服器通訊。確保您的後端伺服器正在運行且可存取。API endpoints 包括：

- `POST /api/auth/register` - 用戶註冊
- `POST /api/auth/login` - 用戶登入
- `POST /api/auth/refresh` - Token 刷新
- `POST /api/auth/logout` - 用戶登出
- `GET /api/user/profile` - 取得用戶資料
- `PUT /api/user/profile` - 更新用戶資料
- `GET /api/user/records` - 取得視力記錄
- `POST /api/chat` - 發送聊天訊息
- `DELETE /api/chat` - 清除聊天記錄

### 環境設定

1. 確保您的後端伺服器正在運行
2. 在 `spring.dart` 中更新 `BASE_DOMAIN` 以符合您的伺服器配置
3. 確保 HTTP 請求擁有適當的網路權限

## 📋 應用程式流程

### 入口點
1. 載入快取偏好設定
2. 嘗試刷新 JWT tokens
3. 成功時：取得用戶資料並導航至首頁
4. 失敗時：清除快取並導航至登入頁面

### 認證流程
1. 用戶輸入憑證（email/username + password）
2. 如果帳戶存在：登入並導航至首頁
3. 如果帳戶不存在：導航至註冊頁面
4. 註冊建立新帳戶並自動登入

### 主要功能
- **首頁**: 包含記錄、遠程控制和設定的分頁介面
- **記錄**: 按日期搜尋和查看視力測試記錄
- **遠程**: 視力測試設備的控制介面
- **聊天**: 浮動動作按鈕提供聊天系統存取
- **設定**: 語言、字體大小、資料管理和登出

## 🌍 國際化

應用程式支援多種語言：

- **英文** (`en`)
- **繁體中文** (`zh`)

語言文件在 `lib/configs/app_localizations.dart` 中管理。

## 🎨 UI 組件

- **底部導航**: 記錄、遠程和設定之間的主要導航
- **浮動動作按鈕**: 快速存取聊天功能
- **搜尋介面**: 基於日期的視力記錄篩選
- **表單驗證**: 用戶數據的全面輸入驗證
- **響應式設計**: 適應不同螢幕尺寸的 UI

## 📱 平台支援

- ✅ Android
- ✅ iOS
- ❌ Web（在 .gitignore 中排除）
- ❌ Desktop 平台（在 .gitignore 中排除）

## 🔐 安全特性

- 基於 JWT token 的認證
- 自動 token 刷新
- 安全的 API 通訊
- 輸入驗證和消毒
- Session 管理，token 過期時自動登出

## 📦 相依套件

- **flutter**: UI framework
- **http**: API 通訊的 HTTP client
- **path_provider**: 快取用的本地檔案系統存取
- **cupertino_icons**: iOS 風格圖示

## 🧪 測試

執行測試：
```bash
flutter test
```

## 🚀 Production 建置

### Android
```bash
flutter build apk --release
```

### iOS
```bash
flutter build ios --release
```

---

**注意**: 在使用應用程式之前，請確保您的後端伺服器已正確配置並正在運行。