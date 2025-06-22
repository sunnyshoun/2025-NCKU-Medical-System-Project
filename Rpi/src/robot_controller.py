import logging
import asyncio
from typing import Optional
from settings import *
from data.draw import draw_phone_icon
from hardwares import Motor, Oled, Sonic, Button
from rpi.resource import Audio, Bluetooth, SttAPI
from rpi.menu import MainMenu
from phone_handler import PhoneHandler
from test_coordinator import TestCoordinator


class RobotController:
    def __init__(self):
        self.logger = logging.getLogger("RobotController")
        
        self.motor = Motor()
        self.sonic = Sonic()
        self.button = Button()
        self.oled = Oled()
        
        self.audio = Audio()
        self.bluetooth = Bluetooth()
        self.stt = SttAPI()
        
        self.current_mode = "button"
        self.mode_lock = asyncio.Lock()
        
        self.phone_handler: Optional[PhoneHandler] = None
        self.test_coordinator: Optional[TestCoordinator] = None
        self.menu: Optional[MainMenu] = None
        
        self.is_running = False
        
    async def start(self):
        self.is_running = True
        
        await self._initialize_components()
        await self.menu.initialize_bluetooth()
        await self.phone_handler.start()
        
        asyncio.create_task(self._menu_loop())
    
    async def stop(self):
        self.is_running = False
        
        if self.phone_handler:
            await self.phone_handler.stop()
        
        if self.test_coordinator:
            self.test_coordinator.stop_test()
    
    async def _initialize_components(self):
        self.phone_handler = PhoneHandler(self)
        
        self.test_coordinator = TestCoordinator(
            motor=self.motor,
            oled=self.oled,
            sonic=self.sonic,
            audio=self.audio,
            stt=self.stt,
            phone_handler=self.phone_handler
        )
        
        self.menu = MainMenu(
            tester_func=self._start_button_test,
            btn=self.button,
            oled=self.oled,
            audio=self.audio,
            bluetooth=self.bluetooth,
            robot_controller=self
        )
    
    async def _menu_loop(self):
        while self.is_running:
            try:
                async with self.mode_lock:
                    current_mode = self.current_mode
                
                if self.test_coordinator and self.test_coordinator.is_test_active():
                    await asyncio.sleep(0.5)
                    continue
                    
                if current_mode == "button":
                    if self.menu:
                        await self.menu.loop()
                elif current_mode == "phone":
                    await self._show_phone_connected()
                        
            except Exception as e:
                self.logger.error(f"Menu loop error: {e}")
                await asyncio.sleep(1)
    
    async def _show_phone_connected(self):
        await self.show_phone_connected_status()
        await asyncio.sleep(1)
    
    async def show_phone_connected_status(self):
        try:
            img = draw_phone_icon()
            self.oled.clear()
            self.oled.set_img(img)
            self.oled.display()
        except Exception as e:
            self.logger.error(f"Show phone icon failed: {e}")
    
    async def switch_to_phone_mode(self):
        async with self.mode_lock:
            if self.current_mode != "phone":
                if self.test_coordinator and self.test_coordinator.is_test_active():
                    self.test_coordinator.stop_test()
                
                self.current_mode = "phone"
                
                if self.menu:
                    self.menu.state = MENU_STATE_ROOT
                    self.menu.ns = MENU_STATE_ROOT
                    await self.menu.stop_bluetooth_update()
                
                await self.show_phone_connected_status()
    
    async def switch_to_button_mode(self):
        async with self.mode_lock:
            if self.current_mode != "button":
                self.current_mode = "button"
                
                if self.menu:
                    self.menu.state = MENU_STATE_ROOT
                    self.menu.ns = MENU_STATE_ROOT
                
                if self.test_coordinator:
                    self.test_coordinator.stop_test()
    
    def is_phone_mode(self) -> bool:
        return self.current_mode == "phone"
    
    def is_button_mode(self) -> bool:
        return self.current_mode == "button"
    
    def _start_button_test(self) -> int:
        if self.is_phone_mode():
            return MENU_STATE_ROOT
        
        if self.test_coordinator:
            success = self.test_coordinator.start_button_test()
            if success:
                self.button.read_btn()
        
        return MENU_STATE_ROOT
    
    def start_phone_test(self) -> bool:
        if self.is_button_mode():
            self.logger.warning("Cannot start phone test in button mode")
            return False
        
        if not self.test_coordinator:
            self.logger.error("Test coordinator not initialized")
            return False
        
        return self.test_coordinator.start_phone_test()
    
    def get_system_status(self) -> dict:
        return {
            "mode": self.current_mode,
            "is_running": self.is_running,
            "phone_connected": self.phone_handler.is_connected() if self.phone_handler else False,
            "test_active": self.test_coordinator.is_test_active() if self.test_coordinator else False
        }