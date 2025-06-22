import logging
import os
import datetime
import asyncio
from settings import *
from robot_controller import RobotController


async def setup_logging():
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
    
    logging.getLogger('Adafruit_I2C.Device.Bus.1.Address.0X3C').setLevel(logging.WARNING)


async def main():
    await setup_logging()
    
    logger = logging.getLogger("Main")
    logger.info("Starting EyeDwell vision test robot...")
    
    controller = RobotController()
    
    try:
        await controller.start()
        logger.info("System started, waiting for operations...")
        
        while controller.is_running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received termination signal, shutting down...")
    except Exception as e:
        logger.error(f"System execution error: {e}")
        import traceback
        logger.error(f"Error details: {traceback.format_exc()}")
    finally:
        try:
            await controller.stop()
            logger.info("System safely shutdown")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program interrupted")
    except Exception as e:
        print(f"Program execution failed: {e}")
        import traceback
        traceback.print_exc()