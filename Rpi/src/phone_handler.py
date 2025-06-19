"""
手機處理器 - 使用簡化的 BLE 服務器
"""

import logging
import json
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
        """處理連線狀態變化"""
        self.connection_status = connected
        self.logger.info(f"手機連線狀態變更: {connected}")
        
        if connected:
            # 連線後切換到手機模式
            self.robot_controller.switch_to_phone_mode()
            self.logger.info("已切換到手機控制模式，OLED 顯示手機圖示")
        else:
            # 斷線後回到按鈕模式
            self.robot_controller.switch_to_button_mode()
            self.logger.info("已切換回板載按鈕操作模式")
    
    async def _handle_control_command(self, command: str):
        """處理來自手機的控制命令"""
        try:
            cmd_data = json.loads(command)
            cmd_type = cmd_data.get("type")
            
            if cmd_type == "start_test":
                # 通訊時機點1: 手機發送開始測試（不需要語言參數）
                self.logger.info("收到開始測試命令")
                
                # 開始測試
                success = await self.robot_controller.start_phone_test()
                
                if success:
                    await self._send_response("test_started", {"message": "測試已開始"})
                else:
                    await self._send_response("test_failed", {"error": "無法開始測試"})
            
            elif cmd_type == "direction_response":
                # 通訊時機點3: 接收手機的方向選擇回應
                direction = cmd_data.get("direction")
                self.logger.info(f"收到方向回應: {direction}")
                
                # 將回應傳遞給測試協調器
                if self.robot_controller.test_coordinator:
                    self.robot_controller.test_coordinator.set_phone_response(direction)
                
            else:
                self.logger.warning(f"未知命令類型: {cmd_type}")
                
        except json.JSONDecodeError as e:
            self.logger.error(f"無法解析控制命令: {command}, 錯誤: {e}")
        except Exception as e:
            self.logger.error(f"處理控制命令失敗: {e}")
    
    async def notify_ready_for_direction(self) -> bool:
        """通訊時機點2: 通知手機等待使用者輸入方向"""
        if not self.is_connected():
            return False
        
        message = {
            "type": "ready_for_direction",
            "message": "機器人已定位完成，請選擇開口方向"
        }
        
        success = await self._send_response("ready_for_direction", message)
        if success:
            self.logger.info("已通知手機準備選擇方向")
        return success
    
    async def send_test_result(self, vision_score: float) -> bool:
        """通訊時機點4: 發送測試結束和結果"""
        if not self.is_connected():
            return False
        
        message = {
            "type": "test_complete",
            "vision_score": vision_score,
            "message": f"視力測試完成，結果: {vision_score}"
        }
        
        success = await self._send_response("test_complete", message)
        if success:
            self.logger.info(f"已發送測試結果: {vision_score}")
            
            # 測試結束後，OLED回到手機圖案
            self.robot_controller.show_phone_connected_status()
            
        return success
    
    async def _send_response(self, response_type: str, data: dict) -> bool:
        """發送回應到手機"""
        try:
            response = {
                "type": response_type,
                "data": data
            }
            
            json_data = json.dumps(response, ensure_ascii=False)
            return await self.ble_server.send_data(json_data.encode('utf-8'))
            
        except Exception as e:
            self.logger.error(f"發送回應失敗: {e}")
            return False