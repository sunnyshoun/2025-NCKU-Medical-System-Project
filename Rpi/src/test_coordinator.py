import logging
import threading
import asyncio
from typing import Optional

from settings import *
from rpi.models import VisionTest
from rpi.tester import make_test
from rpi.resource import Audio
from hardwares.button import Button

class TestCoordinator:
    def __init__(self, motor, oled, sonic, audio, stt, phone_handler):
        self.logger = logging.getLogger("TestCoordinator")
        
        self.motor = motor
        self.oled = oled
        self.sonic = sonic
        self.audio = audio
        
        if not isinstance(audio, Audio):
            self.logger.error("Provided audio is not Audio instance")
            audio = Audio()
        
        self.stt = stt
        self.phone_handler = phone_handler
        
        self.current_test: Optional[VisionTest] = None
        self.test_thread: Optional[threading.Thread] = None
        self.test_active = False
        self.test_mode = "button"
        self.test_lock = threading.Lock()
        
        self.waiting_for_response = False
        self.phone_response = None
        self.response_event = threading.Event()
    
    def is_test_active(self) -> bool:
        with self.test_lock:
            return self.test_active
    
    def start_button_test(self) -> bool:
        with self.test_lock:
            if self.test_active:
                self.logger.warning("Test already active")
                return False
            
            self.test_mode = "button"
            self.test_active = True
        
        self.current_test = VisionTest(
            motor=self.motor,
            oled=self.oled,
            sonic=self.sonic,
            audio=self.audio,
            stt=self.stt
        )
        
        self.test_thread = threading.Thread(
            target=self._run_button_test,
            daemon=True
        )
        self.test_thread.start()
        
        return True
    
    def start_phone_test(self) -> bool:
        with self.test_lock:
            if self.test_active:
                self.logger.warning("Test already active")
                return False
            
            self.test_mode = "phone"
            self.test_active = True
        
        phone_stt = PhoneSttAPI(self)
        
        self.current_test = VisionTest(
            motor=self.motor,
            oled=self.oled,
            sonic=self.sonic,
            audio=DummyAudio(),
            stt=phone_stt
        )
        
        self.current_test.lang = self._get_language_by_code(LANG_EN)
        
        self.test_thread = threading.Thread(
            target=self._run_phone_test,
            daemon=True
        )
        self.test_thread.start()
        
        return True
    
    def stop_test(self):
        with self.test_lock:
            if not self.test_active:
                return
            
            self.test_active = False
        
        self.response_event.set()
        
        if self.test_thread and self.test_thread.is_alive():
            self.test_thread.join(timeout=5)
        
        self.current_test = None
        self.test_thread = None
    
    def set_phone_response(self, direction: int):
        self.phone_response = direction
        self.response_event.set()
    
    def wait_for_phone_response(self, timeout: float = 30.0) -> Optional[int]:
        if self.test_mode != "phone":
            return None
        
        self.waiting_for_response = True
        self.phone_response = None
        self.response_event.clear()
        
        try:
            def notify_phone():
                try:
                    loop = asyncio.get_event_loop()
                    loop.create_task(self.phone_handler.notify_ready_for_input())
                except RuntimeError:
                    async def async_notify():
                        await self.phone_handler.notify_ready_for_input()
                    
                    threading.Thread(
                        target=lambda: asyncio.run(async_notify()),
                        daemon=True
                    ).start()
            
            notify_phone()
            
        except Exception as e:
            self.logger.error(f"Notify phone failed: {e}")
        
        if self.response_event.wait(timeout):
            response = self.phone_response
            self.waiting_for_response = False
            return response
        else:
            self.logger.warning("Wait for phone response timeout")
            self.waiting_for_response = False
            return None
    
    def _run_button_test(self):
        try:
            make_test(self.current_test, phone_mode=False)
            Button().read_btn()
        except Exception as e:
            self.logger.error(f"Button test failed: {e}")
        finally:
            with self.test_lock:
                self.test_active = False
    
    def _run_phone_test(self):
        try:
            make_test(self.current_test, phone_mode=True)
            
            if self.current_test.max_degree >= 0:
                result = self.current_test.max_degree
            else:
                result = 0.0
            
            def send_result():
                try:
                    loop = asyncio.get_event_loop()
                    loop.create_task(self.phone_handler.send_test_result(result))
                except RuntimeError:
                    async def async_send():
                        await self.phone_handler.send_test_result(result)
                    
                    threading.Thread(
                        target=lambda: asyncio.run(async_send()),
                        daemon=True
                    ).start()
            
            send_result()
                
        except Exception as e:
            self.logger.error(f"Phone test failed: {e}")
        finally:
            with self.test_lock:
                self.test_active = False
    
    def _get_language_code(self, language_str: str) -> int:
        language_map = {
            "zh": LANG_ZH,
            "tw": LANG_TW,
            "en": LANG_EN,
            "ja": LANG_JP
        }
        return language_map.get(language_str, LANG_EN)
    
    def _get_language_by_code(self, code: int):
        from audio.language_detection import LANGUAGE_MODELS
        
        lang_map = {
            LANG_EN: "en",
            LANG_ZH: "zh-TW", 
            LANG_JP: "ja",
            LANG_TW: "ta"
        }
        
        api_lang = lang_map.get(code, "en")
        return LANGUAGE_MODELS[api_lang]


class PhoneSttAPI:
    def __init__(self, test_coordinator):
        self.logger = logging.getLogger("PhoneSttAPI")
        self.test_coordinator = test_coordinator
    
    def get_test_resp(self, lang) -> int:
        while True:
            try:
                response = self.test_coordinator.wait_for_phone_response(timeout=30.0)
                
                if response is not None:
                    return response
                else:
                    self.logger.warning("Phone response timeout, retrying")
                    
            except Exception as e:
                self.logger.error(f"Get phone response failed: {e}")
                raise ValueError(f"Get response failed: {e}")
    
    def get_lang_resp(self):
        from audio.language_detection import LANGUAGE_MODELS
        return LANGUAGE_MODELS["en"]


class DummyAudio:
    def __init__(self):
        self.logger = logging.getLogger("DummyAudio")
    
    def play_async(self, file_name: str, language: str, wait_time: int = 0) -> None:
        pass
    
    def set_volume(self, volume: int) -> bool:
        return True
    
    def get_volume(self) -> int:
        return 50
    
    def stop(self):
        pass
    
    def wait_play_done(self):
        pass