#!/usr/bin/env python3
"""
樹莓派 BLE 服務器 - 使用 BlueZ D-Bus API
支援 Flutter App 雙向通訊
需要安裝: pip install dbus-python pygobject
"""

import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service
import json
import os
import threading
import time
from datetime import datetime
from gi.repository import GLib

# D-Bus 相關常數
BLUEZ_SERVICE_NAME = 'org.bluez'
GATT_MANAGER_IFACE = 'org.bluez.GattManager1'
DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'
GATT_SERVICE_IFACE = 'org.bluez.GattService1'
GATT_CHRC_IFACE = 'org.bluez.GattCharacteristic1'
GATT_DESC_IFACE = 'org.bluez.GattDescriptor1'
LE_ADVERTISING_MANAGER_IFACE = 'org.bluez.LEAdvertisingManager1'
LE_ADVERTISEMENT_IFACE = 'org.bluez.LEAdvertisement1'

class InvalidArgsException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.freedesktop.DBus.Error.InvalidArgs'

class NotSupportedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.NotSupported'

class NotPermittedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.NotPermitted'

class InvalidValueLengthException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.InvalidValueLength'

class FailedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.Failed'

class Advertisement(dbus.service.Object):
    PATH_BASE = '/org/bluez/ldsg/advertisement'

    def __init__(self, bus, index, advertising_type):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.ad_type = advertising_type
        self.service_uuids = None
        self.manufacturer_data = None
        self.solicit_uuids = None
        self.service_data = None
        self.local_name = None
        self.include_tx_power = False
        self.data = None
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        properties = dict()
        properties['Type'] = self.ad_type
        if self.service_uuids is not None:
            properties['ServiceUUIDs'] = dbus.Array(self.service_uuids, signature='s')
        if self.solicit_uuids is not None:
            properties['SolicitUUIDs'] = dbus.Array(self.solicit_uuids, signature='s')
        if self.manufacturer_data is not None:
            properties['ManufacturerData'] = dbus.Dictionary(self.manufacturer_data, signature='qv')
        if self.service_data is not None:
            properties['ServiceData'] = dbus.Dictionary(self.service_data, signature='sv')
        if self.local_name is not None:
            properties['LocalName'] = dbus.String(self.local_name)
        if self.include_tx_power:
            properties['IncludeTxPower'] = dbus.Boolean(self.include_tx_power)
        if self.data is not None:
            properties['Data'] = dbus.Dictionary(self.data, signature='yv')
        return {LE_ADVERTISEMENT_IFACE: properties}

    def get_path(self):
        return dbus.ObjectPath(self.path)

    @dbus.service.method(DBUS_PROP_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != LE_ADVERTISEMENT_IFACE:
            raise InvalidArgsException()
        return self.get_properties()[LE_ADVERTISEMENT_IFACE]

    @dbus.service.method(LE_ADVERTISEMENT_IFACE, in_signature='', out_signature='')
    def Release(self):
        print('%s: Released!' % self.path)

class RaspberryPiAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, 'peripheral')
        self.local_name = 'RaspberryPi-BLE'
        self.service_uuids = ['12345678-1234-1234-1234-123456789abc']
        self.include_tx_power = True

class Service(dbus.service.Object):
    PATH_BASE = '/org/bluez/ldsg/service'

    def __init__(self, bus, index, uuid, primary):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.uuid = uuid
        self.primary = primary
        self.characteristics = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
            GATT_SERVICE_IFACE: {
                'UUID': self.uuid,
                'Primary': self.primary,
                'Characteristics': dbus.Array(
                    self.get_characteristic_paths(),
                    signature='o')
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_characteristic(self, characteristic):
        self.characteristics.append(characteristic)

    def get_characteristic_paths(self):
        result = []
        for chrc in self.characteristics:
            result.append(chrc.get_path())
        return result

    def get_characteristics(self):
        return self.characteristics

    @dbus.service.method(DBUS_PROP_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_SERVICE_IFACE:
            raise InvalidArgsException()
        return self.get_properties()[GATT_SERVICE_IFACE]

class Characteristic(dbus.service.Object):
    def __init__(self, bus, index, uuid, flags, service):
        self.path = service.path + '/char' + str(index)
        self.bus = bus
        self.uuid = uuid
        self.service = service
        self.flags = flags
        self.descriptors = []
        self.value = []
        self.notifying = False
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
            GATT_CHRC_IFACE: {
                'Service': self.service.get_path(),
                'UUID': self.uuid,
                'Flags': self.flags,
                'Descriptors': dbus.Array(
                    self.get_descriptor_paths(),
                    signature='o')
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_descriptor(self, descriptor):
        self.descriptors.append(descriptor)

    def get_descriptor_paths(self):
        result = []
        for desc in self.descriptors:
            result.append(desc.get_path())
        return result

    def get_descriptors(self):
        return self.descriptors

    @dbus.service.method(DBUS_PROP_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_CHRC_IFACE:
            raise InvalidArgsException()
        return self.get_properties()[GATT_CHRC_IFACE]

    @dbus.service.method(GATT_CHRC_IFACE, in_signature='a{sv}', out_signature='ay')
    def ReadValue(self, options):
        print('Default ReadValue called, returning: ' + repr(self.value))
        return self.value

    @dbus.service.method(GATT_CHRC_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        print('Default WriteValue called')
        self.value = value

    @dbus.service.method(GATT_CHRC_IFACE)
    def StartNotify(self):
        if self.notifying:
            print('Already notifying, nothing to do')
            return
        self.notifying = True

    @dbus.service.method(GATT_CHRC_IFACE)
    def StopNotify(self):
        if not self.notifying:
            print('Not notifying, nothing to do')
            return
        self.notifying = False

    @dbus.service.signal(DBUS_PROP_IFACE, signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed, invalidated):
        pass

class RxCharacteristic(Characteristic):
    """接收手機資料的特徵值"""
    def __init__(self, bus, index, service, message_handler):
        Characteristic.__init__(
            self, bus, index,
            '12345678-1234-1234-1234-123456789abe',
            ['write', 'write-without-response'],
            service)
        self.message_handler = message_handler

    def WriteValue(self, value, options):
        try:
            message = bytes(value).decode('utf-8')
            print(f'收到手機訊息: {message}')
            self.message_handler(message)
        except Exception as e:
            print(f'處理接收訊息時出錯: {e}')

class TxCharacteristic(Characteristic):
    """發送資料到手機的特徵值"""
    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            '12345678-1234-1234-1234-123456789abd',
            ['notify', 'read'],
            service)

    def send_message(self, message):
        if not self.notifying:
            print('沒有設備訂閱通知，無法發送訊息')
            return

        try:
            value = dbus.Array([dbus.Byte(b) for b in message.encode('utf-8')])
            self.value = value
            self.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])
            print(f'已發送訊息到手機: {message}')
        except Exception as e:
            print(f'發送訊息失敗: {e}')

class FileCharacteristic(Characteristic):
    """檔案傳輸特徵值"""
    def __init__(self, bus, index, service, file_handler):
        Characteristic.__init__(
            self, bus, index,
            '12345678-1234-1234-1234-123456789abf',
            ['write', 'write-without-response', 'notify', 'read'],
            service)
        self.file_handler = file_handler

    def WriteValue(self, value, options):
        try:
            data = bytes(value)
            self.file_handler(data)
        except Exception as e:
            print(f'處理檔案資料時出錯: {e}')

    def send_file_data(self, data):
        if not self.notifying:
            print('沒有設備訂閱檔案通知')
            return

        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            value = dbus.Array([dbus.Byte(b) for b in data])
            self.value = value
            self.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])
        except Exception as e:
            print(f'發送檔案資料失敗: {e}')

class RaspberryPiService(Service):
    """樹莓派主服務"""
    def __init__(self, bus, index):
        Service.__init__(self, bus, index, '12345678-1234-1234-1234-123456789abc', True)
        
        # 創建目錄
        os.makedirs("received_files", exist_ok=True)
        os.makedirs("send_files", exist_ok=True)
        
        # 檔案接收相關
        self.current_file = None
        self.file_buffer = bytearray()
        
        # 建立特徵值
        self.tx_char = TxCharacteristic(bus, 0, self)
        self.add_characteristic(self.tx_char)
        
        self.rx_char = RxCharacteristic(bus, 1, self, self.handle_message)
        self.add_characteristic(self.rx_char)
        
        self.file_char = FileCharacteristic(bus, 2, self, self.handle_file_data)
        self.add_characteristic(self.file_char)
        
        print("樹莓派 BLE 服務已創建")

    def handle_message(self, message):
        """處理接收到的訊息"""
        try:
            # 嘗試解析 JSON
            try:
                data = json.loads(message)
                self.process_json_message(data)
            except json.JSONDecodeError:
                # 處理純文字
                self.process_text_message(message)
        except Exception as e:
            print(f'處理訊息時出錯: {e}')

    def process_json_message(self, data):
        """處理 JSON 訊息"""
        msg_type = data.get('type', 'unknown')
        
        if msg_type == 'text':
            content = data.get('content', '')
            sender = data.get('sender', 'Flutter App')
            print(f"{sender}: {content}")
            
            # 回應確認
            response = {
                'type': 'text_received',
                'message': f'樹莓派已收到: {content}',
                'timestamp': datetime.now().isoformat()
            }
            self.send_to_phone(json.dumps(response, ensure_ascii=False))
            
        elif msg_type == 'ping':
            response = {
                'type': 'pong',
                'timestamp': datetime.now().isoformat()
            }
            self.send_to_phone(json.dumps(response, ensure_ascii=False))

    def process_text_message(self, message):
        """處理純文字訊息"""
        print(f"收到文字: {message}")
        
        response = {
            'type': 'text_received',
            'message': f'樹莓派已收到: {message}',
            'timestamp': datetime.now().isoformat()
        }
        self.send_to_phone(json.dumps(response, ensure_ascii=False))

    def handle_file_data(self, data):
        """處理檔案資料"""
        try:
            # 檢查是否為 JSON 控制訊息
            if data.startswith(b'{'):
                message = data.decode('utf-8')
                file_info = json.loads(message)
                
                if file_info.get('type') == 'file_start':
                    print(f"開始接收檔案: {file_info.get('filename')}")
                    self.current_file = {
                        'name': file_info.get('filename', 'unknown'),
                        'size': file_info.get('size', 0)
                    }
                    self.file_buffer = bytearray()
                    
                elif file_info.get('type') == 'file_end':
                    self.save_received_file()
            else:
                # 二進制檔案資料
                if self.current_file:
                    self.file_buffer.extend(data)
                    print(f"接收檔案資料: {len(data)} bytes")
                    
        except Exception as e:
            print(f"處理檔案資料時出錯: {e}")

    def save_received_file(self):
        """儲存接收到的檔案"""
        if self.current_file and self.file_buffer:
            try:
                filename = self.current_file['name']
                filepath = os.path.join('received_files', filename)
                
                with open(filepath, 'wb') as f:
                    f.write(self.file_buffer)
                    
                print(f"檔案已儲存: {filepath} ({len(self.file_buffer)} bytes)")
                
                # 發送確認
                response = {
                    'type': 'file_received',
                    'filename': filename,
                    'size': len(self.file_buffer),
                    'message': '檔案接收完成'
                }
                self.send_to_phone(json.dumps(response, ensure_ascii=False))
                
                self.current_file = None
                self.file_buffer = bytearray()
                
            except Exception as e:
                print(f"儲存檔案時出錯: {e}")

    def send_to_phone(self, message):
        """發送訊息到手機"""
        self.tx_char.send_message(message)

    def send_file_to_phone(self, filepath):
        """發送檔案到手機"""
        if not os.path.exists(filepath):
            print(f"檔案不存在: {filepath}")
            return
            
        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)
        
        try:
            # 發送檔案開始資訊
            file_start = {
                'type': 'file_start',
                'filename': filename,
                'size': filesize
            }
            self.file_char.send_file_data(json.dumps(file_start))
            
            # 等待一下
            time.sleep(0.5)
            
            # 分塊發送檔案
            chunk_size = 512
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    self.file_char.send_file_data(chunk)
                    time.sleep(0.1)
                    
            # 發送檔案結束
            file_end = {
                'type': 'file_end',
                'filename': filename
            }
            self.file_char.send_file_data(json.dumps(file_end))
            
            print(f"檔案已發送: {filename}")
            
        except Exception as e:
            print(f"發送檔案失敗: {e}")

class Application(dbus.service.Object):
    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)

    @dbus.service.method(DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}
        for service in self.services:
            response[service.get_path()] = service.get_properties()
            chrcs = service.get_characteristics()
            for chrc in chrcs:
                response[chrc.get_path()] = chrc.get_properties()
                descs = chrc.get_descriptors()
                for desc in descs:
                    response[desc.get_path()] = desc.get_properties()
        return response

def register_ad_cb():
    print('廣告註冊成功')

def register_ad_error_cb(error):
    print('廣告註冊失敗: ' + str(error))

def register_app_cb():
    print('GATT 應用程式註冊成功')

def register_app_error_cb(error):
    print('GATT 應用程式註冊失敗: ' + str(error))

def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()

    # 獲取 BlueZ 適配器
    adapter = None
    try:
        adapter = bus.get_object(BLUEZ_SERVICE_NAME, '/org/bluez/hci0')
        print("找到藍牙適配器")
    except:
        print("無法找到藍牙適配器")
        return

    # 獲取廣告管理器
    adapter_props = dbus.Interface(adapter, DBUS_PROP_IFACE)
    adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(1))

    ad_manager = dbus.Interface(adapter, LE_ADVERTISING_MANAGER_IFACE)
    gatt_manager = dbus.Interface(adapter, GATT_MANAGER_IFACE)

    # 創建應用程式
    app = Application(bus)
    service = RaspberryPiService(bus, 0)
    app.add_service(service)

    # 創建廣告
    advertisement = RaspberryPiAdvertisement(bus, 0)

    mainloop = GLib.MainLoop()

    # 註冊應用程式
    gatt_manager.RegisterApplication(app.get_path(), {},
                                    reply_handler=register_app_cb,
                                    error_handler=register_app_error_cb)

    # 註冊廣告
    ad_manager.RegisterAdvertisement(advertisement.get_path(), {},
                                   reply_handler=register_ad_cb,
                                   error_handler=register_ad_error_cb)

    print("樹莓派 BLE 服務器已啟動")
    print("服務 UUID: 12345678-1234-1234-1234-123456789abc")
    print("等待 Flutter App 連接...")
    
    # 啟動互動模式
    def input_thread():
        while True:
            try:
                user_input = input("輸入訊息 (或 'quit' 退出): ")
                if user_input.lower() == 'quit':
                    mainloop.quit()
                    break
                elif user_input.startswith('file:'):
                    filename = user_input[5:].strip()
                    filepath = os.path.join("send_files", filename)
                    if os.path.exists(filepath):
                        service.send_file_to_phone(filepath)
                    else:
                        print(f"檔案不存在: {filepath}")
                else:
                    service.send_to_phone(user_input)
            except EOFError:
                break
    
    thread = threading.Thread(target=input_thread, daemon=True)
    thread.start()

    try:
        mainloop.run()
    except KeyboardInterrupt:
        print("\n正在停止服務器...")
        mainloop.quit()

if __name__ == '__main__':
    main()