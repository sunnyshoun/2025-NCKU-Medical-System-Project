import logging
import json
import asyncio
from typing import Optional
from ble_communication.ble_server import BLEServer


class PhoneHandler:
    """處理與手機的簡化通訊邏輯"""
    
    def __init__(self, robot_controller):
        self.logger = logging.getLogger("PhoneHandler")
        self.robot_controller = robot_controller
        
        # 簡化的 BLE 服務器
        self.ble_server: Optional[BLEServer] = None
        self.connection_status = False
        
    async def start(self):
        """啟動手機處理器"""
        self.logger.info("啟動手機處理器...")
        
        # 創建並啟動簡化的 BLE 服務器
        self.ble_server = BLEServer("EyeDwell_Robot")
        
        # 設置回調函數
        self.ble_server.on_control_command = self._handle_control_command
        self.ble_server.on_connection_changed = self._handle_connection_changed
        
        await self.ble_server.start_server()
        self.logger.info("BLE 服務器啟動成功")
    
    async def stop(self):
        """停止手機處理器"""
        self.logger.info("停止手機處理器...")
        
        if self.ble_server:
            await self.ble_server.stop_server()
            self.ble_server = None
        
        self.connection_status = False
        self.logger.info("手機處理器已停止")
    
    def is_connected(self) -> bool:
        """檢查手機是否已連線"""
        return self.connection_status
    
    async def _handle_connection_changed(self, connected: bool):
        connected = False # for test
        """處理連線狀態變化"""
        self.connection_status = connected
        self.logger.info(f"手機連線狀態變更: {connected}")
        
        if connected:
            # 連線後切換到手機模式
            await self.robot_controller.switch_to_phone_mode()
            self.logger.info("已切換到手機控制模式，OLED 顯示手機圖示")
        else:
            # 斷線後回到板載按鈕操作的主選單
            await self.robot_controller.switch_to_button_mode()
            # 停止當前測試（如果有的話）
            if self.robot_controller.test_coordinator:
                await self.robot_controller.test_coordinator.stop_test()
            self.logger.info("已切換回板載按鈕操作模式，回到主選單")
    
    async def _handle_control_command(self, command: str):
        """處理來自手機的控制命令"""
        try:
            cmd_data = json.loads(command)
            cmd_type = cmd_data.get("type")
            
            if cmd_type == "start_test":
                # 通訊時機點2: 手機發送開始測試
                self.logger.info("收到開始測試命令")
                
                # 開始測試流程（使用預設語言）
                success = await self.robot_controller.start_phone_test()
                
                if success:
                    # OLED 清空或顯示測試狀態
                    self.robot_controller.oled.clear()
                    await self._send_response("test_started", {"message": "測試已開始"})
                    self.logger.info("測試已開始，OLED已清空")
                else:
                    await self._send_response("test_failed", {"error": "無法開始測試"})
                    self.logger.error("無法開始測試")
            
            elif cmd_type == "direction_response":
                # 通訊時機點4: 接收手機的方向選擇回應
                direction = cmd_data.get("direction")
                self.logger.info(f"收到方向回應: {direction}")
                
                # 驗證方向值
                if direction not in [0, 1, 2, 3]:
                    self.logger.warning(f"無效的方向值: {direction}")
                    return
                
                # 將回應傳遞給測試協調器
                if self.robot_controller.test_coordinator:
                    self.robot_controller.test_coordinator.set_phone_response(direction)
                else:
                    self.logger.warning("測試協調器未初始化")
                
            else:
                self.logger.warning(f"未知命令類型: {cmd_type}")
                
        except json.JSONDecodeError as e:
            self.logger.error(f"無法解析控制命令: {command}, 錯誤: {e}")
        except Exception as e:
            self.logger.error(f"處理控制命令失敗: {e}")
    
    async def notify_ready_for_direction(self, test_info: dict = None) -> bool:
        """通知手機等待使用者輸入方向（通訊時機點3）"""
        if not self.is_connected():
            self.logger.warning("手機未連線，無法發送準備選擇方向通知")
            return False
        
        # 設定預設測試資訊
        if test_info is None:
            test_info = {
                "degree": 0.5,
                "thickness": 4
            }
        
        message = {
            "message": "機器人已定位完成，請選擇開口方向",
            "test_info": test_info
        }
        
        success = await self._send_response("ready_for_direction", message)
        if success:
            self.logger.info("已通知手機準備選擇方向")
        return success
    
    async def send_test_result(self, vision_score: float) -> bool:
        """發送測試結束和結果（通訊時機點5）"""
        if not self.is_connected():
            self.logger.warning("手機未連線，無法發送測試結果")
            return False
        
        message = {
            "vision_score": vision_score
        }
        
        success = await self._send_response("test_complete", message)
        if success:
            self.logger.info(f"已發送測試結果: {vision_score}")
            
            # 測試結束後，OLED回到手機圖案
            await asyncio.sleep(0.1)  # 稍等片刻確保消息發送完成
            self.robot_controller.show_phone_connected_status()
            
        return success
    
    async def _send_response(self, response_type: str, data: dict) -> bool:
        """發送回應到手機"""
        try:
            if not self.ble_server:
                self.logger.error("BLE 服務器未初始化")
                return False
            
            response = {
                "type": response_type,
                "data": data
            }
            
            json_data = json.dumps(response, ensure_ascii=False)
            self.logger.debug(f"發送回應: {json_data}")
            
            return await self.ble_server.send_data(json_data.encode('utf-8'))
            
        except Exception as e:
            self.logger.error(f"發送回應失敗: {e}")
            return False
    
    async def send_status_update(self, status: str, details: dict = None) -> bool:
        """發送狀態更新到手機（額外功能）"""
        if not self.is_connected():
            self.logger.warning("手機未連線，無法發送狀態更新")
            return False
        
        try:
            return await self.ble_server.send_status_update(status, details)
        except Exception as e:
            self.logger.error(f"發送狀態更新失敗: {e}")
            return False
    
    def get_connection_info(self) -> dict:
        """獲取連線資訊"""
        return {
            "connected": self.connection_status,
            "client_address": self.ble_server.client_address if self.ble_server else "",
            "device_name": self.ble_server.device_name if self.ble_server else "EyeDwell_Robot"
        }