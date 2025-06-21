import asyncio
import logging
from typing import Optional, Callable, Dict, Any
from dbus_fast import BusType, Variant, Message, MessageType, PropertyAccess, RequestNameReply
from dbus_fast.aio import MessageBus
from dbus_fast.service import ServiceInterface, method, dbus_property, signal
from dbus_fast.introspection import Node

logger = logging.getLogger("BLE_Server")

# D-Bus 和 BlueZ 常數
BLUEZ_SERVICE = "org.bluez"
ADAPTER_PATH = "/org/bluez/hci0"
GATT_MANAGER_IFACE = "org.bluez.GattManager1"
GATT_SERVICE_IFACE = "org.bluez.GattService1"
GATT_CHARACTERISTIC_IFACE = "org.bluez.GattCharacteristic1"
DBUS_PROPERTIES_IFACE = "org.freedesktop.DBus.Properties"
DBUS_OBJECT_MANAGER_IFACE = "org.freedesktop.DBus.ObjectManager"
ADAPTER_IFACE = "org.bluez.Adapter1"
DEVICE_IFACE = "org.bluez.Device1"
ADVERTISING_MANAGER_IFACE = "org.bluez.LEAdvertisingManager1"
ADVERTISEMENT_IFACE = "org.bluez.LEAdvertisement1"
AGENT_MANAGER_IFACE = "org.bluez.AgentManager1"
AGENT_IFACE = "org.bluez.Agent1"

# EyeDwell UUID
SERVICE_UUID = "12345678-abcd-1234-5678-123456789abc"
COMMAND_CHAR_UUID = "12345678-abcd-1234-5678-123456789ab1"
DATA_CHAR_UUID = "12345678-abcd-1234-5678-123456789ab2"


class PairingAgent(ServiceInterface):
    """修正的配對代理，處理現代設備的配對過程"""
    
    def __init__(self):
        super().__init__(AGENT_IFACE)
        self.path = "/org/eyedwell/agent"

    @method()
    def Release(self):
        """配對代理被釋放時調用"""
        logger.debug("配對代理已釋放")

    @method()
    def AuthorizeService(self, device: "o", uuid: "s"):
        """授權服務連接"""
        logger.info(f"設備 {device} 請求服務 {uuid}")
        
        # 定義音訊和通話相關的 UUID 列表，包括 aptX 相關 UUID
        AUDIO_AND_CALL_RELATED_UUIDS = {
            "0000111e-0000-1000-8000-00805f9b34fb",  # Hands-Free Profile (HFP)
            "0000111f-0000-1000-8000-00805f9b34fb",  # Hands-Free Audio Gateway
            "0000110a-0000-1000-8000-00805f9b34fb",  # Audio Source (A2DP)
            "0000110b-0000-1000-8000-00805f9b34fb",  # Audio Sink (A2DP)
            "0000110d-0000-1000-8000-00805f9b34fb",  # Advanced Audio Distribution Profile (A2DP)
            "0000110e-0000-1000-8000-00805f9b34fb",  # Audio/Video Remote Control Profile (AVRCP)
        }
        
        # 檢查請求的 UUID 是否為音訊或通話相關
        if uuid.lower() in AUDIO_AND_CALL_RELATED_UUIDS:
            logger.info(f"拒絕音訊或通話相關服務 {uuid} 的配對請求")
            raise Exception("音訊或通話服務未授權")
        
        # 允許你的 EyeDwell 服務 UUID
        if uuid.lower() == SERVICE_UUID.lower():
            logger.info(f"授權 EyeDwell 服務 {uuid}")
            return
        
        # 如果是其他未知的 UUID，可以選擇拒絕或允許
        logger.warning(f"未知服務 {uuid}，默認拒絕")
        raise Exception("未知服務未授權")

    @method()
    def RequestPinCode(self, device: "o") -> "s":
        """請求 PIN 碼（舊式配對）- 通常不會被調用"""
        logger.info(f"設備 {device} 請求 PIN 碼（舊式配對）")
        return "0000"

    @method()
    def DisplayPinCode(self, device: "o", pincode: "s"):
        """顯示 PIN 碼"""
        logger.info(f"設備 {device} 的 PIN 碼: {pincode}")

    @method()
    def RequestPasskey(self, device: "o") -> "u":
        """請求密鑰（6位數字）- 較少使用"""
        logger.info(f"設備 {device} 請求密鑰")
        return 123456

    @method()
    def DisplayPasskey(self, device: "o", passkey: "u", entered: "q"):
        """顯示密鑰進度"""
        logger.info(f"設備 {device} 的密鑰: {passkey:06d} (已輸入: {entered})")

    @method()
    def RequestConfirmation(self, device: "o", passkey: "u"):
        """請求確認配對 - 這是現代設備最常用的方法"""
        logger.info(f"自動確認設備 {device} 的配對，密鑰: {passkey:06d}")
        # 自動確認配對
        return

    @method()
    def RequestAuthorization(self, device: "o"):
        """請求授權連接"""
        logger.info(f"自動授權設備 {device} 連接")
        # 自動授權連接
        return

    @method()
    def Cancel(self):
        """取消配對過程"""
        logger.info("配對過程被取消")

    def get_path(self):
        return self.path


class Advertisement(ServiceInterface):
    def __init__(self, index: int, device_name: str = "EyeDwell"):
        super().__init__(ADVERTISEMENT_IFACE)
        self.path = f"/org/eyedwell/advertisement{index}"
        self.device_name = device_name

    @dbus_property(access=PropertyAccess.READ)
    def Type(self) -> "s":
        return "peripheral"

    @dbus_property(access=PropertyAccess.READ)
    def LocalName(self) -> "s":
        return self.device_name

    @dbus_property(access=PropertyAccess.READ)
    def Appearance(self) -> "q":
        return 0x0080

    @dbus_property(access=PropertyAccess.READ)
    def ServiceUUIDs(self) -> "as":
        return [SERVICE_UUID]

    @dbus_property(access=PropertyAccess.READ)
    def Includes(self) -> "as":
        return ["tx-power"]

    @method()
    def Release(self):
        logger.debug("廣告已釋放")

    def get_path(self):
        return self.path


class GattApplication(ServiceInterface):
    def __init__(self, bus):
        super().__init__(DBUS_OBJECT_MANAGER_IFACE)
        self.bus = bus
        self.path = "/org/eyedwell/app"
        self.services = {}

    @method()
    async def GetManagedObjects(self) -> "a{oa{sa{sv}}}":
        result = {}
        logger.debug("GetManagedObjects 被調用")
        
        for path, service in self.services.items():
            logger.debug(f"處理服務路徑: {path}")
            # 手動構建服務屬性
            service_props = {
                "UUID": Variant("s", service.UUID),
                "Primary": Variant("b", service.Primary),
                "Device": Variant("o", service.Device),
            }
            result[path] = {GATT_SERVICE_IFACE: service_props}
            
            # 獲取特徵屬性
            for char_path, char in service.characteristics.items():
                logger.debug(f"處理特徵路徑: {char_path}")
                char_props = {
                    "Service": Variant("o", char.Service),
                    "UUID": Variant("s", char.UUID),
                    "Flags": Variant("as", char.Flags),
                    "Value": Variant("ay", char.Value),
                    "Notifying": Variant("b", char.Notifying),
                }
                result[char_path] = {GATT_CHARACTERISTIC_IFACE: char_props}
        
        logger.debug(f"GetManagedObjects 返回: {result}")
        return result

    def add_service(self, service):
        self.services[service.path] = service


class EyeDwellGattService(ServiceInterface):
    def __init__(self, bus):
        super().__init__(GATT_SERVICE_IFACE)
        self.bus = bus
        self.path = "/org/eyedwell/app/service0"
        self.uuid = SERVICE_UUID
        self.characteristics = {}

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> "s":
        return self.uuid

    @dbus_property(access=PropertyAccess.READ)
    def Primary(self) -> "b":
        return True

    @dbus_property(access=PropertyAccess.READ)
    def Device(self) -> "o":
        return ADAPTER_PATH

    def add_characteristic(self, characteristic):
        self.characteristics[characteristic.path] = characteristic


class EyeDwellCharacteristic(ServiceInterface):
    def __init__(self, bus, uuid, flags, path, ble_server=None):
        super().__init__(GATT_CHARACTERISTIC_IFACE)
        self.bus = bus
        self.path = path
        self.uuid = uuid
        self.flags = flags
        self.value = bytearray()
        self.ble_server = ble_server
        self.service_path = "/org/eyedwell/app/service0"
        self.notifying = False

    @dbus_property(access=PropertyAccess.READ)
    def Service(self) -> "o":
        return self.service_path

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> "s":
        return self.uuid

    @dbus_property(access=PropertyAccess.READ)
    def Flags(self) -> "as":
        return self.flags

    @dbus_property(access=PropertyAccess.READ)
    def Value(self) -> "ay":
        return self.value

    @dbus_property(access=PropertyAccess.READ)
    def Notifying(self) -> "b":
        return self.notifying

    def set_value(self, value: bytes):
        self.value = bytearray(value)
        if "notify" in self.flags and self.notifying:
            self.PropertiesChanged(GATT_CHARACTERISTIC_IFACE, {"Value": Variant("ay", self.value), "Notifying": Variant("b", self.notifying)}, [])

    @signal()
    def PropertiesChanged(self, interface: "s", changed: "a{sv}", invalidated: "as"):
        pass

    @method()
    async def ReadValue(self, options: "a{sv}") -> "ay":
        return self.value

    @method()
    async def WriteValue(self, value: "ay", options: "a{sv}"):
        self.value = bytearray(value)
        await self.on_write(bytes(value))

    @method()
    async def StartNotify(self):
        if "notify" not in self.flags:
            raise Exception("Notify not supported")
        self.notifying = True
        self.PropertiesChanged(GATT_CHARACTERISTIC_IFACE, {"Notifying": Variant("b", True)}, [])

    @method()
    async def StopNotify(self):
        self.notifying = False
        self.PropertiesChanged(GATT_CHARACTERISTIC_IFACE, {"Notifying": Variant("b", False)}, [])

    async def on_write(self, data: bytes):
        pass


class CommandCharacteristic(EyeDwellCharacteristic):
    def __init__(self, bus, ble_server):
        super().__init__(bus, COMMAND_CHAR_UUID, ["write"], "/org/eyedwell/app/service0/char0", ble_server)
        self.input_buffer = bytearray()  # 初始化輸入緩衝區

    async def on_write(self, data: bytes):
        if not self.ble_server:
            logger.error("BLE 服務器未設置")
            return

        # 將接收到的數據添加到緩衝區
        self.input_buffer.extend(data)
        logger.debug(f"接收到數據: {data.decode('utf-8', errors='ignore')}, 當前緩衝區: {self.input_buffer.decode('utf-8', errors='ignore')}")

        # 檢查緩衝區中的完整封包
        while b'{' in self.input_buffer and b'}' in self.input_buffer:
            start_idx = self.input_buffer.index(b'{')
            end_idx = self.input_buffer.index(b'}', start_idx) + 1
            packet = self.input_buffer[start_idx:end_idx]
            
            try:
                # 嘗試解碼為 UTF-8 並調用回調函數
                packet_str = packet.decode("utf-8")
                if self.ble_server.on_command_received:
                    await self.ble_server.on_command_received(packet_str)
                logger.info(f"處理完整封包: {packet_str}")
            except UnicodeDecodeError as e:
                logger.error(f"封包解碼失敗: {e}")
                # 清空緩衝區以避免無效數據累積
                self.input_buffer = bytearray()
                break
            except Exception as e:
                logger.error(f"處理封包時發生錯誤: {e}")
            
            # 移除已處理的封包
            self.input_buffer = self.input_buffer[end_idx:]
        
        # 如果緩衝區過長（例如超過 1KB），清空以防止溢出
        if len(self.input_buffer) > 1024:
            logger.warning("輸入緩衝區過長，清空緩衝區")
            self.input_buffer = bytearray()


class DataCharacteristic(EyeDwellCharacteristic):
    def __init__(self, bus, ble_server):
        super().__init__(bus, DATA_CHAR_UUID, ["read", "notify"], "/org/eyedwell/app/service0/char1", ble_server)


class BLEServer:
    def __init__(self, device_name: str = "EyeDwell"):
        self.device_name = device_name
        self.bus: Optional[MessageBus] = None
        self.data_char = None
        self.advertisement = None
        self.pairing_agent = None
        self.is_connected = False
        self.connected_device_path = None
        self.on_command_received: Optional[Callable[[str], Any]] = None
        self.monitor_task = None
        self.gatt_app = None

    async def start_server(self):
        try:
            await self._connect_dbus()
            await self._setup_adapter()
            await self._register_pairing_agent()
            await self._create_gatt_services()
            await self._register_advertisement()
            await self._register_gatt_application()
            logger.info("BLE 服務器啟動成功")
        except Exception as e:
            logger.error(f"啟動失敗: {e}")
            await self.stop_server()
            raise

    async def stop_server(self):
        try:
            if self.monitor_task:
                self.monitor_task.cancel()
                await self.monitor_task
            await self._unregister_advertisement()
            await self._unregister_gatt_application()
            await self._unregister_pairing_agent()
            if self.bus:
                self.bus.disconnect()
                self.bus = None
            logger.info("BLE 服務器已停止")
        except Exception as e:
            logger.error(f"停止失敗: {e}")

    async def _connect_dbus(self):
        try:
            self.bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
            result = await self.bus.request_name("org.eyedwell.BLEServer")
            if result == RequestNameReply.PRIMARY_OWNER:
                logger.info("D-Bus 名稱 org.eyedwell.BLEServer 已成功請求")
            elif result == RequestNameReply.IN_QUEUE:
                logger.warning("D-Bus 名稱 org.eyedwell.BLEServer 已在隊列中，等待其他進程釋放")
                raise Exception("D-Bus 名稱已在隊列中，請檢查是否有其他實例運行")
            elif result == RequestNameReply.EXISTS:
                logger.error("D-Bus 名稱 org.eyedwell.BLEServer 已被其他進程佔用")
                raise Exception("D-Bus 名稱已被佔用，請終止其他實例")
            elif result == RequestNameReply.ALREADY_OWNER:
                logger.warning("D-Bus 名稱 org.eyedwell.BLEServer 已被當前進程擁有")
            else:
                raise Exception(f"請求 D-Bus 名稱 org.eyedwell.BLEServer 失敗，返回碼: {result}")
        except Exception as e:
            logger.error(f"D-Bus 連接或名稱請求失敗: {e}")
            raise

    async def _setup_adapter(self):
        """設置藍牙適配器屬性"""
        try:
            # 基本設置
            await self._set_property("Powered", Variant("b", True))
            await self._set_property("Alias", Variant("s", self.device_name))
            await self._set_property("Discoverable", Variant("b", True))
            await self._set_property("Pairable", Variant("b", True))
            await self._set_property("PairableTimeout", Variant("u", 0))  # 永遠可配對
            await self._set_property("DiscoverableTimeout", Variant("u", 0))  # 永遠可發現
            logger.info(f"適配器設置完成，設備名稱: {self.device_name}")
        except Exception as e:
            logger.error(f"設置適配器失敗: {e}")
            raise

    async def _set_property(self, prop_name: str, value: Variant):
        reply = await self.bus.call(
            Message(
                destination=BLUEZ_SERVICE,
                path=ADAPTER_PATH,
                interface=DBUS_PROPERTIES_IFACE,
                member="Set",
                signature="ssv",
                body=[ADAPTER_IFACE, prop_name, value],
            )
        )
        if reply and reply.message_type == MessageType.ERROR:
            logger.error(f"設置 {prop_name} 失敗: {reply.body[0]}")

    async def _register_pairing_agent(self):
        """註冊配對代理"""
        try:
            self.pairing_agent = PairingAgent()
            self.bus.export(self.pairing_agent.get_path(), self.pairing_agent)
            
            capability = "DisplayYesNo"
            
            reply = await self.bus.call(
                Message(
                    destination=BLUEZ_SERVICE,
                    path="/org/bluez",
                    interface=AGENT_MANAGER_IFACE,
                    member="RegisterAgent",
                    signature="os",
                    body=[self.pairing_agent.get_path(), capability],
                )
            )
            
            if reply and reply.message_type == MessageType.ERROR:
                logger.error(f"註冊配對代理失敗: {reply.body[0]}")
                raise Exception(f"註冊配對代理失敗: {reply.body[0]}")
            
            # 設置為默認代理
            reply = await self.bus.call(
                Message(
                    destination=BLUEZ_SERVICE,
                    path="/org/bluez",
                    interface=AGENT_MANAGER_IFACE,
                    member="RequestDefaultAgent",
                    signature="o",
                    body=[self.pairing_agent.get_path()],
                )
            )
            
            if reply and reply.message_type == MessageType.ERROR:
                logger.warning(f"設置默認代理失敗: {reply.body[0]}")
                raise Exception(f"設置默認代理失敗: {reply.body[0]}")
            
            logger.info(f"配對代理已註冊，使用能力: {capability}")
            
        except Exception as e:
            logger.error(f"註冊配對代理錯誤: {e}")
            raise

    async def _unregister_pairing_agent(self):
        """取消註冊配對代理"""
        if not self.bus or not self.pairing_agent:
            logger.debug("無配對代理物件，跳過取消註冊")
            return
        
        try:
            reply = await self.bus.call(
                Message(
                    destination=BLUEZ_SERVICE,
                    path="/org/bluez",
                    interface=AGENT_MANAGER_IFACE,
                    member="UnregisterAgent",
                    signature="o",
                    body=[self.pairing_agent.get_path()],
                )
            )
            
            if reply and reply.message_type == MessageType.ERROR:
                logger.debug(f"取消配對代理註冊失敗: {reply.body[0]}")
            else:
                logger.info("配對代理已取消註冊")
            
            self.bus.unexport(self.pairing_agent.get_path())
            self.pairing_agent = None
            
        except Exception as e:
            logger.error(f"取消配對代理註冊錯誤: {e}")

    async def _register_advertisement(self):
        if not self.bus:
            logger.error("D-Bus 未連接，無法註冊廣告")
            return
        try:
            self.advertisement = Advertisement(0, self.device_name)
            self.bus.export(self.advertisement.get_path(), self.advertisement)
            # 提供 LEAdvertisingManager1 的內省數據
            introspection = Node.parse("""
                <node>
                    <interface name="org.bluez.LEAdvertisingManager1">
                        <method name="RegisterAdvertisement">
                            <arg type="o" name="advertisement" direction="in"/>
                            <arg type="a{sv}" name="options" direction="in"/>
                        </method>
                        <method name="UnregisterAdvertisement">
                            <arg type="o" name="advertisement" direction="in"/>
                        </method>
                    </interface>
                </node>
            """)
            obj = self.bus.get_proxy_object(BLUEZ_SERVICE, ADAPTER_PATH, introspection)
            ad_manager = obj.get_interface(ADVERTISING_MANAGER_IFACE)
            reply = await ad_manager.call_register_advertisement(self.advertisement.get_path(), {})
            if reply and reply.message_type == MessageType.ERROR:
                logger.error(f"註冊廣告失敗: {reply.body[0]}")
                raise Exception(f"註冊廣告失敗: {reply.body[0]}")
            logger.info("廣告已註冊")
        except Exception as e:
            logger.error(f"註冊廣告錯誤: {e}")
            raise

    async def _unregister_advertisement(self):
        if not self.bus or not self.advertisement:
            logger.debug("無廣告物件，跳過取消註冊")
            return
        try:
            introspection = Node.parse("""
                <node>
                    <interface name="org.bluez.LEAdvertisingManager1">
                        <method name="UnregisterAdvertisement">
                            <arg type="o" name="advertisement" direction="in"/>
                        </method>
                    </interface>
                </node>
            """)
            obj = self.bus.get_proxy_object(BLUEZ_SERVICE, ADAPTER_PATH, introspection)
            ad_manager = obj.get_interface(ADVERTISING_MANAGER_IFACE)
            reply = await ad_manager.call_unregister_advertisement(self.advertisement.get_path())
            if reply and reply.message_type == MessageType.ERROR:
                logger.debug(f"取消廣告註冊失敗: {reply.body[0]}")
            else:
                logger.info("廣告已取消註冊")
            self.bus.unexport(self.advertisement.get_path())
            self.advertisement = None
        except Exception as e:
            logger.error(f"取消廣告註冊錯誤: {e}")

    async def _create_gatt_services(self):
        self.gatt_app = GattApplication(self.bus)
        service = EyeDwellGattService(self.bus)
        self.data_char = DataCharacteristic(self.bus, self)
        service.add_characteristic(CommandCharacteristic(self.bus, self))
        service.add_characteristic(self.data_char)
        self.gatt_app.add_service(service)
        
        # 導出所有對象
        self.bus.export(self.gatt_app.path, self.gatt_app)
        self.bus.export(service.path, service)
        for char in service.characteristics.values():
            self.bus.export(char.path, char)

    async def _register_gatt_application(self):
        reply = await self.bus.call(
            Message(
                destination=BLUEZ_SERVICE,
                path=ADAPTER_PATH,
                interface=GATT_MANAGER_IFACE,
                member="RegisterApplication",
                signature="oa{sv}",
                body=["/org/eyedwell/app", {}],
            )
        )
        if reply and reply.message_type == MessageType.ERROR:
            logger.error(f"註冊 GATT 應用失敗: {reply.body[0]}")
            raise Exception(reply.body[0])

    async def _unregister_gatt_application(self):
        if self.bus:
            reply = await self.bus.call(
                Message(
                    destination=BLUEZ_SERVICE,
                    path=ADAPTER_PATH,
                    interface=GATT_MANAGER_IFACE,
                    member="UnregisterApplication",
                    signature="o",
                    body=["/org/eyedwell/app"],
                )
            )
            if reply and reply.message_type == MessageType.ERROR:
                logger.debug(f"取消註冊失敗: {reply.body[0]}")

    async def _set_device_property(self, device_path: str, prop_name: str, value: Variant):
        """設置設備屬性"""
        try:
            reply = await self.bus.call(
                Message(
                    destination=BLUEZ_SERVICE,
                    path=device_path,
                    interface=DBUS_PROPERTIES_IFACE,
                    member="Set",
                    signature="ssv",
                    body=[DEVICE_IFACE, prop_name, value],
                )
            )
            if reply and reply.message_type == MessageType.ERROR:
                logger.error(f"設置設備 {device_path} 的 {prop_name} 失敗: {reply.body[0]}")
        except Exception as e:
            logger.error(f"設置設備屬性錯誤: {e}")

    async def send_data(self, data: bytes) -> bool:
        if not self.is_connected or not self.data_char:
            return False
        if len(data) > 500:
            data = data[:500]
        self.data_char.set_value(data)
        return True
