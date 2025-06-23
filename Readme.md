##Intruduction

    -The Cloud Lock allow user to connect it via bluetooth

##Key Features

    -The user can use the following Features:  
        1. Lock with new key
        2. Unlock
        3. Get unlock record
        4. Enable/Disable Sleep mode
        5. Set device name
        6. Reset the lock to default setting
        7. Read status of the Lock


##Project Structure

     -Lock.py: main class of the program
     -Encryption.py: Class for encryt the command before sending to the device
     -Record.py : Handle the 0x02 command when device responses the record 

        
    
    
##Guide to Use key Function
    
    -All command sent to device require encryption except command 0x01 (initialize)
    
    1. Connect (async def connect(self))
        -Connect the device though BLE connection
        
        -input : blue_address (e.g "C1:01:01:01:76:08")
                 key (default key : 123456789abcef0123456789abcddeef)


        -Call initialize() after connected to ensure timestamp between the device mathched

        -Every function should be run after connect()
            
        Example:
            lock1 = Lock(ble_address="C1:01:01:01:76:08", key="123456789abcef0123456789abcddeef")
            await lock1.connect()


    2. Initialize (async def initialize(self)) (0x01)
        -Generates timestamp and combinate with the command to sent to deice
        
        -Ensure the timestamp are correct, orelse some function may not work properly

        -using in connect()

    
    3. Lock (async def lock(self, Key)) (0x10)
        -Set new key for the device
    
        -Key MUST be 32 character (e.g., "11223344112233441122334411223344")

        Example:
            await lock1.lock("11223344112233441122334411223344")
        
    4. Unlock (async def unlock(self)) (0xe0)
        -Send encrypted command with KEY to open the lock

        -Timestamp MUST be accurate to unlock

        Example:
            await lock1.unlock()

    5. Get unlock record (async def get_record(self, num)) (0x02)
        -Get the unlock record from the device

        -Input the number of record user want to see

        Example:
            await lock1.get_record(3)
        
        Example Output:
            Record requested: 3
 
            Record 1:
                Timestamp: 2025-06-18 11:54:50
                Battery%: 98
            Record 2:
                Timestamp: 2025-06-18 11:54:52
                Battery%: 98
            Record 3:
                Timestamp: 2025-06-18 14:47:36
                Battery%: 98
    
    
    6. Set Device Name (async def set_name(self, name)) (0x12)
       -Set new name for the devices

       -Name only accept Chinese, English, Number

       -Input the name that user want to set for the device

       Example:
            lock1.set_name("大門鎖")

    
    7. Reset to default (async def reset(self)) (0x1f)
       -Restore the setting to default
        
       -Reset the key to default("123456789abcef0123456789abcddeef")

       Example:
            lock1.reset()

    
    8. Sleep Mode (async def sleep_mode(self, on)) (0x06)
       -Default sleep mode on
    
       -Disable sleep mode = device open bluetooth continusly
        
        - 0 = on, 1 = off
        Example:
            lock1.sleep_mode(0) #turn on
            lock1.sleep_mode(1) #turn off

    9.Disconnect (async def disconnect(self)) 
        -Disconnect with the device
        
        Example:
            lock1.disconnect()

    

##Example Usage

    import asyncio
    from lock import Lock

    async def main():
        lock1 = Lock(ble_address="C1:01:01:01:01:01", key = "123456789abcef0123456789abcddeef")
        await lock1.connect()
        await lock1.unlock()
        await lock1.get_record(3)
        await lcok1.set_name("Door_Lock")
        await lcok1.reset()
        await lock1.disconnect()

    if __name__ == "__main__":
        asyncio.run(main())
    

        
        
        
        
            
        

        

                 

                 

    
    

