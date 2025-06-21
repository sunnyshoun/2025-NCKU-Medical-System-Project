import logging
import asyncio
from typing import Callable
from PIL.Image import Image as Img
from .models import Menu, TextMenuElement, IconMenuElement, MenuBase
from data.draw import *
from bluetooth_headset.model import Device
from config_manager import get_config_value
from settings import *

_LOGGER = logging.getLogger('menu')

def bluetooth_enter_callback() -> int:
    _LOGGER.info('Enter bluetooth')
    return MENU_STATE_BT
    
def volume_enter_callback() -> int:
    _LOGGER.info('Enter volume')
    return MENU_STATE_VOLUME

async def wrap_bluetooth_select_callback(bt_device: Device, menu: 'MainMenu') -> int:
    asyncio.create_task(menu.show_loading_animation())
    success = await menu.bluetooth.connect_bt_device(bt_device)
    if success:
        menu.bt_device = bt_device
        _LOGGER.info(f'Connect to \"{bt_device.device_name}\"')
    else:
        menu.bt_device = None
        _LOGGER.info(f'Fail to connect \"{bt_device.device_name}\"')
    await menu.stop_loading_animation()
    return MENU_STATE_ROOT

async def wrap_volume_select_callback(menu: 'MainMenu', p: int) -> int:
    _LOGGER.info(f'Set volume to {p}%')
    await menu.audio.set_volume(p)
    return MENU_STATE_ROOT

class MainMenu(MenuBase):
    root_menu: Menu
    bluetooth_menu: Menu
    volume_menu: Menu

    state: int
    ns: int

    bt_device: Device | None
    robot_controller: any

    loading_frames: list[Img]
    is_loading: bool
    is_navigating: bool
    stop_update: asyncio.Event
    oled_lock: asyncio.Lock

    def __init__(self, tester_func: Callable[[], int], robot_controller=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        self.robot_controller = robot_controller
        
        root_ele = [
            IconMenuElement(draw_start_icon(), tester_func, 'start'),
            IconMenuElement(draw_bluetooth_icon(), bluetooth_enter_callback, 'bluetooth'),
            IconMenuElement(draw_volume_icon(), volume_enter_callback, 'volume'),
        ]
        self.root_menu = Menu(root_ele, SCREEN_HEIGHT)

        self.bluetooth_menu = Menu([], MENU_TEXT_HEIGHT)

        volume_ele = [
            TextMenuElement(f'{p}%', lambda x=p: wrap_volume_select_callback(self, x)) for p in range(0, 101, 5)
        ]
        
        self.volume_menu = Menu(volume_ele, MENU_TEXT_HEIGHT)

        self.state = MENU_STATE_ROOT
        self.ns = MENU_STATE_ROOT

        self.bt_device = None
        
        self.loading_frames = draw_loading_frames()
        self.is_loading = False
        self.is_navigating = False
        self.stop_update = asyncio.Event()
        self.oled_lock = asyncio.Lock()

    async def initialize_bluetooth(self):
        try:
            default_device = Device('default', get_config_value('HEADPHONE_DEVICE_MAC') or 'none')
            connect_result = await self.bluetooth.connect_bt_device(default_device)
            if connect_result:
                self.bt_device = default_device
            _LOGGER.info(f'Connect to default device: {connect_result}')
        except Exception as e:
            _LOGGER.error(f'Failed to connect to default device: {e}')

    def is_phone_connected(self) -> bool:
        return self.robot_controller and self.robot_controller.phone_handler and self.robot_controller.phone_handler.is_connected()

    async def start_bluetooth_update(self):
        self.stop_update.clear()
        _LOGGER.info("Started bluetooth update task")
        asyncio.create_task(self._update_bluetooth_loop())

    async def stop_bluetooth_update(self):
        self.stop_update.set()
        _LOGGER.info("Requested stop for bluetooth update task")

    async def _update_bluetooth_loop(self):
        while not self.stop_update.is_set():
            if self.state == MENU_STATE_BT and not self.is_loading and not self.is_navigating:
                _LOGGER.debug("Conditions met, refreshing bluetooth")
                await self.refresh_bluetooth()
            await asyncio.sleep(3)

    async def _reset_navigation(self):
        self.is_navigating = False
        _LOGGER.debug("Navigation ended, resuming bluetooth updates")

    async def show_loading_animation(self):
        _LOGGER.info('Starting loading animation')
        self.is_loading = True
        frame_interval = 0.05
        frame_count = len(self.loading_frames)
        frame_index = 0
        while self.is_loading:
            async with self.oled_lock:
                self.oled.clear()
                self.oled.set_img(self.loading_frames[frame_index])
                self.oled.display()
            frame_index = (frame_index + 1) % frame_count
            await asyncio.sleep(frame_interval)

    async def stop_loading_animation(self):
        _LOGGER.info('Stopping loading animation')
        self.is_loading = False
        async with self.oled_lock:
            self.oled.clear()
            self.oled.display()
        

    async def refresh_bluetooth(self):
        _LOGGER.debug('Refresh bluetooth')
        try:
            bluetooth_device_list = await self.bluetooth.list_bt_device()
        except Exception as e:
            _LOGGER.error(f'Failed to list bluetooth devices: {e}')
            bluetooth_device_list = []
        
        current_device_name = None
        if self.bluetooth_menu.item_list and 0 <= self.bluetooth_menu.select_index < len(self.bluetooth_menu.item_list):
            current_device_name = self.bluetooth_menu.item_list[self.bluetooth_menu.select_index].title

        if not bluetooth_device_list:
            bluetooth_ele = [TextMenuElement("No Devices", lambda: MENU_STATE_BT)]
            _LOGGER.debug('No Bluetooth devices found, setting placeholder')
        else:
            bluetooth_ele = [
                TextMenuElement(
                    text=device.device_name,
                    call_back=lambda: wrap_bluetooth_select_callback(device, self)
                ) for device in bluetooth_device_list
            ]

        self.bluetooth_menu.item_list = bluetooth_ele

        if current_device_name:
            for i, item in enumerate(bluetooth_ele):
                if item.title == current_device_name:
                    self.bluetooth_menu.select_index = i
                    _LOGGER.debug(f'Restored selection to "{current_device_name}" at index {i}')
                    break
            else:
                self.bluetooth_menu.select_index = 0
                _LOGGER.debug(f'Device "{current_device_name}" not found, reset to index 0')
        else:
            self.bluetooth_menu.select_index = 0

        if self.bluetooth_menu.select_index >= len(self.bluetooth_menu.item_list):
            self.bluetooth_menu.select_index = max(0, len(self.bluetooth_menu.item_list) - 1)
            _LOGGER.debug(f'Adjusted select_index to {self.bluetooth_menu.select_index}')

        _LOGGER.debug(f'Set bluetooth list to {[item.title for item in bluetooth_ele]}')

        if self.state == MENU_STATE_BT:
            async with self.oled_lock:
                self.oled.clear()
                self.oled.set_img(self.bluetooth_menu.list_img())
                self.oled.display()

    def _current_menu(self) -> Menu:
        menus = {
            MENU_STATE_ROOT: self.root_menu,
            MENU_STATE_BT: self.bluetooth_menu,
            MENU_STATE_VOLUME: self.volume_menu
        }
        r = menus.get(self.state)
        if r is None:
            raise ValueError(f'Unknown state: {self.state}')
        return r

    async def loop(self):
        if self.robot_controller:
            if self.robot_controller.is_phone_mode() or \
            (self.robot_controller.test_coordinator and self.robot_controller.test_coordinator.is_test_active()):
                await asyncio.sleep(0.5)  # 短暫等待，減少 CPU 使用
                return
        
        _LOGGER.debug(f'Enter loop with cs: {self.state}, ns: {self.ns}')
        
        if self.bt_device is None:
            _LOGGER.debug('Not connected to bluetooth device')
            if self.state != MENU_STATE_BT and self.ns != MENU_STATE_BT:
                self.ns = MENU_STATE_ROOT
                self.root_menu.select_index = 1
            self.root_menu.hide_arrow = True
        else:
            self.root_menu.hide_arrow = False

        goto_funcs = {
            MENU_STATE_ROOT: self._goto_root,
            MENU_STATE_BT: self._goto_bt,
            MENU_STATE_VOLUME: self._goto_volume
        }
        goto_func = goto_funcs.get(self.ns)
        if self.state != self.ns:
            if goto_func is None:
                raise ValueError(f'Unknown state: {self.ns}')
            else:
                await goto_func()

        self.state = self.ns
        current_menu = self._current_menu()
        _LOGGER.debug(f'Selected index: {current_menu.select_index}')

        if self.state == MENU_STATE_ROOT:
            if current_menu.select_index == 1:
                if self.bt_device is None:
                    current_menu.item_list[1].img = cross(draw_bluetooth_icon())
                else:
                    current_menu.item_list[1].img = check(draw_bluetooth_icon())

        async with self.oled_lock:
            self.oled.clear()
            self.oled.set_img(current_menu.list_img())
            self.oled.display()

        try:
            btn = await asyncio.to_thread(self.btn.read_btn)
            _LOGGER.debug(f'Got btn {btn}')
            btn_events = {
                BTN_UP: current_menu.move_up,
                BTN_CONFIRM: current_menu.select,
                BTN_DOWN: current_menu.move_down
            }
            callee = btn_events.get(btn)
            if callee is None:
                raise ValueError(f'Unknown btn: {btn}')
            else:
                if btn in (BTN_UP, BTN_DOWN):
                    self.is_navigating = True
                    _LOGGER.debug("Navigation started, pausing bluetooth updates")
                    await self._reset_navigation()
                next_state = await callee() if asyncio.iscoroutinefunction(callee) else callee()
                if next_state is not None:
                    if asyncio.iscoroutine(next_state):
                        next_state = await next_state
                    self.ns = next_state
        except Exception as e:
            _LOGGER.error(f'Button handling error: {e}')
            await asyncio.sleep(0.1)

    async def _goto_volume(self):
        _LOGGER.info('Change to volume')
        self.volume_menu.select_index = self.audio.get_volume() // 5

    async def _goto_bt(self):
        _LOGGER.info('Change to bt')
        await self.refresh_bluetooth()
        await self.start_bluetooth_update()

    async def _goto_root(self):
        _LOGGER.info('Change to root')
        await self.stop_bluetooth_update()