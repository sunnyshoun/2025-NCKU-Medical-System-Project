from PIL.Image import Image
from audio.model import Language
from bluetooth.model import Device

# --- hardware ---
class IButton:
    def read_btn(self) -> int:
        raise NotImplementedError('Calling the interface method `read_btn`')

class IMotor:
    def open_serial(self) -> None:
        raise NotImplementedError('Calling the interface method `open_serial()`')
    def close_serial(self) -> None:
        raise NotImplementedError('Calling the interface method `close_serial()`')
    def write(self, msg: bytes) -> int | None:
        raise NotImplementedError('Calling the interface method `write()`')
    def readline(self) -> bytes:
        raise NotImplementedError('Calling the interface method `readline()`')

class IOled:
    def display(self) -> None:
        raise NotImplementedError('Calling the interface method `display()`')
    def clear(self) -> None:
        raise NotImplementedError('Calling the interface method `clear()`')
    def set_img(self, img: Image) -> None:
        raise NotImplementedError('Calling the interface method `set_img()`')

class ISonic:
    def get_distance(self) -> float:
        raise NotImplementedError('Calling the interface method `get_distance()`')
    
# --- RPI OS ---
class IAudio:
    def play_async(self, file_name: str, language: str, wait_time: int = 0) -> None:
        raise NotImplementedError('Calling the interface method `play_async`')
    def set_volume(self, volume: int) -> bool:
        raise NotImplementedError('Calling the interface method `set_volume`')
    def get_volume(self) -> int:
        raise NotImplementedError('Calling the interface method `get_volume`')

class IBluetooth:
    def start_discover(self, device: Device) -> bool:
        raise NotImplementedError('Calling the interface method `start_discover`')
    def stop_discover(self, device: Device) -> bool:
        raise NotImplementedError('Calling the interface method `stop_discover`')
    def list_bt_device(self) -> list[Device]:
        raise NotImplementedError('Calling the interface method `list_bt_device`')
    def connect_bt_device(self, device: Device) -> bool:
        raise NotImplementedError('Calling the interface method `connect_bt_device`')

class ISttAPI:
    def get_test_resp(self, lang: Language) -> int:
        raise NotImplementedError('Calling the interface method `get_test_resp()`')
    def get_lang_resp(self) -> Language:
        raise NotImplementedError('Calling the interface method `get_lang_resp()`')
