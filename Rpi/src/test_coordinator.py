import logging
import threading
import asyncio
from typing import Optional

from settings import *
from rpi.models import VisionTest
from rpi.tester import make_test
from rpi.resource import Audio
from hardwares.button import Button

from traceback import print_exc

class TestCoordinator:
    """協調視力測試的執行，支援按鈕模式和手機模式"""
    
    def __init__(self, motor, oled, sonic, audio, stt, phone_handler):
        self.logger = logging.getLogger("TestCoordinator")
        
        # 硬體組件
        self.motor = motor
        self.oled = oled
        self.sonic = sonic
        self.audio = audio
        
        # 軟體資源（只用於按鈕模式）
        if not isinstance(audio, Audio):
            self.logger.error("提供的 audio 不是 Audio 實例")
            audio = Audio()
        
        self.stt = stt
        
        # 手機處理器
        self.phone_handler = phone_handler
        
        # 測試狀態
        self.current_test: Optional[VisionTest] = None
        self.test_thread: Optional[threading.Thread] = None
        self.test_active = False
        self.test_mode = "button"  # "button" or "phone"
        self.test_lock = threading.Lock()
        
        # 手機模式的回應等待
        self.waiting_for_response = False
        self.phone_response = None
        self.response_event = threading.Event()
    
    def is_test_active(self) -> bool:
        """檢查測試是否活躍"""
        with self.test_lock:
            return self.test_active
    
    def start_button_test(self) -> bool:
        """開始按鈕模式測試"""
        with self.test_lock:
            if self.test_active:
                self.logger.warning("測試已在進行中")
                return False
            
            self.test_mode = "button"
            self.test_active = True
        
        # 創建按鈕模式測試物件
        self.current_test = VisionTest(
            motor=self.motor,
            oled=self.oled,
            sonic=self.sonic,
            audio=self.audio,
            stt=self.stt
        )
        
        # 在新線程中運行測試
        self.test_thread = threading.Thread(
            target=self._run_button_test,
            daemon=True
        )
        self.test_thread.start()
        
        self.logger.info("開始按鈕模式測試")
        return True
    
    async def start_phone_test(self) -> bool:
        """開始手機模式測試"""
        with self.test_lock:
            if self.test_active:
                self.logger.warning("測試已在進行中")
                return False
            
            self.test_mode = "phone"
            self.test_active = True
        
        # 創建手機模式測試物件（不需要音檔和STT）
        phone_stt = PhoneSttAPI(self)
        
        self.current_test = VisionTest(
            motor=self.motor,
            oled=self.oled,
            sonic=self.sonic,
            audio=DummyAudio(),  # 手機模式不播放音檔
            stt=phone_stt
        )
        
        # 設置預設語言（英文）
        self.current_test.lang = self._get_language_by_code(LANG_EN)
        
        # 在新線程中運行測試
        self.test_thread = threading.Thread(
            target=self._run_phone_test,
            daemon=True
        )
        self.test_thread.start()
        
        self.logger.info("開始手機模式測試（使用預設語言）")
        return True
    
    async def stop_test(self):
        """停止當前測試"""
        with self.test_lock:
            if not self.test_active:
                return
            
            self.test_active = False
        
        # 通知等待的線程
        self.response_event.set()
        
        # 等待測試線程結束
        if self.test_thread and self.test_thread.is_alive():
            self.test_thread.join(timeout=5)
        
        self.current_test = None
        self.test_thread = None
        
        self.logger.info("測試已停止")
    
    def set_phone_response(self, direction: int):
        """設置手機回應"""
        self.phone_response = direction
        self.response_event.set()
        self.logger.info(f"收到手機方向回應: {direction}")
    
    def wait_for_phone_response(self, timeout: float = 30.0) -> Optional[int]:
        """等待手機回應"""
        if self.test_mode != "phone":
            return None
        
        self.waiting_for_response = True
        self.phone_response = None
        self.response_event.clear()
        
        # 通知手機可以選擇方向了
        try:
            # 在事件循環中執行通知
            def notify_phone():
                try:
                    loop = asyncio.get_event_loop()
                    loop.create_task(self.phone_handler.notify_ready_for_input())
                except RuntimeError:
                    # 如果沒有事件循環，創建新線程執行
                    async def async_notify():
                        await self.phone_handler.notify_ready_for_input()
                    
                    threading.Thread(
                        target=lambda: asyncio.run(async_notify()),
                        daemon=True
                    ).start()
            
            notify_phone()
            
        except Exception as e:
            self.logger.error(f"通知手機失敗: {e}")
        
        # 等待回應
        if self.response_event.wait(timeout):
            response = self.phone_response
            self.waiting_for_response = False
            return response
        else:
            self.logger.warning("等待手機回應超時")
            self.waiting_for_response = False
            return None
    
    def _run_button_test(self):
        """運行按鈕模式測試"""
        try:
            make_test(self.current_test, phone_mode=False)
            Button().read_btn()
        except Exception as e:
            self.logger.error(f"按鈕模式測試失敗: {e}")
        finally:
            with self.test_lock:
                self.test_active = False
            self.logger.info("按鈕模式測試結束")
    
    def _run_phone_test(self):
        """運行手機模式測試"""
        try:
            make_test(self.current_test, phone_mode=True)
            
            # 測試完成，發送結果到手機
            if self.current_test.max_degree >= 0:
                result = self.current_test.max_degree
            else:
                result = 0.0
            
            # 在事件循環中發送結果
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
            self.logger.error(f"手機模式測試失敗: {e}")
        finally:
            with self.test_lock:
                self.test_active = False
            self.logger.info("手機模式測試結束")
    
    def _get_language_code(self, language_str: str) -> int:
        """根據語言字串獲取語言代碼"""
        language_map = {
            "zh": LANG_ZH,
            "tw": LANG_TW,
            "en": LANG_EN,
            "ja": LANG_JP
        }
        return language_map.get(language_str, LANG_EN)
    
    def _get_language_by_code(self, code: int):
        """根據代碼獲取語言物件"""
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
    """簡化的手機 STT API - 只等待手機回應"""
    
    def __init__(self, test_coordinator):
        self.logger = logging.getLogger("PhoneSttAPI")
        self.test_coordinator = test_coordinator
    
    def get_test_resp(self, lang) -> int:
        """等待手機的方向回應"""
        while True:
            try:
                # 等待手機回應
                response = self.test_coordinator.wait_for_phone_response(timeout=30.0)
                
                if response is not None:
                    self.logger.info(f"收到手機方向回應: {response}")
                    return response
                else:
                    self.logger.warning("手機回應超時重送")
                    
            except Exception as e:
                self.logger.error(f"獲取手機回應失敗: {e}")
                raise ValueError(f"獲取回應失敗: {e}")
    
    def get_lang_resp(self):
        """語言選擇（手機模式下已由手機指定）"""
        from audio.language_detection import LANGUAGE_MODELS
        return LANGUAGE_MODELS["en"]  # 預設值，實際語言已在開始測試時設定


class DummyAudio:
    """手機模式的虛擬音訊介面 - 不播放任何音檔"""
    
    def __init__(self):
        self.logger = logging.getLogger("DummyAudio")
    
    def play_async(self, file_name: str, language: str, wait_time: int = 0) -> None:
        """不播放音檔（手機模式）"""
        self.logger.debug(f"手機模式：忽略音檔播放 {file_name} ({language})")
    
    def set_volume(self, volume: int) -> bool:
        """不設置音量（手機模式）"""
        return True
    
    def get_volume(self) -> int:
        """返回預設音量"""
        return 50
    
    def stop(self):
        """不需要停止"""
        pass
    
    def wait_play_done(self):
        """不需要等待"""
        pass