import asyncio


from bleak import BleakClient, BleakError 
import time
from datetime import datetime


import record
import encrypt
import urllib.parse


def is_chinese(char):
    return '\u4e00' <= char <= '\u9fff'


def encode_name(name):
    parmas = ""
    for i in range(len(name)):
        if (is_chinese(name[i])):
            encoded_text = urllib.parse.quote(name[i])
            parmas = parmas + encoded_text
        else:
            ascii_text = ord(name[i])
            encoded_text = hex(ascii_text)[2:].rjust(2, "0")
            parmas = parmas + encoded_text

    parmas = parmas.replace("%", "")
    return parmas



class Lock:

    def __init__(self, ble_address, key, characteristic_uuid="0000fff1-0000-1000-8000-00805f9b34fb", 
                 write_uuid="0000fff2-0000-1000-8000-00805f9b34fb", rolling_code = "00"):
        self.ble_address = ble_address
        self.key = bytes.fromhex(key)
        self.characteristic_uuid = characteristic_uuid
        self.write_uuid = write_uuid
        self.client = None
        self.response_flags = {"01": False, "10": False, "e0": False, "02": False, "1f": False, "13" : False}
        self.last_notification = None
        self.rolling_code = rolling_code


    ####Connect 
    async def connect(self):
        try:
            self.client = BleakClient(self.ble_address)
            await self.client.connect()
            print(f"Connected to device: {self.ble_address}")
            await self.initialize()
            if not self.client.is_connected:
                print("Connection failed")
                return False
            return True
        except BleakError as e:
            print(f"BLE Connection Error: {e}")
            return False
        
    ####Handle Response
    def _notification_handler(self, sender, data):
        current_notification = encrypt.print_hex(data)

        if current_notification == self.last_notification:
            print(f"Ignoring duplicate notification: {current_notification}")
            return
        self.last_notification = current_notification
        print(f"Notification received from {sender}: {current_notification}")
        instruction_code = f"{data[0]:02x}"

        if instruction_code in self.response_flags:
            self.response_flags[instruction_code] = True
        else:
            print(f"Unexpected response code: {instruction_code}")

    async def _clear_notifications(self):
        await self.client.start_notify(self.characteristic_uuid, lambda s, d: print("Cleared stale:", encrypt.print_hex(d)))
        await asyncio.sleep(0.1)
        await self.client.stop_notify(self.characteristic_uuid)


     ####Handle Record Respond
    def _record_handler(self, sender, data):
        current_notification = encrypt.print_hex(data)
        outl=[]
        if current_notification == self.last_notification:
            print(f"Ignoring duplicate notification: {current_notification}")
            return
        self.last_notification = current_notification
        print(f"Notification received from {sender}: {current_notification}")
        result = record.parse_record(current_notification)
        print(f"Record requested: {result['record_requested']}")
        for recordss in result['records']:
             print(f"Record {recordss['record']}:")
             print(f"  Timestamp: {recordss['time']}")
             print(f"  Battery%: {recordss['battery']}")
        instruction_code = f"{data[0]:02x}"

        if instruction_code in self.response_flags:
            self.response_flags[instruction_code] = True
        else:
            print(f"Unexpected response code: {instruction_code}")



    ####for command 0x02
    async def _send_frame_record(self, frame, instruction_code, timeout = 5):
        if not self.client.is_connected:
            print(f"Disconnected before sending 00x{instruction_code}")
            return False

        self.response_flags[instruction_code] = False
        self.last_notification = None
        await self._clear_notifications()
        await self.client.write_gatt_char(self.write_uuid, frame)
        print(f"Sent 0x{instruction_code} frame: {encrypt.print_hex(frame)}")
        print(f"Waiting for 0x{instruction_code} response")

        await self.client.start_notify(self.characteristic_uuid, self._record_handler)
        start_time = time.time()
        while not self.response_flags[instruction_code] and (time.time() - start_time) < timeout:
            await asyncio.sleep(0.1)

        await self.client.stop_notify(self.characteristic_uuid)
        if not self.response_flags[instruction_code]:
            print(f"No 0x{instruction_code} response received within timeout")
            return False
        return True



    #### Send Command
    async def _send_frame(self, frame, instruction_code, timeout=5):
        if not self.client.is_connected:
            print(f"Disconnected before sending 0x{instruction_code}")
            return False

        self.response_flags[instruction_code] = False
        self.last_notification = None 
        await self._clear_notifications()  
        await self.client.write_gatt_char(self.write_uuid, frame)
        print(f"Sent 0x{instruction_code} frame: {encrypt.print_hex(frame)}")
        print(f"Waiting for 0x{instruction_code} response")

        await self.client.start_notify(self.characteristic_uuid, self._notification_handler)
        start_time = time.time()
        while not self.response_flags[instruction_code] and (time.time() - start_time) < timeout:
            await asyncio.sleep(0.1)
        
        await self.client.stop_notify(self.characteristic_uuid) 
        if not self.response_flags[instruction_code]:
            print(f"No 0x{instruction_code} response received within timeout")
            return False
        return True


    #### 0x01 (Read State) Auto used when connect
    async def initialize(self):
        mac = self.ble_address.replace(":", "")
        zone = '0100000d' + mac
        now = datetime.now()
        timestamp = f"{now.year - 2000:02x}{now.month:02x}{now.day:02x}{now.hour:02x}{now.minute:02x}{now.second:02x}"
        tgt = zone + timestamp
        sum = 0
        outl = []

        for i in range(len(tgt) // 2):
            sum += int(tgt[i * 2:i * 2 + 2], 16)
            outl.append("0x" + tgt[i * 2:i * 2 + 2])
        outl.append(hex(sum % (16 * 16)))
        result = [int(x, 16) for x in outl]
        frame = bytes(result)

        return await self._send_frame(frame, "01")


    #### 0x10 (Lock) Set new KEY
    async def lock(self, params):
        instruction_code = "10"
        mac = self.ble_address.replace(":", "")
        now = datetime.now()
        timestamp = f"{now.year - 2000:02x}{now.month:02x}{now.day:02x}{now.hour:02x}{now.minute:02x}{now.second:02x}"
        encrypted_frame = encrypt.encrypt_frame(instruction_code, self.rolling_code, mac, params, timestamp, self.key)
        self.key = bytes.fromhex(params)
        return await self._send_frame(encrypted_frame, instruction_code)


    #### 0xe0 (unlock)
    async def unlock(self):
        instruction_code = "e0"
        mac = self.ble_address.replace(":", "")
        params = ""
        now = datetime.now()
        timestamp = f"{now.year - 2000:02x}{now.month:02x}{now.day:02x}{now.hour:02x}{now.minute:02x}{now.second:02x}"
        encrypted_frame = encrypt.encrypt_frame(instruction_code, self.rolling_code, mac, params, timestamp, self.key)
        return await self._send_frame(encrypted_frame, instruction_code)


    #### 0x02 (Record) Input how many record want to look for
    async def get_record(self, num):
        instruction_code = "02"
        mac = self.ble_address.replace(":", "")
        if num < 10:
            params = "00010" + str(num)
        else:
            params = "0001" + str(num)
        
        now = datetime.now()
        timestamp = f"{now.year - 2000:02x}{now.month:02x}{now.day:02x}{now.hour:02x}{now.minute:02x}{now.second:02x}"
        encrypted_frame = encrypt.encrypt_frame(instruction_code, self.rolling_code, mac, params, timestamp, self.key)
        return await self._send_frame_record(encrypted_frame, instruction_code)
    

    #### 0x1f (Reset) reset key to default
    async def reset(self):
        instruction_code = "14"
        mac = self.ble_address.replace(":", "")
        params = "02"
        now = datetime.now()
        timestamp = f"{now.year - 2000:02x}{now.month:02x}{now.day:02x}{now.hour:02x}{now.minute:02x}{now.second:02x}"
        encrypted_frame = encrypt.encrypt_frame(instruction_code, self.rolling_code, mac, params, timestamp, self.key)
        self.key = bytes.fromhex("123456789abcef0123456789abcddeef")
        return await self._send_frame(encrypted_frame, instruction_code)

    #### 0x06 Sleep Mode (On = 0, Off = 1)
    async def sleep_mode(self, on):
        instruction_code = "06"
        mac = self.ble_address.replace(":", "")
        if (on == 0):
            params = "00"
        else:
            params = "01"
        now = datetime.now()
        timestamp = f"{now.year - 2000:02x}{now.month:02x}{now.day:02x}{now.hour:02x}{now.minute:02x}{now.second:02x}"
        encrypted_frame = encrypt.encrypt_frame(instruction_code, self.rolling_code, mac, params, timestamp, self.key)
        return await self._send_frame(encrypted_frame, instruction_code)

    #### 0x12 (Set Device Name)
    async def set_name(self, name):
        instruction_code = "12"
        mac = self.ble_address.replace(":", "")

        encodeName = encode_name(name)
        byte_count = len(bytes.fromhex(encodeName))
        byte_count = hex(byte_count)[2:].rjust(2, "0")
        params = str(byte_count) + encodeName

        now = datetime.now()
        timestamp = f"{now.year - 2000:02x}{now.month:02x}{now.day:02x}{now.hour:02x}{now.minute:02x}{now.second:02x}"
        encrypted_frame = encrypt.encrypt_frame(instruction_code, self.rolling_code, mac, params, timestamp, self.key)
        return await self._send_frame(encrypted_frame, instruction_code)



    #### Disconnect
    async def disconnect(self):
        if self.client and self.client.is_connected:
            await asyncio.sleep(0.1)
            await self.client.disconnect()
            print("Disconnected from device")

    #### Test all
    async def operate(self):
        try:
            if not await self.connect():
                return
            if not await self.initialize():
                return
            await asyncio.sleep(1)
            if not await self.lock("11223344112233441122334411223344"):
                return
            if not await self.unlock():
                return
            if not await self.get_record(3):
                return
            if not await self.set_name("DoorLock"):
                return
            if not await self.reset():
                return
        except BleakError as e: 
            print(f"BLE Error: {e}")
            raise
        except Exception as e:
            print(f"Error: {e}")
            raise
        finally:
            await self.disconnect()


       
###Test
async def main():
    lock = Lock(ble_address="C1:01:01:01:76:08", key="123456789abcef0123456789abcddeef")
    await lock.connect()

    await lock.reset()
    await lock.disconnect()

if __name__ == "__main__":
    asyncio.run(main())

#!!!!!!!Default KEY: 123456789abcef0123456789abcddeef
#!!!!!!!Test KEY: 11223344112233441122334411223344
