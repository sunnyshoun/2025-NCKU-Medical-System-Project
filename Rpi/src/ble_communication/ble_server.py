import asyncio
import logging
import json
import os
import time
from typing import Optional, Callable, Dict, Any
from dbus_fast import BusType, Variant, Message
from dbus_fast.aio import MessageBus
from dbus_fast.service import ServiceInterface, method

logger = logging.getLogger("BLE_Server")

BLUEZ_SERVICE = "org.bluez"
GATT_MANAGER_IFACE = "org.bluez.GattManager1"
GATT_SERVICE_IFACE = "org.bluez.GattService1"
GATT_CHARACTERISTIC_IFACE = "org.bluez.GattCharacteristic1"
DBUS_PROPERTIES_IFACE = "org.freedesktop.DBus.Properties"
DBUS_OBJECT_MANAGER_IFACE = "org.freedesktop.DBus.ObjectManager"
ADAPTER_PATH = "/org/bluez/hci0"

class GattApplication(ServiceInterface):
    def __init__(self):
        super().__init__(DBUS_OBJECT_MANAGER_IFACE)
        self.services = {}

    @method()
    def GetManagedObjects(self):
        response = {}
        for path, service in self.services.items():
            response[path] = {
                GATT_SERVICE_IFACE: {
                    'UUID': Variant('s', service['uuid']),
                    'Primary': Variant('b', service['primary'])
                }
            }
            for char_path, char_data in service.get('characteristics', {}).items():
                response[char_path] = {
                    GATT_CHARACTERISTIC_IFACE: {
                        'UUID': Variant('s', char_data['uuid']),
                        'Service': Variant('o', path),
                        'Flags': Variant('as', char_data['flags']),
                        'Value': Variant('ay', char_data.get('value', b''))
                    }
                }
        return response

class BLEServer:
    # 視力測試機器人專用的 UUID
    VISION_ROBOT_SERVICE_UUID = "12345678-abcd-1234-5678-123456789abc"
    CONTROL_CHAR_UUID = "12345678-abcd-1234-5678-123456789ab1"  # 控制命令
    DATA_CHAR_UUID = "12345678-abcd-1234-5678-123456789ab2"     # 數據傳輸
    AUDIO_CHAR_UUID = "12345678-abcd-1234-5678-123456789ab3"    # 音訊檔案
    STATUS_CHAR_UUID = "12345678-abcd-1234-5678-123456789ab4"   # 狀態回報
    RESPONSE_CHAR_UUID = "12345678-abcd-1234-5678-123456789ab5" # 使用者回應

    def __init__(self, device_name: str = "EyeDwell_Robot"):
        self.device_name = device_name
        self.bus: Optional[MessageBus] = None
        self.is_connected = False
        self.client_address = ""
        
        self.app_path = "/org/example/gatt"
        self.service_path = f"{self.app_path}/service0"
        
        self.characteristics_data = {
            self.CONTROL_CHAR_UUID: {'value': b'', 'flags': ['write', 'write-without-response']},
            self.DATA_CHAR_UUID: {'value': b'Ready', 'flags': ['read', 'write', 'notify']},
            self.AUDIO_CHAR_UUID: {'value': b'', 'flags': ['write', 'write-without-response']},
            self.STATUS_CHAR_UUID: {'value': b'{}', 'flags': ['read', 'notify']},
            self.RESPONSE_CHAR_UUID: {'value': b'', 'flags': ['write', 'write-without-response']},
        }
        
        # 回調函數
        self.on_control_command: Optional[Callable[[str], None]] = None
        self.on_data_received: Optional[Callable[[bytes], None]] = None
        self.on_audio_received: Optional[Callable[[bytes], None]] = None
        self.on_user_response: Optional[Callable[[str], None]] = None
        self.on_connection_changed: Optional[Callable[[bool], None]] = None
        
        # 檔案傳輸緩衝區
        self._audio_buffer = bytearray()
        self._expected_audio_size = 0
        self._audio_transfer_active = False
        
        # 測試狀態
        self.test_active = False
        self.waiting_for_response = False

    async def start_server(self):
        try:
            await self._connect_dbus()
            await self._setup_adapter()
            await self._register_advertisement()
            
            logger.info(f"視力測試 BLE 服務器啟動: {self.device_name}")
            asyncio.create_task(self._monitor_connections())
            
        except Exception as e:
            logger.error(f"Failed to start BLE server: {e}")
            await self.stop_server()
            raise

    async def stop_server(self):
        try:
            if self.bus:
                await self._stop_advertisement()
                self.bus.disconnect()
                self.bus = None
            logger.info("BLE server stopped")
        except Exception as e:
            logger.error(f"Error stopping server: {e}")

    async def _connect_dbus(self):
        self.bus = await MessageBus(bus_type=BusType.SYSTEM).connect()

    async def _setup_adapter(self):
        await self.bus.call(
            Message(
                destination=BLUEZ_SERVICE,
                path=ADAPTER_PATH,
                interface=DBUS_PROPERTIES_IFACE,
                member="GetAll",
                signature="s",
                body=["org.bluez.Adapter1"]
            )
        )
        
        properties = [
            ("Alias", Variant("s", self.device_name)),
            ("Powered", Variant("b", True)),
            ("Discoverable", Variant("b", True)),
            ("DiscoverableTimeout", Variant("u", 0)),
            ("Appearance", Variant("q", 0x0080)),  # 設備外觀：通用設備
            ("Class", Variant("u", 0x000100)),     # 設備類別
        ]
        
        for prop, value in properties:
            try:
                await self.bus.call(
                    Message(
                        destination=BLUEZ_SERVICE,
                        path=ADAPTER_PATH,
                        interface=DBUS_PROPERTIES_IFACE,
                        member="Set",
                        signature="ssv",
                        body=["org.bluez.Adapter1", prop, value]
                    )
                )
            except Exception:
                pass

    async def _register_advertisement(self):
        try:
            await asyncio.create_subprocess_exec('sudo', 'hciconfig', 'hci0', 'up')
            await asyncio.sleep(0.5)
            await asyncio.create_subprocess_exec('sudo', 'hciconfig', 'hci0', 'piscan')
            await asyncio.sleep(0.5)
            await asyncio.create_subprocess_exec('sudo', 'hciconfig', 'hci0', 'leadv')
            logger.info("BLE 廣播已註冊")
        except Exception as e:
            logger.error(f"Advertisement registration failed: {e}")

    async def _stop_advertisement(self):
        try:
            await self.bus.call(
                Message(
                    destination=BLUEZ_SERVICE,
                    path=ADAPTER_PATH,
                    interface=DBUS_PROPERTIES_IFACE,
                    member="Set",
                    signature="ssv",
                    body=["org.bluez.Adapter1", "Discoverable", Variant("b", False)]
                )
            )
        except Exception:
            pass

    async def _monitor_connections(self):
        last_connected = False
        
        while self.bus:
            try:
                reply = await self.bus.call(
                    Message(
                        destination=BLUEZ_SERVICE,
                        path="/",
                        interface=DBUS_OBJECT_MANAGER_IFACE,
                        member="GetManagedObjects",
                        signature="",
                        body=[]
                    )
                )
                
                connected = False
                client_addr = ""
                
                for path, interfaces in reply.body[0].items():
                    if "org.bluez.Device1" in interfaces:
                        device_props = interfaces["org.bluez.Device1"]
                        if device_props.get("Connected", Variant("b", False)).value:
                            connected = True
                            if "/dev_" in path:
                                client_addr = path.split("/dev_")[-1].replace("_", ":")
                            break
                
                if connected != last_connected:
                    self.is_connected = connected
                    self.client_address = client_addr
                    logger.info(f"手機連線狀態: {connected}")
                    
                    if self.on_connection_changed:
                        try:
                            if asyncio.iscoroutinefunction(self.on_connection_changed):
                                await self.on_connection_changed(connected)
                            else:
                                self.on_connection_changed(connected)
                        except Exception as e:
                            logger.error(f"Error in connection callback: {e}")
                    
                    last_connected = connected
                
                await asyncio.sleep(2)
                
            except Exception:
                await asyncio.sleep(5)

    def handle_control_command(self, data: bytes):
        """處理來自手機的控制命令"""
        try:
            command = data.decode('utf-8', errors='ignore')
            logger.info(f"收到控制命令: {command}")
            
            self.characteristics_data[self.CONTROL_CHAR_UUID]['value'] = data
            
            if self.on_control_command:
                if asyncio.iscoroutinefunction(self.on_control_command):
                    asyncio.create_task(self.on_control_command(command))
                else:
                    self.on_control_command(command)
        except Exception as e:
            logger.error(f"Error handling control command: {e}")

    def handle_data_received(self, data: bytes):
        """處理來自手機的一般數據"""
        try:
            logger.info(f"收到數據: {len(data)} bytes")
            self.characteristics_data[self.DATA_CHAR_UUID]['value'] = data
            
            if self.on_data_received:
                if asyncio.iscoroutinefunction(self.on_data_received):
                    asyncio.create_task(self.on_data_received(data))
                else:
                    self.on_data_received(data)
        except Exception as e:
            logger.error(f"Error handling data: {e}")

    def handle_audio_transfer(self, data: bytes):
        """處理來自手機的音訊檔案傳輸"""
        try:
            if not self._audio_transfer_active:
                if len(data) >= 4:
                    self._expected_audio_size = int.from_bytes(data[:4], 'big')
                    self._audio_buffer = bytearray(data[4:])
                    self._audio_transfer_active = True
                    logger.info(f"音訊傳輸開始: {self._expected_audio_size} bytes")
                else:
                    logger.warning("無效的音訊傳輸開始")
                    return
            else:
                self._audio_buffer.extend(data)
                
            if len(self._audio_buffer) >= self._expected_audio_size:
                audio_data = bytes(self._audio_buffer[:self._expected_audio_size])
                logger.info(f"音訊傳輸完成: {len(audio_data)} bytes")
                
                if self.on_audio_received:
                    if asyncio.iscoroutinefunction(self.on_audio_received):
                        asyncio.create_task(self.on_audio_received(audio_data))
                    else:
                        self.on_audio_received(audio_data)
                
                self._audio_buffer.clear()
                self._expected_audio_size = 0
                self._audio_transfer_active = False
                
        except Exception as e:
            logger.error(f"Error handling audio transfer: {e}")
            self._audio_transfer_active = False

    def handle_user_response(self, data: bytes):
        """處理來自手機的使用者回應"""
        try:
            response = data.decode('utf-8', errors='ignore')
            logger.info(f"收到使用者回應: {response}")
            
            self.characteristics_data[self.RESPONSE_CHAR_UUID]['value'] = data
            
            if self.on_user_response:
                if asyncio.iscoroutinefunction(self.on_user_response):
                    asyncio.create_task(self.on_user_response(response))
                else:
                    self.on_user_response(response)
        except Exception as e:
            logger.error(f"Error handling user response: {e}")

    async def send_data(self, data: bytes) -> bool:
        """發送數據到手機"""
        if not self.is_connected:
            logger.warning("無法發送數據：手機未連線")
            return False
        
        try:
            self.characteristics_data[self.DATA_CHAR_UUID]['value'] = data
            logger.info(f"數據已準備發送: {len(data)} bytes")
            return True
        except Exception as e:
            logger.error(f"Error sending data: {e}")
            return False

    async def send_audio_file(self, audio_data: bytes) -> bool:
        """發送音訊檔案到手機"""
        if not self.is_connected:
            logger.warning("無法發送音訊：手機未連線")
            return False
        
        try:
            size_header = len(audio_data).to_bytes(4, 'big')
            full_data = size_header + audio_data
            self.characteristics_data[self.AUDIO_CHAR_UUID]['value'] = full_data
            logger.info(f"音訊檔案已準備發送: {len(audio_data)} bytes")
            return True
        except Exception as e:
            logger.error(f"Error sending audio file: {e}")
            return False

    async def send_status_update(self, status: str, details: dict = None) -> bool:
        """發送狀態更新到手機"""
        status_data = {
            "status": status,
            "details": details or {},
            "timestamp": time.time(),
            "robot_id": self.device_name
        }
        
        try:
            self.characteristics_data[self.STATUS_CHAR_UUID]['value'] = json.dumps(status_data).encode('utf-8')
            logger.info(f"狀態更新已準備: {status}")
            return True
        except Exception as e:
            logger.error(f"Error sending status update: {e}")
            return False

    async def request_user_input(self, message: str, input_type: str = "direction") -> bool:
        """請求使用者輸入"""
        command = {
            "type": "request_input",
            "input_type": input_type,
            "message": message,
            "timestamp": time.time()
        }
        
        self.waiting_for_response = True
        return await self.send_data(json.dumps(command).encode('utf-8'))

    def get_robot_status(self) -> dict:
        """獲取機器人當前狀態"""
        return {
            "connected": self.is_connected,
            "device_name": self.device_name,
            "client_address": self.client_address,
            "test_active": self.test_active,
            "audio_transfer_active": self._audio_transfer_active,
            "waiting_for_response": self.waiting_for_response,
            "timestamp": time.time()
        }


# 測試用的主函數
async def main():
    def on_control_command(command: str):
        logger.info(f"控制命令: {command}")
        try:
            cmd_data = json.loads(command)
            cmd_type = cmd_data.get("type")
            
            if cmd_type == "start_test":
                logger.info("開始視力測試")
            elif cmd_type == "stop_test":
                logger.info("停止測試")
            elif cmd_type == "test_response":
                direction = cmd_data.get("direction")
                logger.info(f"測試回應: 方向 {direction}")
            else:
                logger.info(f"未知命令: {cmd_type}")
                
        except json.JSONDecodeError:
            logger.info(f"非 JSON 命令: {command}")
    
    def on_data_received(data: bytes):
        logger.info(f"收到數據: {len(data)} bytes")
        try:
            if data.startswith(b'{'):
                text = data.decode('utf-8', errors='ignore')
                data_obj = json.loads(text)
                logger.info(f"數據內容: {data_obj}")
            else:
                logger.info(f"二進位數據: {data.hex()[:50]}...")
        except:
            logger.info(f"原始數據: {data[:50]}...")
    
    def on_audio_received(audio_data: bytes):
        logger.info(f"收到音訊檔案: {len(audio_data)} bytes")
        try:
            # 儲存音訊檔案用於測試
            filename = f"received_audio_{int(time.time())}.wav"
            with open(filename, "wb") as f:
                f.write(audio_data)
            logger.info(f"音訊檔案已儲存: {filename}")
        except Exception as e:
            logger.error(f"儲存音訊檔案失敗: {e}")
    
    def on_user_response(response: str):
        logger.info(f"使用者回應: {response}")
        try:
            response_data = json.loads(response)
            direction = response_data.get("direction")
            logger.info(f"使用者選擇方向: {direction}")
        except json.JSONDecodeError:
            logger.info(f"文字回應: {response}")
    
    def on_connection_changed(connected: bool):
        status = "已連線" if connected else "已斷線"
        logger.info(f"手機 {status}")
    
    # 創建並啟動 BLE 服務器
    robot = BLEServer("EyeDwell_Vision_Robot")
    robot.on_control_command = on_control_command
    robot.on_data_received = on_data_received
    robot.on_audio_received = on_audio_received
    robot.on_user_response = on_user_response
    robot.on_connection_changed = on_connection_changed
    
    try:
        logger.info("啟動視力測試機器人 BLE 服務器...")
        await robot.start_server()
        
        heartbeat_counter = 0
        while True:
            await asyncio.sleep(10)
            
            if robot.is_connected:
                # 發送心跳包
                await robot.send_status_update("ready", {
                    "heartbeat": heartbeat_counter,
                    "test_available": True
                })
                heartbeat_counter += 1
                
                # 每分鐘發送一次測試邀請
                if heartbeat_counter % 6 == 0:
                    await robot.send_test_command("test_available", {
                        "message": "準備開始視力測試",
                        "languages": ["中文", "English", "日本語", "台語"]
                    })
                    logger.info("發送測試邀請")
            
    except KeyboardInterrupt:
        logger.info("正在關閉服務器...")
    except Exception as e:
        logger.error(f"服務器錯誤: {e}")
    finally:
        await robot.stop_server()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())