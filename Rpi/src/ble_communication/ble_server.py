import asyncio
import logging
import json
import os
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

class SimpleBLEServer:
    CUSTOM_SERVICE_UUID = "12345678-1234-5678-9abc-def012345678"
    CONTROL_CHAR_UUID = "12345678-1234-1234-1234-123456789ab1"
    DATA_CHAR_UUID = "12345678-1234-1234-1234-123456789ab2"
    FILE_CHAR_UUID = "12345678-1234-1234-1234-123456789ab3"
    STATUS_CHAR_UUID = "12345678-1234-1234-1234-123456789ab4"

    def __init__(self, device_name: str = "MyBLEDevice"):
        self.device_name = device_name
        self.bus: Optional[MessageBus] = None
        self.is_connected = False
        self.client_address = ""
        
        self.app_path = "/org/example/gatt"
        self.service_path = f"{self.app_path}/service0"
        
        self.characteristics_data = {
            self.CONTROL_CHAR_UUID: {'value': b'', 'flags': ['write', 'write-without-response']},
            self.DATA_CHAR_UUID: {'value': b'Ready', 'flags': ['read', 'write', 'notify']},
            self.FILE_CHAR_UUID: {'value': b'', 'flags': ['write', 'write-without-response']},
            self.STATUS_CHAR_UUID: {'value': b'{}', 'flags': ['read', 'notify']},
        }
        
        self.on_control_command: Optional[Callable[[str], None]] = None
        self.on_data_received: Optional[Callable[[bytes], None]] = None
        self.on_file_received: Optional[Callable[[bytes], None]] = None
        self.on_connection_changed: Optional[Callable[[bool], None]] = None
        
        self._file_buffer = bytearray()
        self._expected_file_size = 0
        self._transfer_active = False

    async def start_server(self):
        try:
            if os.getuid() != 0:
                logger.warning("Running without root privileges. Try: sudo python3 script.py")
            
            await self._connect_dbus()
            await self._setup_adapter()
            await self._register_advertisement()
            
            logger.info(f"BLE server started: {self.device_name}")
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
            ("Appearance", Variant("q", 0x0080)),
            ("Class", Variant("u", 0x000100)),
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
            await asyncio.create_subprocess_exec('hciconfig', 'hci0', 'up')
            await asyncio.sleep(0.5)
            await asyncio.create_subprocess_exec('hciconfig', 'hci0', 'piscan')
            await asyncio.sleep(0.5)
            await asyncio.create_subprocess_exec('hciconfig', 'hci0', 'leadv')
            logger.info("Advertisement registered")
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
                    logger.info(f"Connection: {connected}")
                    
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
        try:
            command = data.decode('utf-8', errors='ignore')
            logger.info(f"Control command: {command}")
            
            self.characteristics_data[self.CONTROL_CHAR_UUID]['value'] = data
            
            if self.on_control_command:
                if asyncio.iscoroutinefunction(self.on_control_command):
                    asyncio.create_task(self.on_control_command(command))
                else:
                    self.on_control_command(command)
        except Exception as e:
            logger.error(f"Error handling control command: {e}")

    def handle_data_received(self, data: bytes):
        try:
            logger.info(f"Data received: {len(data)} bytes")
            self.characteristics_data[self.DATA_CHAR_UUID]['value'] = data
            
            if self.on_data_received:
                if asyncio.iscoroutinefunction(self.on_data_received):
                    asyncio.create_task(self.on_data_received(data))
                else:
                    self.on_data_received(data)
        except Exception as e:
            logger.error(f"Error handling data: {e}")

    def handle_file_transfer(self, data: bytes):
        try:
            if not self._transfer_active:
                if len(data) >= 4:
                    self._expected_file_size = int.from_bytes(data[:4], 'big')
                    self._file_buffer = bytearray(data[4:])
                    self._transfer_active = True
                    logger.info(f"File transfer started: {self._expected_file_size} bytes")
                else:
                    logger.warning("Invalid file transfer start")
                    return
            else:
                self._file_buffer.extend(data)
                
            if len(self._file_buffer) >= self._expected_file_size:
                file_data = bytes(self._file_buffer[:self._expected_file_size])
                logger.info(f"File transfer completed: {len(file_data)} bytes")
                
                if self.on_file_received:
                    if asyncio.iscoroutinefunction(self.on_file_received):
                        asyncio.create_task(self.on_file_received(file_data))
                    else:
                        self.on_file_received(file_data)
                
                self._file_buffer.clear()
                self._expected_file_size = 0
                self._transfer_active = False
                
        except Exception as e:
            logger.error(f"Error handling file transfer: {e}")
            self._transfer_active = False

    async def send_data(self, data: bytes) -> bool:
        if not self.is_connected:
            logger.warning("Cannot send data: no client connected")
            return False
        
        try:
            self.characteristics_data[self.DATA_CHAR_UUID]['value'] = data
            logger.info(f"Data prepared: {len(data)} bytes")
            return True
        except Exception as e:
            logger.error(f"Error sending data: {e}")
            return False

    async def send_file(self, file_data: bytes) -> bool:
        if not self.is_connected:
            logger.warning("Cannot send file: no client connected")
            return False
        
        try:
            size_header = len(file_data).to_bytes(4, 'big')
            full_data = size_header + file_data
            self.characteristics_data[self.FILE_CHAR_UUID]['value'] = full_data
            logger.info(f"File prepared: {len(file_data)} bytes")
            return True
        except Exception as e:
            logger.error(f"Error sending file: {e}")
            return False

    def get_status(self) -> dict:
        return {
            "connected": self.is_connected,
            "device_name": self.device_name,
            "client_address": self.client_address,
            "transfer_active": self._transfer_active,
            "timestamp": asyncio.get_event_loop().time()
        }

async def main():
    def on_control_command(command: str):
        logger.info(f"Command: {command}")
        commands = {
            "start_test": "Starting vision test...",
            "stop_test": "Stopping test",
            "calibrate": "Calibrating device...",
            "get_results": "Preparing results",
            "ping": "Device responds: PONG"
        }
        logger.info(commands.get(command.lower(), f"Unknown command: {command}"))
    
    def on_data_received(data: bytes):
        logger.info(f"Data received: {len(data)} bytes")
        try:
            text = data.decode('utf-8', errors='ignore')
            if text.startswith('{'):
                params = json.loads(text)
                logger.info(f"Parameters: {params}")
            else:
                logger.info(f"Text: {text}")
        except:
            logger.info(f"Binary data: {data.hex()}")
    
    def on_file_received(file_data: bytes):
        logger.info(f"File received: {len(file_data)} bytes")
        try:
            if file_data.startswith(b'{'):
                config = json.loads(file_data.decode('utf-8'))
                filename = f"config_{int(asyncio.get_event_loop().time())}.json"
                logger.info(f"Config for patient: {config.get('patient_id', 'unknown')}")
            elif file_data.startswith(b'%PDF'):
                filename = f"report_{int(asyncio.get_event_loop().time())}.pdf"
                logger.info("PDF report received")
            else:
                filename = f"file_{int(asyncio.get_event_loop().time())}.bin"
                logger.info("Unknown file type")
            
            with open(filename, "wb") as f:
                f.write(file_data)
            logger.info(f"File saved: {filename}")
            
        except Exception as e:
            logger.error(f"File processing error: {e}")
    
    def on_connection_changed(connected: bool):
        status = "connected" if connected else "disconnected"
        logger.info(f"Device {status}")
    
    robot = SimpleBLEServer("EyeDwell")
    robot.on_control_command = on_control_command
    robot.on_data_received = on_data_received
    robot.on_file_received = on_file_received
    robot.on_connection_changed = on_connection_changed
    
    try:
        logger.info("Starting EyeDwell BLE server...")
        await robot.start_server()
        
        heartbeat_counter = 0
        while True:
            await asyncio.sleep(20)
            
            if robot.is_connected:
                status_update = {
                    "type": "vision_robot",
                    "status": "ready"
                }
                await robot.send_data(json.dumps(status_update).encode('utf-8'))
                heartbeat_counter += 1
                
                if heartbeat_counter % 5 == 0:
                    test_result = {
                        "test_id": f"VT_{int(asyncio.get_event_loop().time())}",
                        "left_eye": {"acuity": "20/20", "score": 95},
                        "right_eye": {"acuity": "20/25", "score": 92},
                        "timestamp": asyncio.get_event_loop().time(),
                        "device": "EyeDwell"
                    }
                    await robot.send_data(json.dumps(test_result).encode('utf-8'))
                    logger.info("Test result sent")
            else:
                pass
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await robot.stop_server()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())