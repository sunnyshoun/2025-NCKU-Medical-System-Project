# EyeDwell 機器人通訊協議（更新版）

## 概述

機器人和手機之間透過 BLE 進行通訊，使用兩個特徵值通道：
- **COMMAND_CHAR_UUID**: 手機 → 機器人的指令通道
- **DATA_CHAR_UUID**: 機器人 → 手機的數據通道

## BLE 服務資訊

- **服務名稱**: "EyeDwell"  
- **服務 UUID**: "12345678-abcd-1234-5678-123456789abc"
- **指令特徵 UUID**: "12345678-abcd-1234-5678-123456789ab1" (COMMAND_CHAR_UUID)
- **數據特徵 UUID**: "12345678-abcd-1234-5678-123456789ab2" (DATA_CHAR_UUID)

## 通訊協議

### 手機 → 機器人 (COMMAND_CHAR_UUID)

#### 1. 連線指令
```json
{
  "type": "connect"
}
```

**機器人行為**:
- 停止板載按鈕操控
- 切換到手機控制模式  
- OLED 顯示手機圖示（使用 `draw_phone_icon()`）

#### 2. 斷線指令
```json
{
  "type": "disconnect"
}
```

**機器人行為**:
- 立刻回到板載按鈕操作的主選單
- 停止當前測試（如果有的話）
- OLED 回到主選單顯示

#### 3. 開始測試
```json
{
  "type": "start_test"
}
```

**機器人行為**:
- 開始測試流程（使用預設語言）
- 不播放任何音檔
- OLED 清空或顯示測試狀態

#### 4. 方向回應
```json
{
  "type": "direction_response",
  "direction": 2
}
```

**參數說明**:
- `direction`: 開口方向 (0=右, 1=上, 2=左, 3=下)

#### 5. 語音識別回應
```json
{
  "type": "stt_response",
  "text": "上面"
}
```

**參數說明**:
- `text`: 語音識別結果文字

### 機器人 → 手機 (DATA_CHAR_UUID)

#### 1. 準備接收輸入
```json
{
  "type": "ready_for_input"
}
```

當機器人移動到測試位置並準備好接收使用者輸入時發送。

**手機行為**:
- 啟用方向選擇UI
- 或啟用語音輸入功能
- 顯示測試圖案或相關提示

#### 2. 測試完成
```json
{
  "type": "test_complete",
  "score": 1.2
}
```

**參數說明**:
- `score`: 視力分數

**機器人行為**:
- 發送測試結果到手機
- OLED 不顯示測試結果
- OLED 直接回到手機圖案（使用 `draw_phone_icon()`）
- 準備進行下一次測試

## 手機端實現範例

### 1. BLE 連線管理
```dart
class BLEManager {
  // 掃描並連線
  Future<void> scanAndConnect(String deviceName) async {
    // 掃描設備邏輯
    await connect();
    
    // 連線成功後發送連線指令
    await sendCommand({"type": "connect"});
  }
  
  // 發送指令到機器人
  Future<void> sendCommand(Map<String, dynamic> command) async {
    String jsonString = jsonEncode(command);
    await commandCharacteristic.write(utf8.encode(jsonString));
  }
  
  // 監聽來自機器人的數據
  void listenToData() {
    dataCharacteristic.value.listen((data) {
      String jsonString = utf8.decode(data);
      Map<String, dynamic> message = jsonDecode(jsonString);
      handleIncomingMessage(message);
    });
  }
  
  // 處理接收到的訊息
  void handleIncomingMessage(Map<String, dynamic> message) {
    switch (message['type']) {
      case 'ready_for_input':
        onReadyForInput?.call();
        break;
      case 'test_complete':
        onTestComplete?.call(message['score']);
        break;
    }
  }
  
  // 斷線
  Future<void> disconnect() async {
    await sendCommand({"type": "disconnect"});
    await bluetoothConnection.disconnect();
  }
}
```

### 2. 測試控制流程
```dart
class TestController {
  final BLEManager bleManager;
  
  TestController(this.bleManager) {
    bleManager.onReadyForInput = onReadyForInput;
    bleManager.onTestComplete = onTestComplete;
  }
  
  // 開始測試
  Future<void> startTest() async {
    await bleManager.sendCommand({"type": "start_test"});
    updateUI(TestState.testing);
  }
  
  // 當機器人準備接收輸入時
  void onReadyForInput() {
    updateUI(TestState.waitingInput);
    enableDirectionSelector();
  }
  
  // 發送方向選擇
  Future<void> selectDirection(int direction) async {
    await bleManager.sendCommand({
      "type": "direction_response", 
      "direction": direction
    });
    
    disableDirectionSelector();
    updateUI(TestState.testing);
  }
  
  // 發送語音識別結果
  Future<void> sendSTTResponse(String text) async {
    await bleManager.sendCommand({
      "type": "stt_response",
      "text": text
    });
  }
  
  // 測試完成回調
  void onTestComplete(double score) {
    showTestResult(score);
    updateUI(TestState.showingResult);
  }
}
```

### 3. UI 狀態管理
```dart
enum TestState {
  disconnected,    // 未連線
  connected,       // 已連線，等待開始測試
  testing,         // 測試進行中
  waitingInput,    // 等待使用者輸入
  showingResult    // 顯示測試結果
}

class TestStateManager {
  TestState currentState = TestState.disconnected;
  
  void updateState(TestState newState) {
    currentState = newState;
    updateUI();
  }
  
  void updateUI() {
    switch (currentState) {
      case TestState.disconnected:
        showScanInterface();
        break;
      case TestState.connected:
        showTestStartInterface();
        break;
      case TestState.testing:
        showWaitingInterface();
        break;
      case TestState.waitingInput:
        showInputInterface(); // 方向選擇或語音輸入
        break;
      case TestState.showingResult:
        showResultInterface();
        break;
    }
  }
}
```

## 測試流程圖

```
手機掃描並連線 → 發送 connect 指令 → 機器人切換模式，OLED顯示手機圖示
   ↓
手機發送 start_test
   ↓  
機器人開始測試流程（使用預設語言，不播放音檔）
   ↓
[重複] 機器人移動定位 → 發送 ready_for_input → 手機顯示輸入UI → 
手機發送 direction_response 或 stt_response
   ↓
測試完成 → 機器人發送 test_complete → OLED直接回到手機圖案
   ↓
手機顯示結果，可選擇重新測試或發送 disconnect 指令
```

## 機器人端圖案繪製

所有圖案都由 `draw.py` 繪製，由 OLED 控制模組更新螢幕：

### 手機連線狀態
```python
from data.draw import draw_phone_connected_icon

# 顯示手機連線圖案
img = draw_phone_connected_icon()
oled.clear()
oled.set_img(img)
oled.display()
```

### 測試圖像（按鈕模式）
```python
from data.draw import draw_circle_with_right_opening, paste_square_image_centered

# 繪製視力測試圖像
img = draw_circle_with_right_opening(thickness=thickness)
result = paste_square_image_centered(img.rotate(direction * 90))
oled.set_img(result)
oled.display()
```

### 測試結果（按鈕模式）
```python
from PIL import Image, ImageDraw, ImageFont

# 繪製結果顯示
image = Image.new('1', (128, 64))
draw = ImageDraw.Draw(image)
font = ImageFont.truetype(**RESULT_FONT)

draw.rectangle((0, 0, 128, 64), outline=0, fill=0)
draw.text((0, 0), RESULT_STRS[lang_code], font=font, fill=255)
draw.text((5, 22), f'{score:0.1f}', font=font, fill=255)

oled.set_img(image)
oled.display()
```

## 錯誤處理

### 超時處理
- 等待手機輸入回應：30秒超時，超時後重送
- BLE 連線檢測：每2秒檢查一次

### 異常狀況
- 手機斷線：立即停止測試，回到按鈕模式，OLED回到主選單
- 測試失敗：發送錯誤訊息到手機
- 機器人硬體故障：發送錯誤狀態到手機
- JSON 解析錯誤：忽略無效訊息，記錄日誌

### 狀態恢復
- 測試結束後，OLED自動回到手機圖案
- 斷線後，OLED自動回到主選單
- 重新連線後，OLED自動顯示手機圖案

## 協議特點

1. **明確的連線管理** - 使用 connect/disconnect 指令明確控制連線狀態
2. **雙重輸入支持** - 支援觸控方向選擇和語音識別兩種輸入方式
3. **簡化的消息格式** - 使用統一的 JSON 格式，易於解析和調試
4. **清晰的狀態轉換** - 手機端可明確知道當前測試狀態
5. **統一的圖案繪製** - 所有圖案由 draw.py 統一處理
6. **自動狀態恢復** - 測試結束或斷線後自動回到適當狀態

這個更新版本的協議與你的實際藍牙接口完全一致，提供了清晰的通訊架構和實現指南。