import json
import logging
from typing import Optional, Dict
from ble_communication.ble_server import BLEServer

class PhoneHandler:
    def __init__(self, robot_controller):
        self.logger = logging.getLogger("PhoneHandler")
        self.robot_controller = robot_controller
        self.ble_server: Optional[BLEServer] = None
        self.connection_status = False

    async def start(self):
        self.ble_server = BLEServer("EyeDwell")
        self.ble_server.on_command_received = self._handle_command
        await self.ble_server.start_server()

    async def stop(self):
        if self.ble_server:
            await self.ble_server.stop_server()
            self.ble_server = None
        self.connection_status = False

    def is_connected(self) -> bool:
        return self.connection_status

    async def _handle_command(self, command: str):
        try:
            cmd_data = json.loads(command)
            cmd_type = cmd_data.get("type")
            
            if cmd_type == "connect":
                await self.robot_controller.switch_to_phone_mode()
            
            elif cmd_type == "disconnect":
                await self.robot_controller.switch_to_button_mode()
                if self.robot_controller.test_coordinator:
                    self.robot_controller.test_coordinator.stop_test()
            
            elif cmd_type == "start_test":
                success = self.robot_controller.start_phone_test()
                if success:
                    self.robot_controller.oled.clear()
                else:
                    self.logger.error("Cannot start test")
            
            elif cmd_type == "direction_response":
                direction = cmd_data.get("direction")
                if direction in [0, 1, 2, 3]:
                    if self.robot_controller.test_coordinator:
                        self.robot_controller.test_coordinator.set_phone_response(direction)
                else:
                    self.logger.warning(f"Invalid direction value: {direction}")
            
            elif cmd_type == "stt_response":
                text = cmd_data.get("text", "").strip()
                direction = self._text_to_direction(text)
                if direction is not None:
                    if self.robot_controller.test_coordinator:
                        self.robot_controller.test_coordinator.set_phone_response(direction)
                else:
                    self.logger.warning(f"Unrecognized direction text: {text}")
            
            else:
                self.logger.warning(f"Unknown command type: {cmd_type}")
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Cannot parse command: {command}, error: {e}")
        except Exception as e:
            self.logger.error(f"Handle command failed: {e}")

    def _text_to_direction(self, text: str) -> Optional[int]:
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
        message = {
            "type": "test_complete",
            "score": str(vision_score)
        }
        await self._send_message(message)
        await self.robot_controller.show_phone_connected_status()

    async def _send_message(self, message: Dict) -> bool:
        try:
            if not self.ble_server:
                self.logger.error("BLE server not initialized")
                return False
            json_data = json.dumps(message, ensure_ascii=False)
            return await self.ble_server.send_data(json_data.encode("utf-8"))
        except Exception as e:
            self.logger.error(f"Send message failed: {e}")
            return False