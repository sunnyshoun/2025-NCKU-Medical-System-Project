# Entry of the app running on Raspberry Pi 3B+

from rpi.menu import MainMenu
from rpi.models import VisionTest
from rpi.resource import Audio, Bluetooth, SttAPI
from hardwares import Motor, Oled, Sonic, Button
from rpi.tester import make_test
from ble_communication.ble_server import BLEServer
from settings import *
import logging, os, datetime, asyncio, threading, json, time


class RobotController:
    def __init__(self):
        self.stt = SttAPI()
        self.motor = Motor()
        self.sonic = Sonic()
        self.btn = Button()
        self.oled = Oled()
        self.audio = Audio()
        self.bluetooth = Bluetooth()
        self.ble_server = None
        self.phone_connected = False
        self.current_test = None
        self.test_in_progress = False
        
    async def setup_ble_server(self):
        """設置 BLE 服務器"""
        self.ble_server = BLEServer("EyeDwell_Robot")
        
        # 設置回調函數
        self.ble_server.on_control_command = self.handle_control_command
        self.ble_server.on_data_received = self.handle_data_received
        self.ble_server.on_file_received = self.handle_file_received
        self.ble_server.on_connection_changed = self.handle_connection_changed
        
        await self.ble_server.start_server()
        logging.info("BLE 服務器啟動成功")
    
    def handle_control_command(self, command: str):
        """處理來自手機的控制命令"""
        try:
            cmd_data = json.loads(command)
            cmd_type = cmd_data.get("type")
            
            if cmd_type == "start_test":
                if not self.test_in_progress:
                    self.start_phone_controlled_test(cmd_data)
            elif cmd_type == "test_response":
                if self.current_test and self.test_in_progress:
                    direction = cmd_data.get("direction")  # 0=right, 1=up, 2=left, 3=down
                    self.current_test.got_resp = (direction == self.current_test.dir)
            elif cmd_type == "stop_test":
                if self.test_in_progress:
                    self.test_in_progress = False
                    
        except json.JSONDecodeError:
            logging.error(f"無法解析控制命令: {command}")
    
    def handle_data_received(self, data: bytes):
        """處理來自手機的數據"""
        try:
            # 檢查是否為文字訊息
            if data.startswith(b'{'):
                message = json.loads(data.decode('utf-8'))
                logging.info(f"收到手機訊息: {message}")
            else:
                logging.info(f"收到手機數據: {len(data)} bytes")
        except Exception as e:
            logging.error(f"處理數據失敗: {e}")
    
    def handle_file_received(self, file_data: bytes):
        """處理來自手機的音訊檔案"""
        try:
            # 儲存音訊檔案
            audio_path = "/tmp/phone_audio.wav"
            with open(audio_path, "wb") as f:
                f.write(file_data)
            
            # 如果正在測試中，使用此音訊進行 STT
            if self.current_test and self.test_in_progress:
                result = self.stt.recognize_from_file(audio_path, self.current_test.lang)
                if result is not None:
                    self.current_test.got_resp = (result == self.current_test.dir)
                    
        except Exception as e:
            logging.error(f"處理音訊檔案失敗: {e}")
    
    def handle_connection_changed(self, connected: bool):
        """處理連線狀態變化"""
        self.phone_connected = connected
        logging.info(f"手機連線狀態: {connected}")
        
        if connected:
            # 顯示手機連線圖示
            self.show_phone_connected()
        else:
            # 回到正常選單
            self.phone_connected = False
            if self.test_in_progress:
                self.test_in_progress = False
    
    def show_phone_connected(self):
        """顯示手機已連線"""
        from PIL import Image, ImageDraw, ImageFont
        from settings import MENU_FONT
        
        img = Image.new('1', (128, 64), 0)
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(**MENU_FONT)
        
        # 畫手機圖示
        draw.rectangle([50, 10, 78, 40], outline=1, width=2)
        draw.rectangle([52, 12, 76, 38], fill=1)
        draw.rectangle([60, 42, 68, 44], outline=1)
        
        # 顯示文字
        draw.text((30, 50), "Phone Connected", font=font, fill=1)
        
        self.oled.clear()
        self.oled.set_img(img)
        self.oled.display()
    
    def start_phone_controlled_test(self, params):
        """開始由手機控制的測試"""
        self.test_in_progress = True
        
        # 創建測試物件
        self.current_test = VisionTest(
            motor=self.motor,
            oled=self.oled,
            sonic=self.sonic,
            audio=PhoneAudio(self.ble_server),  # 使用手機音訊
            stt=PhoneSttAPI(self.ble_server)    # 使用手機 STT
        )
        
        # 設置測試參數
        language_code = params.get("language", LANG_EN)
        self.current_test.lang = self.get_language_by_code(language_code)
        
        # 在新線程中運行測試
        test_thread = threading.Thread(target=self.run_phone_test)
        test_thread.start()
    
    def get_language_by_code(self, code):
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
    
    def run_phone_test(self):
        """運行手機控制的測試"""
        try:
            make_test(self.current_test, phone_mode=True)
            
            # 測試完成，發送結果到手機
            if self.current_test.max_degree >= 0:
                result = {
                    "type": "test_result",
                    "vision_score": self.current_test.max_degree,
                    "timestamp": time.time()
                }
                asyncio.create_task(
                    self.ble_server.send_data(json.dumps(result).encode('utf-8'))
                )
                
        except Exception as e:
            logging.error(f"手機控制測試失敗: {e}")
        finally:
            self.test_in_progress = False
            self.current_test = None
    
    def start_func(self):
        """開始測試功能（按鈕控制）"""
        if self.phone_connected:
            # 如果手機已連線，不允許按鈕操作
            return MENU_STATE_ROOT
            
        test = VisionTest(
            motor=self.motor,
            oled=self.oled,
            sonic=self.sonic,
            audio=self.audio,
            stt=self.stt
        )
        make_test(test, phone_mode=False)
        self.btn.read_btn()
        return MENU_STATE_ROOT
    
    def run_menu_loop(self):
        """運行選單循環"""
        menu = MainMenu(
            self.start_func,
            btn=self.btn,
            oled=self.oled,
            audio=self.audio,
            bluetooth=self.bluetooth,
            robot_controller=self
        )
        
        while True:
            if self.phone_connected and not self.test_in_progress:
                self.show_phone_connected()
                time.sleep(1)
            else:
                menu.loop()


class PhoneAudio:
    """手機音訊介面"""
    def __init__(self, ble_server):
        self.ble_server = ble_server
    
    def play_async(self, file_name: str, language: str, wait_time: int = 0):
        """發送音訊檔案到手機播放"""
        import os
        from audio.player import audio_player
        
        audio_path = os.path.join(audio_player.base_folder, language, file_name)
        if os.path.exists(audio_path):
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            
            # 發送音訊到手機
            asyncio.create_task(self.ble_server.send_file(audio_data))
    
    def set_volume(self, volume: int) -> bool:
        # 發送音量設置命令到手機
        command = json.dumps({"type": "set_volume", "volume": volume})
        asyncio.create_task(
            self.ble_server.send_data(command.encode('utf-8'))
        )
        return True
    
    def get_volume(self) -> int:
        return 50  # 預設值


class PhoneSttAPI:
    """手機 STT 介面"""
    def __init__(self, ble_server):
        self.ble_server = ble_server
        self.waiting_for_response = False
        self.last_response = None
    
    def get_test_resp(self, lang):
        """等待手機的測試回應"""
        # 發送請求語音輸入的命令
        command = json.dumps({
            "type": "request_voice_input",
            "language": lang.lang_code
        })
        asyncio.create_task(
            self.ble_server.send_data(command.encode('utf-8'))
        )
        
        # 等待回應
        self.waiting_for_response = True
        timeout = 30
        start_time = time.time()
        
        while self.waiting_for_response and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        if self.last_response is not None:
            response = self.last_response
            self.last_response = None
            return response
        
        raise ValueError("語音辨識超時")
    
    def recognize_from_file(self, file_path, lang):
        """從音訊檔案進行語音辨識"""
        from audio.recognizer import recognize
        return recognize(file_path, lang)
    
    def get_lang_resp(self):
        """語言選擇（手機模式下由手機處理）"""
        from audio.language_detection import LANGUAGE_MODELS
        return LANGUAGE_MODELS["en"]  # 預設英文


async def main():
    controller = RobotController()
    
    # 設置日誌
    if not os.path.exists(LOG_FOLDER):
        os.mkdir(LOG_FOLDER)

    log_name = datetime.datetime.strftime(datetime.datetime.now(), LOG_TIME_FORMAT)

    if SAVE_LOG:
        logging.basicConfig(
            level=LOGGER_LEVEL, 
            format=LOGGER_FORMAT,
            filemode='w',
            filename=f'{LOG_FOLDER}{log_name}.log'
        )
    else:
        logging.basicConfig(
            level=LOGGER_LEVEL, 
            format=LOGGER_FORMAT
        )
    
    # 設置 BLE 服務器
    await controller.setup_ble_server()
    
    # 在新線程中運行選單循環
    menu_thread = threading.Thread(target=controller.run_menu_loop)
    menu_thread.daemon = True
    menu_thread.start()
    
    # 保持 BLE 服務器運行
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logging.info("程式結束")
    finally:
        if controller.ble_server:
            await controller.ble_server.stop_server()


if __name__ == '__main__':
    logging.getLogger('Adafruit_I2C.Device.Bus.1.Address.0X3C').setLevel(logging.WARNING)
    asyncio.run(main())