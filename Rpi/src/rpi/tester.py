from .models import VisionTest, InterruptException
from . import interrupts
from settings import *
from data import vision
import logging, time, json, asyncio

_LOGGER = logging.getLogger('TestingFlow')
_LOGGER.setLevel(LOGGER_LEVEL)

def setup(t: VisionTest, phone_mode: bool = False):
    _LOGGER.info(f'Setup section (phone_mode: {phone_mode})')

    t.motor.open_serial()

    t.oled.clear()
    t.oled.display()

    t.cur_degree = TEST_START_DEGREE
    t.cur_distance = -1.0
    
    while t.cur_distance < 0:
        t.cur_distance = t.sonic.get_distance()

    _LOGGER.info(f'Set cur_distance to {t.cur_distance}')

    if phone_mode:
        # 手機模式下，語言由手機端選擇
        _LOGGER.info('Phone mode: language set by phone')
    else:
        # 按鈕模式下，選擇語言
        _LOGGER.debug('Choose language')
        t.lang = interrupts.lang_resp(t)
        while t.lang == None:
            t.lang = interrupts.lang_resp(t)
            time.sleep(1)
            
        _LOGGER.info(f'Set language to: {t.lang.lang_code}')
        t.audio.play_async(TEST_INTRO_FILE, LANGUAGES[t.lang.lang_code])

def loop(t: VisionTest, phone_mode: bool = False):
    # === define ===
    _STATE_SET_UP = 0
    _STATE_SHOW_IMG = 1
    _STATE_INPUT = 2

    _LOGGER.info(f'--- Enter loop with state: {t.state} (phone_mode: {phone_mode}) ---')
    _LOGGER.info(f'cur_degree: {t.cur_degree}, cur_distance: {t.cur_distance}')

    if t.state == _STATE_SET_UP:
        if 0.1 <= t.cur_degree and t.cur_degree <= 1.5:
            t.state = _STATE_SHOW_IMG
            t.got_resp = None

        else:
            if t.max_degree < 0:
                # 結束測試，度數小於最低值
                raise InterruptException(INTERRUPT_INST_SHOW_RESULT,
                                        INTERRUPT_RESULT_MIN,
                                        test=t,
                                        end=True,
                                        phone_mode=phone_mode)
            else:
                # 結束測試，度數大於最高值
                raise InterruptException(INTERRUPT_INST_SHOW_RESULT,
                                        INTERRUPT_RESULT_MAX,
                                        test=t,
                                        end=True,
                                        phone_mode=phone_mode)

    elif t.state == _STATE_SHOW_IMG:
        target = vision.distance[int(t.cur_degree * 10) - 1]
        _LOGGER.debug(f'{abs(target - t.cur_distance)} m to target')
        if abs(target - t.cur_distance) < 0.001:
            # 不須移動
            t.state = _STATE_INPUT
            # 顯示圖像
            raise InterruptException(INTERRUPT_INST_SHOW_IMG,
                                    test=t,
                                    end=False,
                                    phone_mode=phone_mode)
        else:
            # 移動 target - t.cur_distance 公尺，換算毫米
            raise InterruptException(INTERRUPT_INST_START_MOV,
                                    int((target - t.cur_distance) * 1000),
                                    test=t,
                                    end=False,
                                    phone_mode=phone_mode)
    
    elif t.state == _STATE_INPUT:
        # 使用者是否看得清楚？
        if t.got_resp == None:
            raise InterruptException(INTERRUPT_INST_USR_RESP,
                                    test=t,
                                    end=False,
                                    phone_mode=phone_mode)
        else:
            t.state = _STATE_SET_UP
            if t.got_resp:
                t.max_degree = t.cur_degree
                t.cur_degree = round(t.cur_degree + 0.1, 1)
            elif t.max_degree < 0.0:
                t.cur_degree = round(t.cur_degree - 0.1, 1)
            else:
                raise InterruptException(INTERRUPT_INST_SHOW_RESULT,
                                        t.max_degree,
                                        test=t,
                                        end=True,
                                        phone_mode=phone_mode)

    else:
        raise ValueError(f'Unexpected state code: {t.state}')

    
def end(t: VisionTest, phone_mode: bool = False):
    _LOGGER.info(f'End section (phone_mode: {phone_mode})')
    t.motor.close_serial()

def make_test(vision_test_obj: VisionTest, phone_mode: bool = False):
    """
    執行視力測試
    Args:
        vision_test_obj: 視力測試物件
        phone_mode: 是否為手機控制模式
    """
    try:
        setup(vision_test_obj, phone_mode)

        while (True):
            try:
                loop(vision_test_obj, phone_mode)
                time.sleep(RPI_LOOP_INTERVAL)

            except InterruptException as ex:
                _LOGGER.debug(f'Interrupt: {ex.args}, end: {ex.end}, phone_mode: {phone_mode}')
                
                # 將 phone_mode 資訊傳遞給中斷處理器
                ex.phone_mode = phone_mode
                interrupts.sorter(ex)
                
                if ex.end:
                    break
            
    except KeyboardInterrupt:
        _LOGGER.info('Catch KeyboardInterrupt')
        
    finally:
        end(vision_test_obj, phone_mode)


class PhoneTestController:
    """手機測試控制器"""
    
    def __init__(self, ble_server):
        self.ble_server = ble_server
        self.current_test = None
        self.test_active = False
    
    async def send_test_command(self, command_type: str, data: dict = None):
        """發送測試命令到手機"""
        command = {
            "type": "test_command",
            "command": command_type,
            "data": data or {}
        }
        await self.ble_server.send_data(json.dumps(command).encode('utf-8'))
    
    async def send_image_data(self, image_thickness: int, direction: int):
        """發送圖像數據到手機"""
        command = {
            "type": "show_image",
            "thickness": image_thickness,
            "direction": direction  # 0=right, 1=up, 2=left, 3=down
        }
        await self.ble_server.send_data(json.dumps(command).encode('utf-8'))
    
    async def send_test_result(self, result: float):
        """發送測試結果到手機"""
        command = {
            "type": "test_result",
            "vision_score": result,
            "timestamp": time.time()
        }
        await self.ble_server.send_data(json.dumps(command).encode('utf-8'))
    
    async def request_user_response(self):
        """請求使用者回應"""
        command = {
            "type": "request_response",
            "message": "請指出開口方向"
        }
        await self.ble_server.send_data(json.dumps(command).encode('utf-8'))
    
    async def send_audio_file(self, file_name: str, language: str):
        """發送音訊檔案到手機"""
        import os
        from audio.player import audio_player
        
        audio_path = os.path.join(audio_player.base_folder, language, file_name)
        if os.path.exists(audio_path):
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            
            # 發送音訊檔案
            await self.ble_server.send_file(audio_data)
            
            # 發送播放命令
            command = {
                "type": "play_audio",
                "file_name": file_name,
                "language": language
            }
            await self.ble_server.send_data(json.dumps(command).encode('utf-8'))


if __name__ == '__main__':

    raise RuntimeError('Should not be call as \"__main__\"')

    # from rpi.resource import Resource
    # logging.basicConfig(format=LOGGER_FORMAT)
    # main(VisionTest(Resource()), wait=TEST_SHOW_DURATION)