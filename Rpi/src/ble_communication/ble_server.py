import logging
import subprocess
from typing import Optional, Callable, Dict, Any
from dbus_fast import BusType, Variant, Message, MessageType, PropertyAccess, RequestNameReply
from dbus_fast.aio import MessageBus
from dbus_fast.service import ServiceInterface, method, dbus_property, signal
from dbus_fast.introspection import Node

logger = logging.getLogger("BLE_Server")

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

SERVICE_UUID = "12345678-abcd-1234-5678-123456789abc"
COMMAND_CHAR_UUID = "12345678-abcd-1234-5678-123456789ab1"
DATA_CHAR_UUID = "12345678-abcd-1234-5678-123456789ab2"


class PairingAgent(ServiceInterface):
    def __init__(self):
        super().__init__(AGENT_IFACE)
        self.path = "/org/eyedwell/agent"

    @method()
    def Release(self):
        pass

    @method()
    def AuthorizeService(self, device: "o", uuid: "s"):
        uuid_lower = uuid.lower()
        if uuid_lower == SERVICE_UUID.lower():
            return
        raise Exception(f"Only EyeDwell service allowed, denied service {uuid}")

    @method()
    def RequestPinCode(self, device: "o") -> "s":
        return "0000"

    @method()
    def DisplayPinCode(self, device: "o", pincode: "s"):
        pass

    @method()
    def RequestPasskey(self, device: "o") -> "u":
        return 123456

    @method()
    def DisplayPasskey(self, device: "o", passkey: "u", entered: "q"):
        pass

    @method()
    def RequestConfirmation(self, device: "o", passkey: "u"):
        return

    @method()
    def RequestAuthorization(self, device: "o"):
        return

    @method()
    def Cancel(self):
        pass

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
        pass

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
        
        for path, service in self.services.items():
            service_props = {
                "UUID": Variant("s", service.UUID),
                "Primary": Variant("b", service.Primary),
                "Device": Variant("o", service.Device),
            }
            result[path] = {GATT_SERVICE_IFACE: service_props}
            
            for char_path, char in service.characteristics.items():
                char_props = {
                    "Service": Variant("o", char.Service),
                    "UUID": Variant("s", char.UUID),
                    "Flags": Variant("as", char.Flags),
                    "Value": Variant("ay", char.Value),
                    "Notifying": Variant("b", char.Notifying),
                }
                result[char_path] = {GATT_CHARACTERISTIC_IFACE: char_props}
        
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
            signal_msg = Message(
                message_type=MessageType.SIGNAL,
                path=self.path,
                interface=DBUS_PROPERTIES_IFACE,
                member="PropertiesChanged",
                signature="sa{sv}as",
                body=[GATT_CHARACTERISTIC_IFACE, {"Value": Variant("ay", bytes(self.value))}, []]
            )
            self.bus.send(signal_msg)

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
        self.input_buffer = bytearray()

    async def on_write(self, data: bytes):
        if not self.ble_server:
            logger.error("BLE server not set")
            return

        self.input_buffer.extend(data)

        while b'{' in self.input_buffer and b'}' in self.input_buffer:
            start_idx = self.input_buffer.index(b'{')
            end_idx = self.input_buffer.index(b'}', start_idx) + 1
            packet = self.input_buffer[start_idx:end_idx]
            
            try:
                packet_str = packet.decode("utf-8")
                if self.ble_server.on_command_received:
                    await self.ble_server.on_command_received(packet_str)
            except UnicodeDecodeError as e:
                logger.error(f"Packet decode failed: {e}")
                self.input_buffer = bytearray()
                break
            except Exception as e:
                logger.error(f"Error processing packet: {e}")
            
            self.input_buffer = self.input_buffer[end_idx:]
        
        if len(self.input_buffer) > 1024:
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
            subprocess.call(["sudo", "hciconfig", "hci0", "class", "0x000100"])
            logger.info("BLE server started successfully")
        except Exception as e:
            logger.error(f"Start failed: {e}")
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
        except Exception as e:
            logger.error(f"Stop failed: {e}")

    async def _connect_dbus(self):
        try:
            self.bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
            result = await self.bus.request_name("org.eyedwell.BLEServer")
            if result == RequestNameReply.PRIMARY_OWNER:
                pass
            elif result == RequestNameReply.IN_QUEUE:
                raise Exception("D-Bus name queued, check for other instances")
            elif result == RequestNameReply.EXISTS:
                raise Exception("D-Bus name occupied, terminate other instances")
            elif result == RequestNameReply.ALREADY_OWNER:
                pass
            else:
                raise Exception(f"D-Bus name request failed: {result}")
        except Exception as e:
            logger.error(f"D-Bus connection failed: {e}")
            raise

    async def _setup_adapter(self):
        try:
            await self._set_property("Powered", Variant("b", True))
            await self._set_property("Alias", Variant("s", self.device_name))
            await self._set_property("Discoverable", Variant("b", True))
            await self._set_property("Pairable", Variant("b", True))
            await self._set_property("PairableTimeout", Variant("u", 0))
            await self._set_property("DiscoverableTimeout", Variant("u", 0))
        except Exception as e:
            logger.error(f"Adapter setup failed: {e}")
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
            logger.error(f"Set {prop_name} failed: {reply.body[0]}")

    async def _register_pairing_agent(self):
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
                raise Exception(f"Register agent failed: {reply.body[0]}")
            
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
                raise Exception(f"Set default agent failed: {reply.body[0]}")
            
        except Exception as e:
            logger.error(f"Register pairing agent error: {e}")
            raise

    async def _unregister_pairing_agent(self):
        if not self.bus or not self.pairing_agent:
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
            
            self.bus.unexport(self.pairing_agent.get_path())
            self.pairing_agent = None
            
        except Exception as e:
            logger.error(f"Unregister pairing agent error: {e}")

    async def _register_advertisement(self):
        if not self.bus:
            logger.error("D-Bus not connected, cannot register advertisement")
            return
        try:
            self.advertisement = Advertisement(0, self.device_name)
            self.bus.export(self.advertisement.get_path(), self.advertisement)
            
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
                raise Exception(f"Register advertisement failed: {reply.body[0]}")
        except Exception as e:
            logger.error(f"Register advertisement error: {e}")
            raise

    async def _unregister_advertisement(self):
        if not self.bus or not self.advertisement:
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
            
            self.bus.unexport(self.advertisement.get_path())
            self.advertisement = None
        except Exception as e:
            logger.error(f"Unregister advertisement error: {e}")

    async def _create_gatt_services(self):
        self.gatt_app = GattApplication(self.bus)
        service = EyeDwellGattService(self.bus)
        self.data_char = DataCharacteristic(self.bus, self)
        service.add_characteristic(CommandCharacteristic(self.bus, self))
        service.add_characteristic(self.data_char)
        self.gatt_app.add_service(service)
        
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

    async def _set_device_property(self, device_path: str, prop_name: str, value: Variant):
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
                logger.error(f"Set device {device_path} {prop_name} failed: {reply.body[0]}")
        except Exception as e:
            logger.error(f"Set device property error: {e}")

    async def send_data(self, data: bytes) -> bool:
        if not self.data_char:
            return False
        if len(data) > 500:
            data = data[:500]
        self.data_char.set_value(data)
        return True