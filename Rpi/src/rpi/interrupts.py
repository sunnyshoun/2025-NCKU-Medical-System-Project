from .models import InterruptException, VisionTest
from audio.model import Language
from audio.player import audio_player
from settings import *
from data import vision
from data.draw import draw_circle_with_right_opening, paste_square_image_centered
from PIL.Image import Image, new
from PIL import ImageDraw, ImageFont
import logging, random

_LOGGER = logging.getLogger('Interrupt')

def sorter(ex: InterruptException):
    _LOGGER.debug(f'Sorter got {ex.args}')

    test = ex.test
    instruction = ex.args[0]
    phone_mode = getattr(ex, 'phone_mode', False)

    dispatch = {
        INTERRUPT_INST_SHOW_RESULT: lambda: _handle_show_result(test, ex.args[1], phone_mode),
        INTERRUPT_INST_START_MOV: lambda: _handle_start_mov(test, ex.args[1], phone_mode),
        INTERRUPT_INST_SHOW_IMG: lambda: _handle_show_img(test, phone_mode),
        INTERRUPT_INST_USR_RESP: lambda: _handle_user_response(test, phone_mode),
    }

    handler = dispatch.get(instruction)
    if handler:
        handler()
    else:
        raise ValueError(f'Unexpected instruction code: {instruction}')

def _handle_show_result(test: VisionTest, degree: float, phone_mode: bool = False):
    _LOGGER.debug(f'Show result (phone_mode: {phone_mode})')
    show_result(test, degree, phone_mode)

def _handle_start_mov(test: VisionTest, delta: float, phone_mode: bool = False):
    target = test.cur_distance + (delta / 1000)
    _LOGGER.info(f"Start moving {delta} mm to {round(target, 3)} (phone_mode: {phone_mode})")

    if phone_mode:
        # 手機模式：清空 OLED，使用draw.py繪製，由oled控制模組更新螢幕
        test.oled.clear()
        test.oled.display()
    else:
        # 按鈕模式：清空 OLED 顯示
        test.oled.clear()
        test.oled.display()

    # 發送馬達控制命令
    msg = f'm{0 if delta > 0 else 1},{abs(delta)}\n'
    _LOGGER.debug(f"sending: {msg.rstrip()}")
    test.motor.write(msg.encode())

    resp = test.motor.readline().decode().strip()
    if resp == 'ok':
        test.cur_distance = round(target, 3)
        _LOGGER.debug(f"Start move got \"ok\"")
    else:
        raise ValueError(f'Unexpected response from start move: {resp}')

    wait_mov(test, phone_mode)

def _handle_show_img(test: VisionTest, phone_mode: bool = False):
    thickness = vision.thickness[int(test.cur_degree * 10) - 1]
    test.dir = random.randint(0, 3)
    _LOGGER.debug(f"Dir: {test.dir} (phone_mode: {phone_mode})")
    
    if phone_mode:
        # 手機模式：清空 OLED，圖像處理由手機端負責
        test.oled.clear()
        test.oled.display()
        _LOGGER.info("手機模式：圖像將由手機端處理")
    else:
        # 按鈕模式：在 OLED 上顯示圖像，使用draw.py繪製
        img = draw_circle_with_right_opening(thickness=thickness)
        result = paste_square_image_centered(img.rotate(test.dir * 90))
        show_img(test, result)

def _handle_user_response(test: VisionTest, phone_mode: bool = False):
    if phone_mode:
        # 手機模式：等待手機回應
        test.got_resp = _get_phone_test_response(test)
    else:
        # 按鈕模式：使用語音辨識
        test.got_resp = test_resp(test)
    
    _LOGGER.info(f'Got test response: {test.got_resp} (phone_mode: {phone_mode})')

def _get_phone_test_response(test: VisionTest) -> bool:
    """獲取手機測試回應"""
    try:
        # 使用手機模式的 STT API 獲取回應
        direction = test.stt.get_test_resp(test.lang)
        return direction == test.dir
    except Exception as e:
        _LOGGER.error(f"獲取手機測試回應失敗: {e}")
        return False

def wait_mov(test: VisionTest, phone_mode: bool = False):
    resp = test.motor.readline().decode().strip()

    if resp == 'done':
        if phone_mode:
            # 手機模式：移動完成，不播放提示音
            _LOGGER.info("機器人移動完成（手機模式，無音檔播放）")
        else:
            # 按鈕模式：播放提示音
            test.audio.play_async(BEEP_FILE, 'all')
            _LOGGER.info("機器人移動完成（按鈕模式，播放提示音）")
    else:
        raise ValueError(f'Unexpected response from wait move: {resp}')

def show_result(test: VisionTest, degree: float, phone_mode: bool = False) -> None:
    if abs(degree - INTERRUPT_RESULT_MIN) < 0.1:
        _LOGGER.info('Test result: < 0.1')
        d = 0.0
    elif abs(degree - INTERRUPT_RESULT_MAX) < 0.1:
        _LOGGER.info('Test result: >= 1.5')
        d = 1.6
    else:
        _LOGGER.info(f'Test result: {degree}')
        d = degree

    if phone_mode:
        # 手機模式：結果只發送到手機，OLED不顯示結果
        test.oled.clear()
        test.oled.display()
        _LOGGER.info(f"測試完成，結果只發送到手機: {d}，OLED不顯示結果")
    else:
        # 按鈕模式：在 OLED 上顯示結果，使用draw.py繪製圖案
        image = new('1', (128, 64))
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(**RESULT_FONT)

        # 使用draw.py的繪製邏輯
        draw.rectangle((0, 0, 128, 64), outline=0, fill=0)
        draw.text((0, 0), RESULT_STRS[test.lang.lang_code], font=font, fill=255)
        draw.text((5, 22), f'{d:0.1f}', font=font, fill = 255)
        
        # 由oled控制模組更新螢幕
        test.oled.set_img(image)
        test.oled.display()
        
        # 播放完成音檔
        test.audio.play_async(TEST_DONE_FILE, LANGUAGES[test.lang.lang_code])

def show_img(test: VisionTest, img: Image) -> None:
    """顯示圖像，由oled控制模組更新螢幕"""
    _LOGGER.info(f'Show image, dir: {test.dir}')
    test.oled.set_img(img)
    test.oled.display()

def test_resp(test: VisionTest) -> bool:
    while True:
        try:
            _LOGGER.info(f'Waiting test resp')
            res = test.stt.get_test_resp(test.lang)
            _LOGGER.info(f'Got response: {res}')
            return  res == test.dir

        except ValueError as e:
            _LOGGER.warning(e.args[0])

def lang_resp(test: VisionTest) -> Language:
    while True:
        try:
            _LOGGER.info(f'Waiting language resp')
            return test.stt.get_lang_resp()

        except ValueError as e:
            _LOGGER.warning(e.args[0])