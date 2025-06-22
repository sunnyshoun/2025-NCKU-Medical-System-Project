import asyncio
import subprocess
import time
import logging
from settings import *
from typing import List, Dict, Optional, Any
from dbus_fast import BusType, Message, MessageType, Variant
from dbus_fast.aio import MessageBus
from pulsectl import Pulse, PulseError
from .model import Device
from config_manager import load_config, save_config

logger = logging.getLogger("DeviceManager")
logger.setLevel(LOGGER_LEVEL)

class BluetoothConstants:
    ADAPTER_PATH = "/org/bluez/hci0"
    BLUEZ_SERVICE = "org.bluez"
    ADAPTER_INTERFACE = "org.bluez.Adapter1"
    DEVICE_INTERFACE = "org.bluez.Device1"
    PROPERTIES_INTERFACE = "org.freedesktop.DBus.Properties"
    OBJECT_MANAGER_INTERFACE = "org.freedesktop.DBus.ObjectManager"
    
    HEADSET_UUIDS = {
        '0000111e-0000-1000-8000-00805f9b34fb',  # HFP (Hands-Free Profile)
        '00001108-0000-1000-8000-00805f9b34fb',  # HSP (Headset Profile)  
        '0000110d-0000-1000-8000-00805f9b34fb',  # A2DP (Advanced Audio Distribution Profile)
        '0000110b-0000-1000-8000-00805f9b34fb',  # Audio Sink
        '0000110a-0000-1000-8000-00805f9b34fb',  # Audio Source
    }
    
    HEADSET_DEVICE_CLASSES = {
        0x040404,  # Audio/Video - Headphones
        0x040408,  # Audio/Video - Microphone
        0x040414,  # Audio/Video - Headset
        0x040418,  # Audio/Video - Hands-free
        0x240404,  # 有些設備可能使用這個類別
        0x240408,  # 有些設備可能使用這個類別
    }
    
    HEADSET_KEYWORDS = [
        'headphone', 'headset', 'earphone', 'earbud', 'airpod', 
        'beats', 'sony', 'bose', 'sennheiser', 'audio', 'wireless',
        'buds', 'pods'
    ]
    
    DISCOVERY_TIMEOUT = 10
    PROPERTY_CHANGE_TIMEOUT = 5.0
    CARD_WAIT_TIMEOUT = 15
    RETRY_ATTEMPTS = 3

class VariantHelper:
    @staticmethod
    def extract_value(variant: Any, default: Any = None) -> Any:
        if isinstance(variant, Variant):
            return variant.value
        return variant if variant is not None else default
    
    @staticmethod
    def extract_string(variant: Any, default: str = "") -> str:
        return str(VariantHelper.extract_value(variant, default))
    
    @staticmethod
    def extract_bool(variant: Any, default: bool = False) -> bool:
        return bool(VariantHelper.extract_value(variant, default))
    
    @staticmethod
    def extract_list(variant: Any, default: list = None) -> list:
        if default is None:
            default = []
        value = VariantHelper.extract_value(variant, default)
        return value if isinstance(value, list) else default

class PulseAudioManager:
    @staticmethod
    def get_card_by_name(card_name: str):
        try:
            with Pulse('bluetooth-audio') as pulse:
                return pulse.get_card_by_name(card_name)
        except PulseError:
            return None
        except Exception as e:
            logger.error(f"Get card failed: {e}")
            return None
    
    @staticmethod
    def set_card_profile(card_name: str, profile_name: str) -> bool:
        try:
            with Pulse('bluetooth-audio') as pulse:
                card = pulse.get_card_by_name(card_name)
                if not card:
                    logger.error(f"Card not found: {card_name}")
                    return False
                
                target_profile = next(
                    (p for p in card.profile_list if p.name == profile_name), 
                    None
                )
                
                if not target_profile:
                    logger.error(f"Profile not found: {profile_name}")
                    return False
                
                pulse.card_profile_set(card, target_profile)
                return True
                
        except PulseError as e:
            logger.error(f"Set profile failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Set profile failed: {e}")
            return False
    
    @staticmethod
    def set_default_sink(sink_name: str) -> bool:
        try:
            with Pulse('bluetooth-audio') as pulse:
                sink = pulse.get_sink_by_name(sink_name)
                if not sink:
                    logger.error(f"Sink not found: {sink_name}")
                    return False
                pulse.sink_default_set(sink)
                return True
                
        except PulseError as e:
            logger.error(f"Set default sink failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Set default sink failed: {e}")
            return False
    
    @staticmethod
    def set_default_source(source_name: str) -> bool:
        try:
            with Pulse('bluetooth-audio') as pulse:
                source = pulse.get_source_by_name(source_name)
                if not source:
                    logger.error(f"Source not found: {source_name}")
                    return False
                pulse.source_default_set(source)
                return True
                
        except PulseError as e:
            logger.error(f"Set default source failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Set default source failed: {e}")
            return False
    
    @staticmethod
    def set_sink_volume(sink_name: str, volume: float) -> bool:
        try:
            with Pulse('volume-setter') as pulse:
                sink = pulse.get_sink_by_name(sink_name)
                if not sink:
                    logger.error(f"Sink not found: {sink_name}")
                    return False
                pulse.volume_set_all_chans(sink, volume)
                return True
                
        except PulseError as e:
            logger.error(f"Set volume failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Set volume failed: {e}")
            return False

class BluetoothInterfaceAsync:
    def __init__(self):
        self.bus = None
        self.devices: Dict[str, Dict] = {}
    
    async def connect(self) -> None:
        if not self.bus:
            self.bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    
    async def disconnect(self) -> None:
        if self.bus:
            await self.bus.disconnect()
            self.bus = None
    
    async def start_discover(self) -> bool:
        try:
            reply = await self.bus.call(
                Message(
                    destination=BluetoothConstants.BLUEZ_SERVICE,
                    path=BluetoothConstants.ADAPTER_PATH,
                    interface=BluetoothConstants.ADAPTER_INTERFACE,
                    member="StartDiscovery"
                )
            )
            return reply.message_type == MessageType.METHOD_RETURN
        except Exception as e:
            logger.error(f"Start discovery failed: {e}")
            return False
    
    async def stop_discover(self) -> bool:
        try:
            reply = await self.bus.call(
                Message(
                    destination=BluetoothConstants.BLUEZ_SERVICE,
                    path=BluetoothConstants.ADAPTER_PATH,
                    interface=BluetoothConstants.ADAPTER_INTERFACE,
                    member="StopDiscovery"
                )
            )
            return reply.message_type == MessageType.METHOD_RETURN
        except Exception as e:
            logger.error(f"Stop discovery failed: {e}")
            return False
    
    def _is_headset_device(self, device_props: Dict) -> bool:
        device_class = VariantHelper.extract_value(device_props.get("Class", 0))
        class_match = device_class in BluetoothConstants.HEADSET_DEVICE_CLASSES
        
        uuids = VariantHelper.extract_list(device_props.get("UUIDs", []))
        uuid_match = any(
            uuid.lower() in BluetoothConstants.HEADSET_UUIDS 
            for uuid in uuids
        )
        
        name = VariantHelper.extract_string(device_props.get("Name", ""))
        alias = VariantHelper.extract_string(device_props.get("Alias", ""))
        device_name_lower = (name + ' ' + alias).lower()
        name_match = any(
            keyword in device_name_lower 
            for keyword in BluetoothConstants.HEADSET_KEYWORDS
        )
        
        icon = VariantHelper.extract_string(device_props.get("Icon", ""))
        icon_match = 'audio' in icon.lower()
        
        return class_match or uuid_match or name_match or icon_match
    
    async def list_devices(self) -> List[Device]:
        try:
            reply = await self.bus.call(
                Message(
                    destination=BluetoothConstants.BLUEZ_SERVICE,
                    path="/",
                    interface=BluetoothConstants.OBJECT_MANAGER_INTERFACE,
                    member="GetManagedObjects"
                )
            )
            
            devices = []
            if reply.message_type != MessageType.METHOD_RETURN:
                return devices
            
            objects = reply.body[0]
            for path, interfaces in objects.items():
                if BluetoothConstants.DEVICE_INTERFACE not in interfaces:
                    continue
                
                device_props = interfaces[BluetoothConstants.DEVICE_INTERFACE]
                
                if not self._is_headset_device(device_props):
                    continue
                
                name = VariantHelper.extract_string(device_props.get("Name", "Unknown"))
                address = VariantHelper.extract_string(device_props.get("Address", ""))
                
                devices.append(Device(
                    device_name=name,
                    mac_address=address.replace(':', '_')
                ))
            
            return devices
            
        except Exception as e:
            logger.error(f"List devices failed: {e}")
            return []
    
    async def _get_property(self, path: str, interface: str, property_name: str) -> Optional[Variant]:
        try:
            reply = await self.bus.call(
                Message(
                    destination=BluetoothConstants.BLUEZ_SERVICE,
                    path=path,
                    interface=BluetoothConstants.PROPERTIES_INTERFACE,
                    member="Get",
                    signature="ss",
                    body=[interface, property_name]
                )
            )
            return reply.body[0] if reply.message_type == MessageType.METHOD_RETURN else None
        except Exception as e:
            logger.error(f"Get property {property_name} failed: {e}")
            return None
    
    async def _wait_for_property_change(self, path: str, property_name: str, 
                                      expected_value: Any, timeout: float = 5.0) -> bool:
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            prop = await self._get_property(path, BluetoothConstants.DEVICE_INTERFACE, property_name)
            if prop and VariantHelper.extract_value(prop) == expected_value:
                return True
            await asyncio.sleep(0.2)
        
        return False
    
    async def _pair_device(self, device_path: str, device_name: str) -> bool:
        try:
            paired_prop = await self._get_property(
                device_path, BluetoothConstants.DEVICE_INTERFACE, "Paired"
            )
            if paired_prop and VariantHelper.extract_bool(paired_prop):
                return True
            
            pair_reply = await self.bus.call(
                Message(
                    destination=BluetoothConstants.BLUEZ_SERVICE,
                    path=device_path,
                    interface=BluetoothConstants.DEVICE_INTERFACE,
                    member="Pair"
                )
            )
            
            if pair_reply.message_type == MessageType.ERROR:
                error_name = pair_reply.error_name
                if error_name == "org.bluez.Error.AlreadyExists":
                    return True
                else:
                    logger.error(f"Pair {device_name} failed: {error_name}")
                    return False
            
            await self._wait_for_property_change(
                device_path, "Paired", True, 
                timeout=BluetoothConstants.DISCOVERY_TIMEOUT
            )
            return True
            
        except Exception as e:
            logger.error(f"Pair {device_name} failed: {e}")
            return False
    
    async def _connect_bluetooth_device(self, device_path: str, device_name: str) -> bool:
        try:
            reply = await self.bus.call(
                Message(
                    destination=BluetoothConstants.BLUEZ_SERVICE,
                    path=device_path,
                    interface=BluetoothConstants.DEVICE_INTERFACE,
                    member="Connect"
                )
            )
            
            if reply.message_type == MessageType.METHOD_RETURN:
                connected_prop = await self._get_property(
                    device_path, BluetoothConstants.DEVICE_INTERFACE, "Connected"
                )
                if connected_prop and VariantHelper.extract_bool(connected_prop):
                    return True
            
            logger.error(f"Device {device_name} connection failed")
            return False
            
        except Exception as e:
            logger.error(f"Connect {device_name} failed: {e}")
            return False
    
    async def _wait_for_pulseaudio_card(self, card_name: str, timeout: int = 15):
        for attempt in range(timeout * 2):
            card = PulseAudioManager.get_card_by_name(card_name)
            if card:
                return card
            await asyncio.sleep(0.5)
        
        logger.error(f"Wait for PulseAudio card {card_name} timeout")
        return None
    
    def _find_best_hfp_profile(self, card):
        profile_terms = ["headset", "handsfree"]
        
        for profile in card.profile_list:
            profile_name_lower = profile.name.lower()
            if (any(term in profile_name_lower for term in profile_terms) 
                and "cvsd" not in profile_name_lower):
                return profile
        
        return None
    
    async def _setup_audio_profile(self, device: Device) -> bool:
        try:
            card_name = f"bluez_card.{device.mac_address}"
            
            card = await self._wait_for_pulseaudio_card(card_name)
            if not card:
                return False
            
            hfp_profile = self._find_best_hfp_profile(card)
            if not hfp_profile:
                logger.error(f"Device {device.device_name} no supported HFP profile")
                return False
            
            if not PulseAudioManager.set_card_profile(card_name, hfp_profile.name):
                return False
            
            await asyncio.sleep(1)
            
            if not await self.verify_profile(card_name, hfp_profile.name):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Setup HFP for {device.device_name} failed: {e}")
            return False
    
    async def _setup_default_audio_devices(self, device: Device) -> bool:
        sink_name = f"bluez_output.{device.mac_address.replace(':', '_')}.1"
        source_name = f"bluez_input.{device.mac_address.replace(':', '_')}.0"
        
        for attempt in range(BluetoothConstants.RETRY_ATTEMPTS):
            try:
                sink_success = PulseAudioManager.set_default_sink(sink_name)
                source_success = PulseAudioManager.set_default_source(source_name)
                
                if sink_success and source_success:
                    return True
                
            except Exception:
                pass
            
            await asyncio.sleep(0.5)
        
        logger.error(f"Sink/source not found: {sink_name}/{source_name}")
        return False
    
    def _update_device_config(self, device: Device) -> None:
        try:
            config = load_config()
            config["HEADPHONE_DEVICE_MAC"] = device.mac_address
            save_config(config)
        except Exception as e:
            logger.error(f"Update config failed: {e}")
    
    async def _apply_device_volume(self) -> bool:
        try:
            config = load_config()
            volume = config.get("VOLUME", 50)
            return await self.set_device_volume(volume)
        except Exception as e:
            logger.error(f"Apply volume failed: {e}")
            return False
    
    async def verify_profile(self, card_name: str, expected_profile: str) -> bool:
        try:
            output = subprocess.check_output(["pactl", "list", "cards"], text=True)
            lines = iter(output.splitlines())
            
            for line in lines:
                if f"Name: {card_name}" in line:
                    for next_line in lines:
                        if "Active Profile:" in next_line:
                            current_profile = next_line.split("Active Profile:")[1].strip()
                            return current_profile == expected_profile
            return False
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Verify profile failed: {e}")
            return False
    
    async def connect_device(self, device: Device) -> bool:
        device_path = f"/org/bluez/hci0/dev_{device.mac_address}"
        
        paired_prop = await self._get_property(
            device_path, BluetoothConstants.DEVICE_INTERFACE, "Paired"
        )
        if paired_prop is None:
            logger.error(f"Device {device.device_name} not exist or accessible")
            return False
        
        if not await self._pair_device(device_path, device.device_name):
            return False
        
        if not await self._connect_bluetooth_device(device_path, device.device_name):
            return False
        
        if not await self._setup_audio_profile(device):
            return False
        
        if not await self._setup_default_audio_devices(device):
            return False
        
        self._update_device_config(device)
        
        if not await self._apply_device_volume():
            logger.warning(f"Set volume failed for {device.device_name}")
        
        return True
    
    async def set_device_volume(self, volume: int) -> bool:
        try:
            volume = int(volume)
            if not 0 <= volume <= 100:
                logger.warning("Volume must be 0~100")
                return False
            
            config = load_config()
            mac = config.get("HEADPHONE_DEVICE_MAC")
            if not mac:
                logger.warning("HEADPHONE_DEVICE_MAC not set")
                return False
            
            sink_name = f"bluez_output.{mac.replace(':', '_')}.1"
            if PulseAudioManager.set_sink_volume(sink_name, volume / 100.0):
                config["VOLUME"] = volume
                save_config(config)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Set volume failed: {e}")
            return False

bt_interface = None

async def get_bt_interface():
    global bt_interface
    if bt_interface is None:
        bt_interface = BluetoothInterfaceAsync()
        await bt_interface.connect()
        await bt_interface.start_discover()
    return bt_interface