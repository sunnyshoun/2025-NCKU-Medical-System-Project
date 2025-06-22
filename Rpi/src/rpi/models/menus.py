from typing import Callable, Sequence
import logging
from settings import *
from PIL.Image import Image, new
from PIL import ImageDraw, ImageFont
from .resources import IButton, IOled, IAudio, IBluetooth

class MenuBase:
    """
    Providing hardwares and OS resources
    """
    btn: IButton
    oled: IOled
    audio: IAudio
    bluetooth: IBluetooth

    def __init__(
            self,
            btn: IButton | None = None,
            oled: IOled | None = None,
            audio: IAudio | None = None,
            bluetooth: IBluetooth | None = None
        ) -> None:

        self.btn = btn if btn is not None else IButton()
        self.oled = oled if oled is not None else IOled()
        self.audio = audio if audio is not None else IAudio()
        self.bluetooth = bluetooth if bluetooth is not None else IBluetooth()

class MenuElement:
    img: Image
    title: str
    call_back: Callable[[], int]

    def __init__(self, img: Image, call_back: Callable[[], int], title=''):
        self.img = img
        self.call_back = call_back
        self.title = title
    
    def indicate(self) -> Image:
        raise NotImplementedError()

class Menu:
    select_index: int
    hide_arrow: bool
    item_list: Sequence[MenuElement]
    item_height: int
    logger = logging.getLogger('menus')
    logger.setLevel(LOGGER_LEVEL)

    def __init__(self, item_list: Sequence[MenuElement], item_height: int):
        self.hide_arrow = False
        self.select_index = 0
        self.item_list = item_list
        self.item_height = item_height

    def move_up(self):
        if self.select_index > 0:
            self.select_index -= 1
        else:
            self.logger.info('Cannot move up')

    def move_down(self):
        if self.select_index < len(self.item_list) - 1:
            self.select_index += 1
        else:
            self.logger.info('Cannot move down')

    def select(self) -> int:
        if not self.item_list:
            self.logger.info('No items in menu, staying in current state')
            return MENU_STATE_BT
        return self.item_list[self.select_index].call_back()

    def list_img(self) -> Image:
        img = new('1', (SCREEN_WIDTH, SCREEN_HEIGHT))
        draw = ImageDraw.Draw(img)
        draw.rectangle((0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), outline=0, fill=0)
        
        mid_pixel = (SCREEN_HEIGHT - self.item_height) // 2
        if self.item_list:
            img.paste(self.item_list[self.select_index].indicate(), (0, mid_pixel))
            self.logger.debug(f'Place selected item \"{self.item_list[self.select_index].title}\" at {mid_pixel}')

            offset_pixel = mid_pixel - self.item_height
            offset_index = self.select_index - 1
            while (offset_pixel > 0) and (offset_index >= 0):
                img.paste(self.item_list[offset_index].img, (0, offset_pixel))
                offset_pixel -= self.item_height
                offset_index -= 1
                
            offset_pixel = mid_pixel + self.item_height
            offset_index = self.select_index + 1
            while (offset_pixel < SCREEN_HEIGHT - self.item_height) and (offset_index < len(self.item_list)):
                img.paste(self.item_list[offset_index].img, (0, offset_pixel))
                offset_pixel += self.item_height
                offset_index += 1

        if self.select_index > 0 and not self.hide_arrow:
            up_triangle = [
                (SCREEN_WIDTH - 3, 2),
                (SCREEN_WIDTH - 5, 6),
                (SCREEN_WIDTH - 1, 6)
            ]
            draw.polygon(up_triangle, fill=255)

        if self.select_index < len(self.item_list) - 1 and not self.hide_arrow:
            down_triangle = [
                (SCREEN_WIDTH - 3, SCREEN_HEIGHT - 2),
                (SCREEN_WIDTH - 5, SCREEN_HEIGHT - 6),
                (SCREEN_WIDTH - 1, SCREEN_HEIGHT - 6)
            ]
            draw.polygon(down_triangle, fill=255)
            
        return img

class TextMenuElement(MenuElement):
    title: str

    def _str_cut(self, text: str) -> str:
        width = 0
        if text == None:
            return 'None'
        
        paste_text = ''

        for c in text:
            if 126 >= ord(c) >= 32:
                width += 1
            else:
                width += 2

            if width > MENU_MAX_TEXT_LEN:
                paste_text = paste_text[:-1] + '...'
                break
            else:
                paste_text += c

        return paste_text

    def __init__(self, text: str, call_back: Callable[[], int]):
        img = new('1', (128, MENU_TEXT_HEIGHT))
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(**MENU_FONT)

        draw.rectangle((0, 0, 128, MENU_TEXT_HEIGHT), outline=0, fill=0)
        paste_text = self._str_cut(text)

        draw.text((2, 0), paste_text, font=font, fill=255)

        super().__init__(img, call_back, text)

    def indicate(self) -> Image:
        img = new('1', (128, MENU_TEXT_HEIGHT))
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(**MENU_FONT)

        draw.rectangle((0, 0, 128, MENU_TEXT_HEIGHT), outline=0, fill=255)
        paste_text = self._str_cut(self.title)

        draw.text((2, 0), paste_text, font=font, fill=0)

        return img
    
    def __eq__(self, value: object):
        return self.title.__eq__(value)
    
class IconMenuElement(MenuElement):
    def __init__(self, img, call_back: Callable[[], int], title: str):
        super().__init__(img, call_back, title)

    def indicate(self) -> Image:
        return self.img