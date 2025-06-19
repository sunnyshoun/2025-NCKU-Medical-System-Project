import asyncio
import logging
import json
import time
from typing import Optional, Callable
from dbus_fast import BusType, Variant, Message
from dbus_fast.aio import MessageBus
from dbus_fast.service import ServiceInterface, method, signal

logger = logging.getLogger("BLE_Server")

BLUEZ_SERVICE = "org.bluez"
GATT_MANAGER_IFACE = "org.bluez.GattManager1"
GATT_SERVICE_IFACE = "org.bluez.GattService1"
GATT_CHARACTERISTIC_IFACE = "org.bluez.GattCharacteristic1"
GATT_DESCRIPTOR_IFACE = "org.bluez.GattDescriptor1"
DBUS_PROPERTIES_IFACE = "org.freedesktop.DBus.Properties"
DBUS_OBJECT_MANAGER_IFACE = "org.freedesktop.DBus.ObjectManager"
ADAPTER_PATH = "/org/bluez/hci0"

class GattApplication(ServiceInterface):
    def __init__(self, bus, path):
        super().__init__(DBUS_OBJECT_MANAGER_IFACE)
        self.bus = bus
        self.path = path
        self.services = {}
        self.next_index = 0

    @method()
    def GetManagedObjects(self):
        response = {}
        for path, service in self.services.items():
            response[path] = service.get_properties()
            # 添加特徵值
            for char_path, char in service.characteristics.items():
                response[char_path] = char.get_properties()
        return response

    def add_service(self, service):
        service.set_index(self.next_index)
        self.services[service.get_path()] = service
        self.next_index += 1

class GattService(ServiceInterface):
    def __init__(self, bus, index, uuid, primary=True):
        self.bus = bus
        self.index = index
        self.uuid = uuid
        self.primary = primary
        self.characteristics = {}
        self.path = f"/org/example/service{index:04d}"
        super().__init__(GATT_SERVICE_IFACE)

    def get_properties(self):
        return {
            GATT_SERVICE_IFACE: {
                'UUID': Variant('s', self.uuid),
                'Primary': Variant('b', self.primary)
            }
        }

    def get_path(self):
        return self.path

    def set_index(self, index):
        self.index = index
        self.path = f"/org/example/service{index:04d}"

    def add_characteristic(self, characteristic):
        characteristic.service = self
        self.characteristics[characteristic.get_path()] = characteristic

class GattCharacteristic(ServiceInterface):
    def __init__(self, bus, index, uuid, flags, service):
        self.bus = bus
        self.index = index
        self.uuid = uuid
        self.flags = flags
        self.service = service
        self.value = []
        self.path = f"{service.path}/char{index:04d}"
        
        # 回調函數
        self.read_callback = None
        self.write_callback = None
        
        super().__init__(GATT_CHARACTERISTIC_IFACE)

    def get_properties(self):
        return {
            GATT_CHARACTERISTIC_IFACE: {
                'Service': Variant('o', self.service.get_path()),
                'UUID': Variant('s', self.uuid),
                'Flags': Variant('as', self.flags),
                'Value': Variant('ay', self.value)
            }
        }

    def get_path(self):
        return self.path

    def set_value(self, value):
        self.value = value
        if 'notify' in self.flags:
            self.PropertiesChanged(
                GATT_CHARACTERISTIC_IFACE,
                {'Value': Variant('ay', value)},
                []
            )

    @signal()
    def PropertiesChanged(self, interface: "s", changed: "a{sv}", invalidated: "as"):
        pass

    @method()
    def ReadValue(self, options: "a{sv}"):
        logger.info(f"特徵值讀取請求: {self.uuid}")
        if self.read_callback:
            return self.read_callback()
        return self.value

    @method()
    def WriteValue(self, value: "ay", options: "a{sv}"):
        logger.info(f"特徵值寫入請求: {self.uuid}, 長度: {len(value)}")
        self.value = value
        if self.write_callback:
            self.write_callback(bytes(value))

    @method()
    def StartNotify(self):
        logger.info(f"開始通知: {self.uuid}")
        return

    @method()
    def StopNotify(self):
        logger.info(f"停止通知: {self.uuid}")
        return

class BLEServer:
    # 視力測試機器人專用的 UUID
    VISION_ROBOT_SERVICE_UUID = "12345678-abcd-1234-5678-123456789abc"
    CONTROL_CHAR_UUID = "12345678-abcd-1234-5678-123456789ab1"  # 控制命令
    DATA_CHAR_UUID = "12345678-abcd-1234-5678-123456789ab2"     # 數據傳輸
    STATUS_CHAR_UUID = "12345678-abcd-1234-5678-123456789ab4"   # 狀態回報

    def __init__(self, device_name: str = "EyeDwell"):
        self.device_name = device_name
        self.bus: Optional[MessageBus] = None
        self.is_connected = False
        self.client_address = ""
        
        # GATT 應用程序和服務
        self.app = None
        self.service = None
        self.control_char = None
        self.data_char = None
        self.status_char = None
        
        # 回調函數
        self.on_control_command: Optional[Callable[[str], None]] = None
        self.on_data_received: Optional[Callable[[bytes], None]] = None
        self.on_connection_changed: Optional[Callable[[bool], None]] = None
        
        # 測試狀態
        self.test_active = False
        self.waiting_for_response = False

    async def start_server(self):
        try:
            await self._connect_dbus()
            await self._setup_adapter()
            await self._setup_gatt_services()
            await self._register_gatt_application()
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
                await self._unregister_gatt_application()
                self.bus.disconnect()
                self.bus = None
            logger.info("BLE server stopped")
        except Exception as e:
            logger.error(f"Error stopping server: {e}")

    async def _connect_dbus(self):
        self.bus = await MessageBus(bus_type=BusType.SYSTEM).connect()

    async def _setup_adapter(self):
        # 檢查適配器是否存在
        try:
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
        except Exception as e:
            logger.error(f"適配器不存在或無法訪問: {e}")
            raise
        
        # 設置適配器屬性
        properties = [
            ("Alias", Variant("s", self.device_name)),
            ("Powered", Variant("b", True)),
            ("Discoverable", Variant("b", True)),
            ("DiscoverableTimeout", Variant("u", 0)),
            ("Pairable", Variant("b", True)),
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
            except Exception as e:
                logger.warning(f"設置屬性 {prop} 失敗: {e}")

    async def _setup_gatt_services(self):
        """設置 GATT 服務和特徵值"""
        # 創建 GATT 應用程序
        self.app = GattApplication(self.bus, "/org/example")
        
        # 創建視力測試服務
        self.service = GattService(self.bus, 0, self.VISION_ROBOT_SERVICE_UUID)
        
        # 創建控制特徵值（手機寫入命令）
        self.control_char = GattCharacteristic(
            self.bus, 0, self.CONTROL_CHAR_UUID, 
            ['write', 'write-without-response'], self.service
        )
        self.control_char.write_callback = self._handle_control_write
        
        # 創建數據特徵值（機器人發送數據，手機讀取和接收通知）
        self.data_char = GattCharacteristic(
            self.bus, 1, self.DATA_CHAR_UUID,
            ['read', 'notify'], self.service
        )
        self.data_char.read_callback = self._handle_data_read
        
        # 創建狀態特徵值（機器人發送狀態）
        self.status_char = GattCharacteristic(
            self.bus, 2, self.STATUS_CHAR_UUID,
            ['read', 'notify'], self.service
        )
        self.status_char.read_callback = self._handle_status_read
        
        # 將特徵值添加到服務
        self.service.add_characteristic(self.control_char)
        self.service.add_characteristic(self.data_char)
        self.service.add_characteristic(self.status_char)
        
        # 將服務添加到應用程序
        self.app.add_service(self.service)
        
        # 在 D-Bus 上註冊所有服務和特徵值
        self.bus.export("/org/example", self.app)
        self.bus.export(self.service.get_path(), self.service)
        self.bus.export(self.control_char.get_path(), self.control_char)
        self.bus.export(self.data_char.get_path(), self.data_char)
        self.bus.export(self.status_char.get_path(), self.status_char)

    async def _register_gatt_application(self):
        """註冊 GATT 應用程序"""
        try:
            await self.bus.call(
                Message(
                    destination=BLUEZ_SERVICE,
                    path=ADAPTER_PATH,
                    interface=GATT_MANAGER_IFACE,
                    member="RegisterApplication",
                    signature="oa{sv}",
                    body=["/org/example", {}]
                )
            )
            logger.info("GATT 應用程序註冊成功")
        except Exception as e:
            logger.error(f"GATT 應用程序註冊失敗: {e}")
            raise

    async def _unregister_gatt_application(self):
        """取消註冊 GATT 應用程序"""
        try:
            await self.bus.call(
                Message(
                    destination=BLUEZ_SERVICE,
                    path=ADAPTER_PATH,
                    interface=GATT_MANAGER_IFACE,
                    member="UnregisterApplication",
                    signature="o",
                    body=["/org/example"]
                )
            )
            logger.info("GATT 應用程序取消註冊成功")
        except Exception as e:
            logger.warning(f"GATT 應用程序取消註冊失敗: {e}")

    async def _register_advertisement(self):
        """註冊 BLE 廣播"""
        try:
            # 使用 hciconfig 命令啟用廣播
            proc = await asyncio.create_subprocess_exec(
                'sudo', 'hciconfig', 'hci0', 'up',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            
            proc = await asyncio.create_subprocess_exec(
                'sudo', 'hciconfig', 'hci0', 'piscan',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            
            proc = await asyncio.create_subprocess_exec(
                'sudo', 'hciconfig', 'hci0', 'leadv',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            
            logger.info("BLE 廣播已啟用")
        except Exception as e:
            logger.error(f"BLE 廣播註冊失敗: {e}")

    async def _stop_advertisement(self):
        """停止 BLE 廣播"""
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
            logger.info("BLE 廣播已停止")
        except Exception as e:
            logger.warning(f"停止 BLE 廣播失敗: {e}")

    async def _monitor_connections(self):
        """監控連線狀態"""
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
                
            except Exception as e:
                logger.error(f"監控連線狀態時發生錯誤: {e}")
                await asyncio.sleep(5)

    def _handle_control_write(self, data: bytes):
        """處理控制特徵值的寫入"""
        try:
            command = data.decode('utf-8', errors='ignore')
            logger.info(f"收到控制命令: {command}")
            
            if self.on_control_command:
                if asyncio.iscoroutinefunction(self.on_control_command):
                    asyncio.create_task(self.on_control_command(command))
                else:
                    self.on_control_command(command)
        except Exception as e:
            logger.error(f"處理控制命令時發生錯誤: {e}")

    def _handle_data_read(self):
        """處理數據特徵值的讀取"""
        return self.data_char.value

    def _handle_status_read(self):
        """處理狀態特徵值的讀取"""
        return self.status_char.value

    async def send_data(self, data: bytes) -> bool:
        """發送數據到手機"""
        if not self.is_connected:
            logger.warning("無法發送數據：手機未連線")
            return False
        
        try:
            # 限制數據大小（BLE MTU 限制）
            if len(data) > 500:
                logger.warning(f"數據過大: {len(data)} bytes，截斷至500字節")
                data = data[:500]
            
            self.data_char.set_value(list(data))
            logger.info(f"數據已發送: {len(data)} bytes")
            return True
        except Exception as e:
            logger.error(f"發送數據時發生錯誤: {e}")
            return False

    async def send_status_update(self, status: str, details: dict = None) -> bool:
        """發送狀態更新到手機"""
        if not self.is_connected:
            logger.warning("無法發送狀態：手機未連線")
            return False
        
        status_data = {
            "status": status,
            "details": details or {},
            "timestamp": time.time(),
            "robot_id": self.device_name
        }
        
        try:
            json_data = json.dumps(status_data, ensure_ascii=False)
            data = json_data.encode('utf-8')
            
            # 限制數據大小
            if len(data) > 500:
                logger.warning(f"狀態數據過大: {len(data)} bytes")
                return False
            
            self.status_char.set_value(list(data))
            logger.info(f"狀態更新已發送: {status}")
            return True
        except Exception as e:
            logger.error(f"發送狀態更新時發生錯誤: {e}")
            return False

    def get_robot_status(self) -> dict:
        """獲取機器人當前狀態"""
        return {
            "connected": self.is_connected,
            "device_name": self.device_name,
            "client_address": self.client_address,
            "test_active": self.test_active,
            "waiting_for_response": self.waiting_for_response,
            "timestamp": time.time()
        }