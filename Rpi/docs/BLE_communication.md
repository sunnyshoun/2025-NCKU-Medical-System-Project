# EyeDwell 機器人通訊協議（最終簡化版）

## 概述

機器人和手機之間只在4個關鍵時機點進行通訊，完全移除音檔傳輸，保持協議極簡高效。

## BLE 服務資訊

- **服務名稱**: "EyeDwell_Robot"  
- **服務 UUID**: "12345678-abcd-1234-5678-123456789abc"

## 4個關鍵通訊時機點

### 1. 連線狀態變化

#### 連線後（自動處理）
**機器人行為**:
- 停止板載按鈕操控
- 切換到手機控制模式  
- OLED 顯示手機圖示（使用 `draw_phone_icon()`）

#### 斷線後（自動處理）
**機器人行為**:
- 立刻回到板載按鈕操作的主選單
- 停止當前測試（如果有的話）
- OLED 回到主選單顯示

### 2. 開始測試（手機 → 機器人）

```json
{
  "type": "start_test"
}
```

**機器人回應**:
```json
{
  "type": "test_started", 
  "data": {
    "message": "測試已開始"
  }
}
```

**機器人行為**:
- 開始測試流程（使用預設語言）
- 不播放任何音檔
- OLED 清空或顯示測試狀態

### 3. 等待使用者輸入方向（機器人 → 手機）

當機器人移動到測試位置並準備好時：

```json
{
  "type": "ready_for_direction",
  "data": {
    "message": "機器人已定位完成，請選擇開口方向",
    "test_info": {
      "degree": 0.5,
      "thickness": 4
    }
  }
}
```

**手機回應（方向選擇）**:
```json
{
  "type": "direction_response",
  "direction": 0  // 0=右, 1=上, 2=左, 3=下
}
```

### 4. 測試結束（機器人 → 手機）

```json
{
  "type": "test_complete",
  "data": {
    "vision_score": 0.8
  }
}
```

**機器人行為**:
- 發送測試結果到手機
- OLED 不顯示測試結果
- OLED 直接回到手機圖案（使用 `draw_phone_icon()`）
- 準備進行下一次測試

## 手機端需實現的功能

### 1. BLE 連線管理
```dart
// 掃描並連線
await bleManager.scanAndConnect("EyeDwell_Robot");

// 監聽連線狀態
bleManager.onConnectionChanged = (connected) {
  if (connected) {
    // 顯示連線成功，準備開始測試
    showTestInterface();
  } else {
    // 顯示斷線，回到掃描畫面
    showScanInterface();
  }
};
```

### 2. 測試控制流程
```dart
// 開始測試
void startTest() {
  bleManager.sendCommand({
    "type": "start_test"
  });
  
  // 顯示等待狀態
  showWaitingForRobot();
}

// 監聽準備選擇方向的訊號
bleManager.onReadyForDirection = (data) {
  // 啟用方向選擇UI
  enableDirectionSelector();
  showDirectionSelector();
};

// 發送方向選擇
void selectDirection(int direction) {
  bleManager.sendCommand({
    "type": "direction_response", 
    "direction": direction
  });
  
  // 禁用UI，等待下一次輸入
  disableDirectionSelector();
  showWaitingForNextRound();
}

// 監聽測試結果
bleManager.onTestComplete = (result) {
  showTestResult(result.visionScore);
  // 提供重新測試選項
  showRetestOption();
};
```

### 3. UI 狀態管理
```dart
enum TestState {
  disconnected,    // 未連線
  connected,       // 已連線，等待開始測試
  testing,         // 測試進行中
  waitingInput,    // 等待使用者輸入方向
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
        showDirectionSelector();
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
手機連線 → 機器人切換模式，OLED顯示手機圖示
   ↓
手機發送開始測試
   ↓  
機器人開始測試流程（使用預設語言，不播放音檔）
   ↓
[重複] 機器人移動定位 → 通知手機準備輸入 → 手機顯示方向選擇UI → 手機回應方向
   ↓
測試完成 → 機器人發送結果到手機 → OLED直接回到手機圖案（不顯示結果）
   ↓
手機顯示結果，可選擇重新測試或斷線
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
- 等待手機方向回應：30秒超時
- BLE 連線檢測：每2秒檢查一次

### 異常狀況
- 手機斷線：立即停止測試，回到按鈕模式，OLED回到主選單
- 測試失敗：發送錯誤訊息到手機
- 機器人硬體故障：發送錯誤狀態到手機

### 狀態恢復
- 測試結束後，OLED自動回到手機圖案
- 斷線後，OLED自動回到主選單
- 重新連線後，OLED自動顯示手機圖案

## 主要簡化優勢

1. **極簡通訊** - 只有4個通訊時機點
2. **無音檔傳輸** - 完全移除音檔處理複雜度
3. **清晰的UI狀態** - 手機端可明確知道當前狀態
4. **統一的圖案繪製** - 所有圖案由 draw.py 統一處理
5. **自動狀態恢復** - 測試結束或斷線後自動回到適當狀態

這個最終簡化版本將通訊協議精簡到最核心的功能，大幅提升了系統的穩定性和可維護性。