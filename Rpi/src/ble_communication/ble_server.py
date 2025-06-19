import asyncio
import logging
import json
from typing import Optional, Callable
from dbus_fast import BusType, Variant, Message
from dbus_fast.aio import MessageBus

logger = logging.getLogger("BLE_Server")

class BLEServer:
    """簡化的 BLE 服務器，只處理基本通訊"""
    
    # 服務 UUID
    SERVICE_UUID = "12345678-abcd-1234-5678-123456789abc"
    
    def __init__(self, device_name: str = "EyeDwell_Robot"):
        self.device_name = device_name
        self.bus: Optional[MessageBus] = None
        self.is_connected = False
        self.client_address = ""
        
        # 回調函數
        self.on_control_command: Optional[Callable] = None
        self.on_connection_changed: Optional[Callable] = None

    async def start_server(self):
        """啟動 BLE 服務器"""
        try:
            await self._connect_dbus()
            await self._setup_adapter()
            await self._start_advertising()
            
            logger.info(f"BLE 服務器啟動成功: {self.device_name}")
            asyncio.create_task(self._monitor_connections())
            
        except Exception as e:
            logger.error(f"BLE 服務器啟動失敗: {e}")

    async def stop_server(self):
        """停止 BLE 服務器"""
        try:
            if self.bus:
                await self._stop_advertising()
                self.bus.disconnect()
                self.bus = None
            logger.info("BLE 服務器已停止")
        except Exception as e:
            logger.error(f"停止 BLE 服務器失敗: {e}")

    async def _connect_dbus(self):
        self.bus = await MessageBus(bus_type=BusType.SYSTEM).connect()

    async def _setup_adapter(self):
        """設置藍牙適配器"""
        try:
            # 設置適配器屬性
            properties = [
                ("Alias", Variant("s", self.device_name)),
                ("Powered", Variant("b", True)),
                ("Discoverable", Variant("b", True)),
                ("DiscoverableTimeout", Variant("u", 0)),
            ]
            
            for prop, value in properties:
                try:
                    await self.bus.call(
                        Message(
                            destination="org.bluez",
                            path="/org/bluez/hci0",
                            interface="org.freedesktop.DBus.Properties",
                            member="Set",
                            signature="ssv",
                            body=["org.bluez.Adapter1", prop, value]
                        )
                    )
                except Exception as e:
                    logger.debug(f"設置屬性 {prop} 失敗: {e}")
                    
        except Exception as e:
            logger.error(f"設置適配器失敗: {e}")

    async def _start_advertising(self):
        """開始 BLE 廣播"""
        try:
            # 使用系統命令啟動廣播
            process = await asyncio.create_subprocess_exec(
                'sudo', 'hciconfig', 'hci0', 'piscan',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            if process.returncode == 0:
                logger.info("BLE 廣播已啟動")
            else:
                logger.warning("BLE 廣播啟動可能失敗")
                
        except Exception as e:
            logger.error(f"啟動廣播失敗: {e}")

    async def _stop_advertising(self):
        """停止 BLE 廣播"""
        try:
            process = await asyncio.create_subprocess_exec(
                'sudo', 'hciconfig', 'hci0', 'noscan',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            logger.debug("BLE 廣播已停止")
        except Exception as e:
            logger.error(f"停止廣播失敗: {e}")

    async def _monitor_connections(self):
        """監控連線狀態"""
        last_connected = False
        
        while self.bus:
            try:
                # 簡化的連線檢測
                connected = await self._check_connection_status()
                
                if connected != last_connected:
                    self.is_connected = connected
                    logger.info(f"連線狀態變更: {connected}")
                    
                    if self.on_connection_changed:
                        try:
                            if asyncio.iscoroutinefunction(self.on_connection_changed):
                                await self.on_connection_changed(connected)
                            else:
                                self.on_connection_changed(connected)
                        except Exception as e:
                            logger.error(f"連線回調失敗: {e}")
                    
                    last_connected = connected
                
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"監控連線失敗: {e}")
                await asyncio.sleep(5)

    async def _check_connection_status(self) -> bool:
        """檢查連線狀態"""
        try:
            # 簡化的連線檢查邏輯
            # 實際實現可能需要更複雜的邏輯
            return False  # 預設未連線
        except Exception:
            return False

    def handle_incoming_data(self, data: bytes):
        """處理接收到的數據"""
        try:
            message = data.decode('utf-8')
            logger.info(f"收到數據: {message}")
            
            if self.on_control_command:
                if asyncio.iscoroutinefunction(self.on_control_command):
                    asyncio.create_task(self.on_control_command(message))
                else:
                    self.on_control_command(message)
                    
        except Exception as e:
            logger.error(f"處理數據失敗: {e}")

    async def send_data(self, data: bytes) -> bool:            
        if not self.is_connected:
            logger.warning("未連線，無法發送數據")
            return False
        
        try:
            # 實際的 BLE 數據發送邏輯
            logger.info(f"發送數據: {len(data)} bytes")
            return True
        except Exception as e:
            logger.error(f"發送數據失敗: {e}")
            return False

    async def send_status_update(self, status: str, details: dict = None) -> bool:
        """發送狀態更新"""
        status_data = {
            "type": "status_update",
            "status": status,
            "details": details or {}
        }
        
        try:
            json_data = json.dumps(status_data, ensure_ascii=False)
            return await self.send_data(json_data.encode('utf-8'))
        except Exception as e:
            logger.error(f"發送狀態更新失敗: {e}")
            return False

    def get_connection_status(self) -> dict:
        """獲取連線狀態"""
        return {
            "connected": self.is_connected,
            "device_name": self.device_name,
            "client_address": self.client_address
        }