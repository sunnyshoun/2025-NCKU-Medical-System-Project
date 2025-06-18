from settings import *
from .models import IAudio, IBluetooth, ISttAPI
from audio.recognizer import recognize_direct
from audio.language_detection import detect_language
from audio.player import audio_player
from audio.model import Language
from bluetooth.device_manager import list_devices_sync, connect_device_sync, set_device_volume
from bluetooth.model import Device
from config_manager import get_config_value
import logging

_LOGGER = logging.getLogger('Resource')
    
class Audio(IAudio):
    def play_async(self, file_name: str, language: str, wait_time: int = 0) -> None:
        return audio_player.play_async(file_name, language)
    
    def set_volume(self, volume: int) -> bool:
        return set_device_volume(volume)
    
    def get_volume(self) -> int:
        r = get_config_value('VOLUME')
        if type(r) is int:
            _LOGGER.debug(f'Get volume: {r}%')
            return r
        else:
            _LOGGER.warning('Cannot get volume')
            return -1
    
class Bluetooth(IBluetooth):
    """藍牙設備管理類，使用 dbus-fast 後端"""

    def __init__(self) -> None:
        self.bt_device = None
        _LOGGER.info('Bluetooth resource initialized with dbus-fast backend')

    def list_bt_device(self):
        """列出藍牙設備 (同步接口)"""
        try:
            devices = list_devices_sync()
            _LOGGER.debug(f'Found {len(devices)} bluetooth devices')
            return devices
        except Exception as e:
            _LOGGER.error(f'Failed to list bluetooth devices: {e}')
            return []
    
    def connect_bt_device(self, device: Device):
        """連接藍牙設備 (同步接口)"""
        try:
            _LOGGER.info(f'Attempting to connect to device: {device.device_name}')
            success = connect_device_sync(device)
            if success:
                self.bt_device = device
                _LOGGER.info(f'Successfully connected to {device.device_name}')
            else:
                _LOGGER.warning(f'Failed to connect to {device.device_name}')
            return success
        except Exception as e:
            _LOGGER.error(f'Error connecting to device {device.device_name}: {e}')
            return False

class AsyncBluetooth:
    """異步版本的藍牙設備管理類，供需要異步操作的場合使用"""
    
    def __init__(self):
        self.bt_device = None
        _LOGGER.info('AsyncBluetooth resource initialized')
    
    async def list_bt_device(self):
        """列出藍牙設備 (異步接口)"""
        from bluetooth.device_manager import list_devices
        try:
            devices = await list_devices()
            _LOGGER.debug(f'Found {len(devices)} bluetooth devices (async)')
            return devices
        except Exception as e:
            _LOGGER.error(f'Failed to list bluetooth devices (async): {e}')
            return []
    
    async def connect_bt_device(self, device: Device):
        """連接藍牙設備 (異步接口)"""
        from bluetooth.device_manager import connect_device
        try:
            _LOGGER.info(f'Attempting to connect to device (async): {device.device_name}')
            success = await connect_device(device)
            if success:
                self.bt_device = device
                _LOGGER.info(f'Successfully connected to {device.device_name} (async)')
            else:
                _LOGGER.warning(f'Failed to connect to {device.device_name} (async)')
            return success
        except Exception as e:
            _LOGGER.error(f'Error connecting to device {device.device_name} (async): {e}')
            return False

class SttAPI(ISttAPI):
    def get_test_resp(self, lang: Language):
        while True:
            try:
                command = recognize_direct(lang)
                break
            except ValueError:
                audio_player.play_async(RECOGNITION_FAIL_FILE, LANGUAGES[lang.lang_code])
                _LOGGER.info("辨識失敗，請再說一次")
        return command
                    
    def get_lang_resp(self) -> Language:
        audio_player.play_async(ASK_LANG_FILE, 'all')
        while True:
            try:
                user_lang = detect_language()
                audio_player.stop()
                break
            except TimeoutError:
                audio_player.play_async(ASK_LANG_FILE, 'all')
                _LOGGER.info("未收到使用者語音，請再試一次")
        return user_lang