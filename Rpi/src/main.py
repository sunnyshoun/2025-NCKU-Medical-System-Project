# Entry of the app running on Raspberry Pi 3B+

import logging
import os
import datetime
import asyncio
from settings import *
from robot_controller import RobotController


async def setup_logging():
    """設置日誌系統"""
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
    
    # 抑制 Adafruit I2C 的詳細日誌
    logging.getLogger('Adafruit_I2C.Device.Bus.1.Address.0X3C').setLevel(logging.WARNING)


async def main():
    """主程式入口"""
    # 設置日誌
    await setup_logging()
    
    logger = logging.getLogger("Main")
    logger.info("啟動 EyeDwell 視力測試機器人...")
    
    # 創建機器人控制器
    controller = RobotController()
    
    try:
        # 啟動機器人控制器
        await controller.start()
        logger.info("系統啟動完成，等待操作...")
        
        # 保持程式運行
        while controller.is_running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("收到終止信號，正在關閉系統...")
    except Exception as e:
        logger.error(f"系統執行錯誤: {e}")
        import traceback
        logger.error(f"錯誤詳情: {traceback.format_exc()}")
    finally:
        try:
            await controller.stop()
            logger.info("系統已安全關閉")
        except Exception as e:
            logger.error(f"關閉系統時發生錯誤: {e}")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("程式被中斷")
    except Exception as e:
        print(f"程式執行失敗: {e}")
        import traceback
        traceback.print_exc()