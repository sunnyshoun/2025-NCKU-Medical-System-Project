import time
import dbus
import logging
import subprocess
from typing import List
from pulsectl import Pulse, PulseError
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
    """藍牙設備掃描器，支援連續掃描和設備列舉"""
    
    def __init__(self):
        self.bus = dbus.SystemBus()
        logger.info('BluetoothScanner initialized, starting scan')
        self.start()  # 自動啟動掃描
    
    def __del__(self):
        """在對象銷毀時自動停止掃描"""
        logger.info('BluetoothScanner being destroyed, stopping scan')
        try:
            self.stop()
        except BluetoothStopError as e:
            logger.error(f'Failed to stop scan during destruction: {e}')
    
    def _get_adapter_iface(self):
        """獲取藍牙適配器介面"""
        try:
            adapter = self.bus.get_object('org.bluez', '/org/bluez/hci0')
            return (
                dbus.Interface(adapter, 'org.bluez.Adapter1'),
                dbus.Interface(adapter, 'org.freedesktop.DBus.Properties')
            )
        except Exception as e:
            logger.error(f"Failed to get adapter interface: {e}")
            raise BluetoothStartError(f"Cannot access Bluetooth adapter: {e}")
    
    def start(self):
        """啟動藍牙掃描"""
        try:
            adapter_iface, props_iface = self._get_adapter_iface()
            if not props_iface.Get('org.bluez.Adapter1', 'Powered'):
                props_iface.Set('org.bluez.Adapter1', 'Powered', True)
                logger.info('Bluetooth adapter powered on')
            if not props_iface.Get('org.bluez.Adapter1', 'Discovering'):
                adapter_iface.StartDiscovery()
                logger.info('Bluetooth scan started')
        except Exception as e:
            logger.error(f"Failed to start Bluetooth scan: {e}")
            raise BluetoothStartError(f"Bluetooth scan start failed: {e}")
    
    def list_devices(self) -> List[Device]:
        """列出可連線的藍牙設備，排除名稱為 'Unknown' 的設備"""
        devices = []
        try:
            obj_mngr = self.bus.get_object('org.bluez', '/')
            objects = dbus.Interface(obj_mngr, 'org.freedesktop.DBus.ObjectManager').GetManagedObjects()
            
            for path, interfaces in objects.items():
                if 'org.bluez.Device1' not in interfaces:
                    continue
                props = interfaces['org.bluez.Device1']
                device_name = props.get('Name', 'Unknown')
                if device_name == 'Unknown':
                    continue
                
                is_paired = props.get('Paired', False)
                has_rssi = props.get('RSSI') is not None
                if not (is_paired or has_rssi):
                    continue
                
                device = Device(
                    device_name=device_name,
                    mac_address=props['Address'].replace(':', '_')
                )
                if device not in devices:
                    devices.append(device)
            logger.debug(f"Found {len(devices)} Bluetooth devices")
        except Exception as e:
            logger.error(f"Failed to list devices: {e}")
        
        return devices
    
    def stop(self):
        """停止藍牙掃描"""
        try:
            adapter_iface, props_iface = self._get_adapter_iface()
            if props_iface.Get('org.bluez.Adapter1', 'Discovering'):
                adapter_iface.StopDiscovery()
                logger.info('Bluetooth scan stopped')
            else:
                logger.debug('Bluetooth scan already stopped')
        except Exception as e:
            logger.error(f"Failed to stop Bluetooth scan: {e}")
            raise BluetoothStopError(f"Bluetooth scan stop failed: {e}")

bt_scanner = BluetoothScanner()

def list_devices() -> List[Device]:
    return bt_scanner.list_devices()

def verify_profile(card_name: str, expected_profile: str) -> bool:
    """驗證當前 profile 是否匹配預期"""
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

def connect_device(device: Device) -> bool:
    """連線設備、設定 HFP、設為預設輸入/輸出、應用音量並更新 config"""
    dev_path = f"/org/bluez/hci0/dev_{device.mac_address}"

    # 步驟 1: 配對並連線設備
    try:
        bus = dbus.SystemBus()
        dev = bus.get_object('org.bluez', dev_path)
        dev_iface = dbus.Interface(dev, 'org.bluez.Device1')
        props_iface = dbus.Interface(dev, 'org.freedesktop.DBus.Properties')

        if not props_iface.Get('org.bluez.Device1', 'Paired'):
            dev_iface.Pair(timeout=30000)
        dev_iface.Connect(timeout=30000)
        
        time.sleep(2)
        
        if not props_iface.Get('org.bluez.Device1', 'Connected'):
            logger.error(f"設備 {device.device_name} 未連線")
            return False
    except Exception as e:
        logger.error(f"連線 {device.device_name} 失敗: {e}")
        return False

    # 步驟 2: 檢查是否支援 HFP
    try:
        with Pulse('bluetooth-audio') as pulse:
            card_name = f"bluez_card.{device.mac_address}"
            card = None
            for _ in range(10):
                try:
                    card = pulse.get_card_by_name(card_name)
                    break
                except PulseError:
                    time.sleep(0.5)
            if not card:
                return False
            
            hfp_profile = next(
                (p for p in card.profile_list if any(term in p.name.lower() and "cvsd" not in p.name.lower() for term in ["headset", "handsfree"])),
                None
            )
            
            if not hfp_profile:
                return False
            
            pulse.card_profile_set(card, hfp_profile)
            time.sleep(1)
            
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
                    time.sleep(0.5)
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
    """設定預設設備音量並更新 config"""
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