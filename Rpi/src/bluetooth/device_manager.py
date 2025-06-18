import asyncio
import logging
import subprocess
from typing import List
from pulsectl import Pulse, PulseError
from dbus_fast import BusType, Message
from dbus_fast.aio import MessageBus
from config_manager import load_config, save_config
from .model import Device

logger = logging.getLogger('deviceManager')

# 新增自定義異常類
class BluetoothStartError(Exception):
    """拋出當藍牙掃描啟動失敗時"""
    pass

class BluetoothStopError(Exception):
    """拋出當藍牙掃描停止失敗時"""
    pass

class BluetoothScanner:
    """藍牙設備掃描器，支援連續掃描和設備列舉 (dbus-fast異步版本)"""
    
    def __init__(self):
        self.bus = None
        self._loop = None
        logger.info('BluetoothScanner initialized')
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        await self._ensure_bus()
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        await self.stop()
        if self.bus:
            self.bus.disconnect()
    
    async def _ensure_bus(self):
        """確保 D-Bus 連接已建立"""
        if self.bus is None:
            try:
                self.bus = MessageBus(bus_type=BusType.SYSTEM)
                await self.bus.connect()
                logger.info('Connected to system D-Bus')
            except Exception as e:
                logger.error(f"Failed to connect to D-Bus: {e}")
                raise BluetoothStartError(f"Cannot connect to D-Bus: {e}")
    
    async def _get_adapter_properties(self):
        """獲取藍牙適配器屬性介面"""
        try:
            await self._ensure_bus()
            introspection = await self.bus.introspect('org.bluez', '/org/bluez/hci0')
            obj = self.bus.get_proxy_object('org.bluez', '/org/bluez/hci0', introspection)
            adapter_iface = obj.get_interface('org.bluez.Adapter1')
            props_iface = obj.get_interface('org.freedesktop.DBus.Properties')
            return adapter_iface, props_iface
        except Exception as e:
            logger.error(f"Failed to get adapter interface: {e}")
            raise BluetoothStartError(f"Cannot access Bluetooth adapter: {e}")
    
    async def start(self):
        """啟動藍牙掃描"""
        try:
            adapter_iface, props_iface = await self._get_adapter_properties()
            
            # 檢查並開啟藍牙適配器
            powered = await props_iface.call_get('org.bluez.Adapter1', 'Powered')
            if not powered.value:
                await props_iface.call_set('org.bluez.Adapter1', 'Powered', True)
                logger.info('Bluetooth adapter powered on')
            
            # 檢查並開始掃描
            discovering = await props_iface.call_get('org.bluez.Adapter1', 'Discovering')
            if not discovering.value:
                await adapter_iface.call_start_discovery()
                logger.info('Bluetooth scan started')
                
        except Exception as e:
            logger.error(f"Failed to start Bluetooth scan: {e}")
            raise BluetoothStartError(f"Bluetooth scan start failed: {e}")
    
    async def list_devices(self) -> List[Device]:
        """列出可連線的藍牙設備，排除名稱為 'Unknown' 的設備"""
        devices = []
        try:
            await self._ensure_bus()
            
            # 獲取 ObjectManager
            introspection = await self.bus.introspect('org.bluez', '/')
            obj_manager = self.bus.get_proxy_object('org.bluez', '/', introspection)
            obj_manager_iface = obj_manager.get_interface('org.freedesktop.DBus.ObjectManager')
            
            # 獲取所有管理的對象
            managed_objects = await obj_manager_iface.call_get_managed_objects()
            
            for path, interfaces in managed_objects.value.items():
                if 'org.bluez.Device1' not in interfaces:
                    continue
                    
                props = interfaces['org.bluez.Device1']
                device_name = props.get('Name', 'Unknown').value if 'Name' in props else 'Unknown'
                
                if device_name == 'Unknown':
                    continue
                
                is_paired = props.get('Paired', False).value if 'Paired' in props else False
                has_rssi = 'RSSI' in props
                
                if not (is_paired or has_rssi):
                    continue
                
                address = props['Address'].value if 'Address' in props else ''
                device = Device(
                    device_name=device_name,
                    mac_address=address.replace(':', '_')
                )
                
                if device not in devices:
                    devices.append(device)
                    
            logger.debug(f"Found {len(devices)} Bluetooth devices")
            
        except Exception as e:
            logger.error(f"Failed to list devices: {e}")
        
        return devices
    
    async def stop(self):
        """停止藍牙掃描"""
        try:
            adapter_iface, props_iface = await self._get_adapter_properties()
            discovering = await props_iface.call_get('org.bluez.Adapter1', 'Discovering')
            
            if discovering.value:
                await adapter_iface.call_stop_discovery()
                logger.info('Bluetooth scan stopped')
            else:
                logger.debug('Bluetooth scan already stopped')
                
        except Exception as e:
            logger.error(f"Failed to stop Bluetooth scan: {e}")
            raise BluetoothStopError(f"Bluetooth scan stop failed: {e}")

# 全局掃描器實例
_bt_scanner = None

async def get_scanner():
    """獲取或創建掃描器實例"""
    global _bt_scanner
    if _bt_scanner is None:
        _bt_scanner = BluetoothScanner()
        await _bt_scanner._ensure_bus()
        await _bt_scanner.start()
    return _bt_scanner

async def list_devices() -> List[Device]:
    """異步列出設備"""
    scanner = await get_scanner()
    return await scanner.list_devices()

def verify_profile(card_name: str, expected_profile: str) -> bool:
    """驗證當前 profile 是否匹配預期 (同步函數保持不變)"""
    try:
        output = subprocess.check_output(["pactl", "list", "cards"], text=True)
        lines = iter(output.splitlines())
        for line in lines:
            if f"Name: {card_name}" in line:
                for next_line in lines:
                    if "Active Profile:" in next_line:
                        return next_line.split("Active Profile:")[1].strip() == expected_profile
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"驗證 profile 失敗: {e}")
        return False

async def connect_device(device: Device) -> bool:
    """連線設備、設定 HFP、設為預設輸入/輸出、應用音量並更新 config"""
    dev_path = f"/org/bluez/hci0/dev_{device.mac_address}"

    # 步驟 1: 配對並連線設備
    try:
        scanner = await get_scanner()
        await scanner._ensure_bus()
        
        # 獲取設備對象
        introspection = await scanner.bus.introspect('org.bluez', dev_path)
        dev_obj = scanner.bus.get_proxy_object('org.bluez', dev_path, introspection)
        dev_iface = dev_obj.get_interface('org.bluez.Device1')
        props_iface = dev_obj.get_interface('org.freedesktop.DBus.Properties')

        # 檢查是否已配對
        paired = await props_iface.call_get('org.bluez.Device1', 'Paired')
        if not paired.value:
            await dev_iface.call_pair()
            
        # 連接設備
        await dev_iface.call_connect()
        
        # 等待連接完成
        await asyncio.sleep(2)
        
        # 檢查連接狀態
        connected = await props_iface.call_get('org.bluez.Device1', 'Connected')
        if not connected.value:
            logger.error(f"設備 {device.device_name} 未連線")
            return False
            
    except Exception as e:
        logger.error(f"連線 {device.device_name} 失敗: {e}")
        return False

    # 步驟 2: 檢查是否支援 HFP (同步部分保持不變)
    try:
        with Pulse('bluetooth-audio') as pulse:
            card_name = f"bluez_card.{device.mac_address}"
            card = None
            for _ in range(10):
                try:
                    card = pulse.get_card_by_name(card_name)
                    break
                except PulseError:
                    await asyncio.sleep(0.5)
            if not card:
                return False
            
            hfp_profile = next(
                (p for p in card.profile_list if any(term in p.name.lower() and "cvsd" not in p.name.lower() for term in ["headset", "handsfree"])),
                None
            )
            
            if not hfp_profile:
                return False
            
            pulse.card_profile_set(card, hfp_profile)
            await asyncio.sleep(1)
            
            if not verify_profile(card_name, hfp_profile.name):
                logger.error(f"HFP profile 未設定為 {hfp_profile.name}")
                return False

            sink_name = f"bluez_output.{device.mac_address}.1"
            source_name = f"bluez_input.{device.mac_address}.0"
            sink = source = None
            for _ in range(3):
                try:
                    sink = pulse.get_sink_by_name(sink_name)
                    source = pulse.get_source_by_name(source_name)
                    break
                except PulseError:
                    await asyncio.sleep(0.5)
            if not (sink and source):
                logger.error(f"未找到 sink/source: {sink_name}/{source_name}")
                return False

            pulse.sink_default_set(sink)
            pulse.source_default_set(source)
    except Exception as e:
        logger.error(f"設定 HFP for {device.device_name} 失敗: {e}")
        return False

    # 步驟 3: 更新 config
    config = load_config()
    config["HEADPHONE_DEVICE_MAC"] = device.mac_address
    save_config(config)

    # 步驟 4: 應用音量（僅對音訊設備）
    try:
        if hfp_profile:
            volume = config.get("VOLUME", 50)
            if not set_device_volume(volume):
                logger.error(f"設定音量失敗 for {device.device_name}")
                return False
    except ValueError as e:
        logger.error(f"無效音量值: {e}")
        return False

    return True

def set_device_volume(volume: int) -> bool:
    """設定預設設備音量並更新 config (同步函數保持不變)"""
    volume = int(volume)
    if not 0 <= volume <= 100:
        logger.warning("音量需在 0~100")
        return False

    config = load_config()
    mac = config.get("HEADPHONE_DEVICE_MAC")
    if not mac:
        logger.warning("未設定 HEADPHONE_DEVICE_MAC")
        return False

    try:
        with Pulse('volume-setter') as pulse:
            sink = pulse.get_sink_by_name(f"bluez_output.{mac}.1")
            pulse.volume_set_all_chans(sink, volume / 100.0)
            config["VOLUME"] = volume
            save_config(config)
            return True
    except PulseError as e:
        logger.error(f"設定音量失敗: {e}")
        return False

# 同步包裝器函數，用於保持向後兼容性
def run_async(coro):
    """運行異步函數的同步包裝器"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        # 如果事件循環已在運行，創建任務
        return asyncio.create_task(coro)
    else:
        # 如果事件循環未運行，直接運行
        return loop.run_until_complete(coro)

# 為向後兼容性提供的同步包裝器
def list_devices_sync() -> List[Device]:
    """同步版本的 list_devices"""
    return run_async(list_devices())

def connect_device_sync(device: Device) -> bool:
    """同步版本的 connect_device"""
    return run_async(connect_device(device))

# 舊的全局變量保持兼容性
class LegacyBluetoothScanner:
    """為了向後兼容而提供的同步包裝類"""
    
    def list_devices(self) -> List[Device]:
        return list_devices_sync()

bt_scanner = LegacyBluetoothScanner()