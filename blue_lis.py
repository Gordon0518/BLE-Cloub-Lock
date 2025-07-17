import asyncio
from bleak import BleakScanner
import asyncio
from bleak import BleakClient
import time
end_flag = False
def print_hex(bytes):
    l = [hex(int(i)) for i in bytes]
    return " ".join(l)
async def main():
    ble_address = "C1:01:01:01:76:08"
    characteristic_uuid = "0000fff1-0000-1000-8000-00805f9b34fb"

    async with BleakClient(ble_address) as client:

        def notification_handler(sender, data):
            global end_flag
            global constriction
            global diastolic
            global pulse
            print(f"{sender}: {print_hex(data)}")
            end_flag= True

        zone = '0100000dc10101017608'
        ts = time.strftime("%Y%m%d%H%M%S", time.localtime())
        ts = ts[2:]
        outs = ''
        for i in range(len(ts) // 2):
            curen = hex(int(ts[i * 2:i * 2 + 2]))[2:]
            if len(curen) < 2:
                curen = '0' + curen
            outs += curen
        tgt = zone + outs
        sum = 0
        outl=[]
        for i in range(len(tgt) // 2):
            sum += int(tgt[i * 2:i * 2 + 2], 16)
            outl.append("0x"+tgt[i * 2:i * 2 + 2])
            # print(int(tgt[i * 2:i * 2 + 2], 16))
        outl.append(hex(sum % (16 * 16)))
        result = [int(x, 16) for x in outl]
        data=tgt+hex(sum%(16*16))[2:]
        print(bytes.fromhex(data))
        # await client.start_notify("fff1", notification_handler)


        datar = await client.read_gatt_char("fff1")

        print_hex(datar)
        for i in range(1):
            tem = await client.write_gatt_char("fff2", bytes(result))
            print(print_hex(bytes(result)))
            await client.start_notify("fff1", notification_handler)
            datar = await client.read_gatt_char("fff1")
            print(print_hex(bytes(datar)))
            print(tem)

        # while not end_flag:
        #     await asyncio.sleep(1)

        await client.stop_notify("fff1")
asyncio.run(main())