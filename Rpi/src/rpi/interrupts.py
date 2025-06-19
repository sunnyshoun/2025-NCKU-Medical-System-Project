from .models import InterruptException, VisionTest
from audio.model import Language
from audio.player import audio_player
from settings import *
from data import vision
from data.draw import draw_circle_with_right_opening, paste_square_image_centered
from PIL.Image import Image, new
from PIL import ImageDraw, ImageFont
import logging, random, json, asyncio, time

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
        # 手機模式：發送移動命令到手機
        send_movement_command_to_phone(test, delta)
    else:
        # 按鈕模式：直接控制馬達
        test.oled.clear()
        test.oled.display()

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
        # 手機模式：發送圖像數據到手機
        send_image_to_phone(test, thickness, test.dir)
    else:
        # 按鈕模式：在 OLED 上顯示圖像
        img = draw_circle_with_right_opening(thickness=thickness)
        result = paste_square_image_centered(img.rotate(test.dir * 90))
        show_img(test, result)

def _handle_user_response(test: VisionTest, phone_mode: bool = False):
    if phone_mode:
        # 手機模式：請求手機端使用者回應
        request_phone_user_response(test)
        # 等待手機回應（已在其他地方處理）
        wait_for_phone_response(test)
    else:
        # 按鈕模式：使用語音辨識
        test.got_resp = test_resp(test)
    
    _LOGGER.info(f'Got test response: {test.got_resp} (phone_mode: {phone_mode})')


def wait_mov(test: VisionTest, phone_mode: bool = False):
    resp = test.motor.readline().decode().strip()

    if resp == 'done':
        if phone_mode:
            # 手機模式：發送移動完成通知
            send_movement_done_to_phone(test)
        else:
            # 按鈕模式：播放提示音
            test.audio.play_async(BEEP_FILE, 'all')
        _LOGGER.info(f"Move done (phone_mode: {phone_mode})")
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
        # 手機模式：發送結果到手機
        send_result_to_phone(test, d)
    else:
        # 按鈕模式：在 OLED 上顯示結果
        image = new('1', (128, 64))
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(**RESULT_FONT)

        draw.rectangle((0, 0, 128, 64), outline=0, fill=0)
        draw.text((0, 0), RESULT_STRS[test.lang.lang_code], font=font, fill=255)
        draw.text((5, 22), f'{d:0.1f}', font=font, fill = 255)
        test.oled.set_img(image)
        test.oled.display()
        test.audio.play_async(TEST_DONE_FILE, LANGUAGES[test.lang.lang_code])

def show_img(test: VisionTest, img: Image) -> None:
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


# === 手機模式專用函數 ===

def send_movement_command_to_phone(test: VisionTest, delta: float):
    """發送移動命令到手機"""
    try:
        if hasattr(test, 'phone_controller'):
            command = {
                "type": "robot_movement",
                "distance_mm": delta,
                "message": f"機器人移動 {delta}mm"
            }
            asyncio.create_task(
                test.phone_controller.send_data(json.dumps(command).encode('utf-8'))
            )
    except Exception as e:
        _LOGGER.error(f"發送移動命令失敗: {e}")

def send_image_to_phone(test: VisionTest, thickness: int, direction: int):
    """發送圖像數據到手機"""
    try:
        if hasattr(test, 'phone_controller'):
            command = {
                "type": "show_vision_test",
                "thickness": thickness,
                "direction": direction,
                "degree": test.cur_degree
            }
            asyncio.create_task(
                test.phone_controller.send_data(json.dumps(command).encode('utf-8'))
            )
    except Exception as e:
        _LOGGER.error(f"發送圖像數據失敗: {e}")

def request_phone_user_response(test: VisionTest):
    """請求手機端使用者回應"""
    try:
        if hasattr(test, 'phone_controller'):
            command = {
                "type": "request_user_input",
                "message": "請指出開口方向",
                "options": ["右", "上", "左", "下"]
            }
            asyncio.create_task(
                test.phone_controller.send_data(json.dumps(command).encode('utf-8'))
            )
    except Exception as e:
        _LOGGER.error(f"請求使用者回應失敗: {e}")

def wait_for_phone_response(test: VisionTest):
    """等待手機回應"""
    timeout = 30
    start_time = time.time()
    
    while test.got_resp is None and (time.time() - start_time) < timeout:
        time.sleep(0.1)
    
    if test.got_resp is None:
        _LOGGER.warning("等待手機回應超時")
        test.got_resp = False

def send_movement_done_to_phone(test: VisionTest):
    """發送移動完成通知到手機"""
    try:
        if hasattr(test, 'phone_controller'):
            command = {
                "type": "movement_complete",
                "message": "機器人移動完成",
                "current_distance": test.cur_distance
            }
            asyncio.create_task(
                test.phone_controller.send_data(json.dumps(command).encode('utf-8'))
            )
    except Exception as e:
        _LOGGER.error(f"發送移動完成通知失敗: {e}")

def send_result_to_phone(test: VisionTest, result: float):
    """發送測試結果到手機"""
    try:
        if hasattr(test, 'phone_controller'):
            command = {
                "type": "test_complete",
                "vision_score": result,
                "timestamp": time.time(),
                "message": f"視力測試完成，結果: {result}"
            }
            asyncio.create_task(
                test.phone_controller.send_data(json.dumps(command).encode('utf-8'))
            )
    except Exception as e:
        _LOGGER.error(f"發送測試結果失敗: {e}")

def send_audio_to_phone(test: VisionTest, file_name: str, language: str):
    """發送音訊檔案到手機播放"""
    try:
        if hasattr(test, 'phone_controller'):
            import os
            from audio.player import audio_player
            
            audio_path = os.path.join(audio_player.base_folder, language, file_name)
            if os.path.exists(audio_path):
                with open(audio_path, 'rb') as f:
                    audio_data = f.read()
                
                # 發送音訊檔案
                asyncio.create_task(
                    test.phone_controller.send_file(audio_data)
                )
                
                # 發送播放命令
                command = {
                    "type": "play_audio",
                    "file_name": file_name,
                    "language": language
                }
                asyncio.create_task(
                    test.phone_controller.send_data(json.dumps(command).encode('utf-8'))
                )
    except Exception as e:
        _LOGGER.error(f"發送音訊檔案失敗: {e}")