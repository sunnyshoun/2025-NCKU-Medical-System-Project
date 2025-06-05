# Arduino 組件

## 概述
本組件運行於 Arduino Uno，負責控制視力檢測機器人的馬達，根據 Raspberry Pi 的指令調整設備位置。通過序列通訊（SoftwareSerial）接收移動指令（方向和距離），執行馬達控制並回傳狀態。

## 硬體需求
- Arduino Uno
- 步進馬達（兩組，控制左右移動）
- 馬達驅動板（支援 4 線步進馬達）
- 序列連線（RX: Pin 6, TX: Pin 7）

## 軟體依賴
- Arduino IDE
- 必要庫：
  - `AccelStepper`：步進馬達控制
  - `SoftwareSerial`：序列通訊

## 檔案結構
```
Arduino/
├── sketches/
│   ├── motorController.ino # 馬達控制程式
├── config/
│   ├── motor_config.json   # 馬達配置（例如腳位、速度）
├── README.md               # 本文件
```

## 設置與運行
1. **安裝 Arduino IDE**：
   - 下載並安裝 Arduino IDE。
2. **安裝依賴**：
   - 通過 Arduino IDE 的 Library Manager 安裝 `AccelStepper` 和 `SoftwareSerial` 庫。
3. **硬體連接**：
   - 將步進馬達連接到指定腳位（左：2,3,4,5；右：8,9,10,11）。
   - 連接到 Rpi 的序列埠（RX: Pin 6, TX: Pin 7）。
4. **燒錄程式碼**：
   - 開啟 `sketches/motorController.ino`，燒錄至 Arduino：
     ```plaintext
     Upload via Arduino IDE
     ```

## 序列通訊協議
- **輸入格式**：`m<direction>,<distance>\n`
  - `direction`：`0`（反向）或 `1`（正向）
  - `distance`：移動距離（毫米）
  - 示例：`m1,100\n`（正向移動 100 毫米）
- **輸出**：
  - `ok`：指令有效，開始移動
  - `done`：移動完成
  - `error`：指令無效

## 注意事項
- 確保序列埠速率設為 9600，與 Rpi 通訊一致。
- 檢查馬達腳位和驅動板是否正確連接。