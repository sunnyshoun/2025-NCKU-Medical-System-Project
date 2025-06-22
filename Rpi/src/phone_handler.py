import json
import logging
from typing import Optional, Dict
from ble_communication.ble_server import BLEServer

class PhoneHandler:
    """處理與手機的簡化通訊邏輯"""
    
    def __init__(self, robot_controller):
        self.logger = logging.getLogger("PhoneHandler")
        self.robot_controller = robot_controller
        self.ble_server: Optional[BLEServer] = None
        self.connection_status = False

    async def start(self):
        """啟動手機處理器"""
        self.logger.info("啟動手機處理器...")
        self.ble_server = BLEServer("EyeDwell")
        self.ble_server.on_command_received = self._handle_command
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

    async def _handle_command(self, command: str):
        """處理來自手機的命令"""
        try:
            cmd_data = json.loads(command)
            cmd_type = cmd_data.get("type")
            
            if cmd_type == "connect":
                self.logger.info("收到 connect 命令")
                # 切換到手機模式
                await self.robot_controller.switch_to_phone_mode()
                self.logger.info("已切換到手機控制模式")
            
            elif cmd_type == "disconnect":
                self.logger.info("收到 disconnect 命令")
                # 回到主畫面（按鈕模式）
                await self.robot_controller.switch_to_button_mode()
                # 停止當前測試（如果有的話）
                if self.robot_controller.test_coordinator:
                    self.robot_controller.test_coordinator.stop_test()
                self.logger.info("已切換回板載按鈕操作模式")
            
            elif cmd_type == "start_test":
                self.logger.info("收到開始測試命令")
                success = self.robot_controller.start_phone_test()
                if success:
                    self.robot_controller.oled.clear()
                    self.logger.info("測試已開始，OLED已清空")
                else:
                    self.logger.error("無法開始測試")
            
            elif cmd_type == "direction_response":
                direction = cmd_data.get("direction")
                self.logger.info(f"收到方向回應: {direction}")
                if direction in [0, 1, 2, 3]:
                    if self.robot_controller.test_coordinator:
                        self.robot_controller.test_coordinator.set_phone_response(direction)
                else:
                    self.logger.warning(f"無效的方向值: {direction}")
            
            elif cmd_type == "stt_response":
                text = cmd_data.get("text", "").strip()
                self.logger.info(f"收到STT回應: {text}")
                direction = self._text_to_direction(text)
                if direction is not None:
                    if self.robot_controller.test_coordinator:
                        self.robot_controller.test_coordinator.set_phone_response(direction)
                        self.logger.info(f"STT轉換為方向: {direction}")
                else:
                    self.logger.warning(f"無法識別的方向文字: {text}")
            
            else:
                self.logger.warning(f"未知命令類型: {cmd_type}")
                
        except json.JSONDecodeError as e:
            self.logger.error(f"無法解析命令: {command}, 錯誤: {e}")
        except Exception as e:
            self.logger.error(f"處理命令失敗: {e}")

    def _text_to_direction(self, text: str) -> Optional[int]:
        """將文字轉換為方向代碼"""
        direction_map = {
            "うえ": 1, "上": 1, "した": 3, "下": 3, "左": 2, "右": 0, "みぎ": 0,
            "up": 1, "down": 3, "left": 2, "right": 0,
            "上": 1, "上面": 1, "下": 3, "下面": 3, "左": 2, "左邊": 2, "右": 0, "右邊": 0, "yo": 0,
            "左": 2, "左邊": 2, "左側": 2,
            "下": 3, "下面": 3, "下方": 3,
            "t-ing* p-ing*": 1, "t-ing* k-uan*": 1, "e* b-in*": 3, "e* kh-a*": 3,
            "t-o* p-ing*": 2, "t-o* tsh-iu* p-ing*": 2, "ts-iann* tsh-iu* p-ing*": 0, "ts-iann* p-ing*": 0,
            "0": 0, "1": 1, "2": 2, "3": 3,
        }
        text_lower = text.lower()
        return direction_map.get(text_lower)

    async def notify_ready_for_input(self):
        message = {"type": "ready_for_input"}
        await self._send_message(message)

    async def send_test_result(self, vision_score: float):
        """發送測試結果"""
        message = {
            "type": "test_complete",
            "score": str(vision_score)
        }
        await self._send_message(message)
        await self.robot_controller.show_phone_connected_status()

    async def _send_message(self, message: Dict) -> bool:
        """發送訊息到手機"""
        try:
            if not self.ble_server:
                self.logger.error("BLE 服務器未初始化")
                return False
            json_data = json.dumps(message, ensure_ascii=False)
            self.logger.debug(f"發送訊息: {json_data}")
            return await self.ble_server.send_data(json_data.encode("utf-8"))
        except Exception as e:
            self.logger.error(f"發送訊息失敗: {e}")
            return False