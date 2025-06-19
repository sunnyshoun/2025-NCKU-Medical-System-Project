"""
機器人控制器 - 簡化版，只處理模式切換和基本協調
"""

import logging
import threading
import asyncio
from typing import Optional

from settings import *
from hardwares import Motor, Oled, Sonic, Button
from rpi.resource import Audio, Bluetooth, SttAPI
from rpi.menu import MainMenu
from phone_handler import PhoneHandler
from test_coordinator import TestCoordinator


class RobotController:
    """主要的機器人控制器，負責協調所有組件"""
    
    def __init__(self):
        self.logger = logging.getLogger("RobotController")
        
        # 硬體組件
        self.motor = Motor()
        self.sonic = Sonic()
        self.button = Button()
        self.oled = Oled()
        
        # 軟體資源
        self.audio = Audio()
        self.bluetooth = Bluetooth()
        self.stt = SttAPI()
        
        # 模式管理
        self.current_mode = "button"  # "button" 或 "phone"
        self.mode_lock = threading.Lock()
        
        # 組件
        self.phone_handler: Optional[PhoneHandler] = None
        self.test_coordinator: Optional[TestCoordinator] = None
        self.menu: Optional[MainMenu] = None
        
        # 狀態
        self.is_running = False
        self.menu_thread: Optional[threading.Thread] = None
        
    async def start(self):
        """啟動機器人控制器"""
        self.logger.info("啟動機器人控制器...")
        
        self.is_running = True
        
        # 初始化組件
        await self._initialize_components()
        
        # 啟動手機處理器
        await self.phone_handler.start()
        
        # 啟動選單循環（在獨立線程中）
        self._start_menu_thread()
        
        self.logger.info("機器人控制器啟動完成")
    
    async def stop(self):
        """停止機器人控制器"""
        self.logger.info("停止機器人控制器...")
        
        self.is_running = False
        
        # 停止手機處理器
        if self.phone_handler:
            await self.phone_handler.stop()
        
        # 等待選單線程結束
        if self.menu_thread and self.menu_thread.is_alive():
            self.menu_thread.join(timeout=5)
        
        self.logger.info("機器人控制器已停止")
    
    async def _initialize_components(self):
        """初始化所有組件"""
        # 創建手機處理器
        self.phone_handler = PhoneHandler(self)
        
        # 創建測試協調器
        self.test_coordinator = TestCoordinator(
            motor=self.motor,
            oled=self.oled,
            sonic=self.sonic,
            audio=self.audio,
            stt=self.stt,
            phone_handler=self.phone_handler
        )
        
        # 創建選單
        self.menu = MainMenu(
            tester_func=self._start_button_test,
            btn=self.button,
            oled=self.oled,
            audio=self.audio,
            bluetooth=self.bluetooth,
            robot_controller=self
        )
    
    def _start_menu_thread(self):
        """啟動選單循環線程"""
        self.menu_thread = threading.Thread(target=self._menu_loop, daemon=True)
        self.menu_thread.start()
    
    def _menu_loop(self):
        """選單循環（在獨立線程中運行）"""
        while self.is_running:
            try:
                with self.mode_lock:
                    current_mode = self.current_mode
                
                if current_mode == "button":
                    # 按鈕模式：正常運行選單
                    self.menu.loop()
                elif current_mode == "phone":
                    # 手機模式：顯示手機圖示並等待
                    self._show_phone_connected()
                    
            except Exception as e:
                self.logger.error(f"選單循環錯誤: {e}")
    
    def _show_phone_connected(self):
        """顯示手機已連線狀態"""
        self.show_phone_connected_status()
        
        # 等待一段時間
        import time
        time.sleep(1)
    
    def show_phone_connected_status(self):
        """顯示手機連線狀態（可被外部調用）"""
        from data.draw import draw_phone_icon
        
        # 使用draw.py繪製手機圖案，由oled控制模組更新螢幕
        img = draw_phone_icon()
        self.oled.clear()
        self.oled.set_img(img)
        self.oled.display()
        
        self.logger.debug("OLED顯示手機連線圖案")
    
    def switch_to_phone_mode(self):
        """切換到手機模式"""
        with self.mode_lock:
            if self.current_mode != "phone":
                self.logger.info("切換到手機模式")
                self.current_mode = "phone"
    
    def switch_to_button_mode(self):
        """切換到按鈕模式"""
        with self.mode_lock:
            if self.current_mode != "button":
                self.logger.info("切換到按鈕模式")
                self.current_mode = "button"
                # 停止當前測試
                if self.test_coordinator:
                    asyncio.create_task(self.test_coordinator.stop_test())
    
    def is_phone_mode(self) -> bool:
        """檢查是否為手機模式"""
        with self.mode_lock:
            return self.current_mode == "phone"
    
    def is_button_mode(self) -> bool:
        """檢查是否為按鈕模式"""
        with self.mode_lock:
            return self.current_mode == "button"
    
    def _start_button_test(self) -> int:
        """開始按鈕模式測試"""
        if self.is_phone_mode():
            # 手機模式下不允許按鈕測試
            self.logger.info("手機模式下，忽略按鈕測試請求")
            return MENU_STATE_ROOT
        
        # 開始按鈕模式測試
        self.test_coordinator.start_button_test()
        self.button.read_btn()  # 等待按鈕確認
        return MENU_STATE_ROOT
    
    async def start_phone_test(self):
        """開始手機模式測試"""
        if self.is_button_mode():
            self.logger.warning("按鈕模式下不能開始手機測試")
            return False
        
        return await self.test_coordinator.start_phone_test()
    
    def get_system_status(self) -> dict:
        """獲取系統狀態"""
        return {
            "mode": self.current_mode,
            "is_running": self.is_running,
            "phone_connected": self.phone_handler.is_connected() if self.phone_handler else False,
            "test_active": self.test_coordinator.is_test_active() if self.test_coordinator else False
        }