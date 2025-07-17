import asyncio
from bleak import BleakScanner
import time

DEVICE_ADDRESS = "FC:3D:11:6F:1E:D4"
SCAN_TIMEOUT = 1.0
RESCAN_DELAY = 1.0


def print_hex(bytes):
    l = [hex(int(i)) for i in bytes]
    return " ".join(l)

async def advertisement_handler(device, advertisement_data):
    if device.address.lower() == DEVICE_ADDRESS.lower():
        try:
            manufacturer_data = advertisement_data.manufacturer_data or {}
            print(f"Received advertisement from {device.address} at {time.strftime('%H:%M:%S')}")
            if manufacturer_data:
                for company_id, data in manufacturer_data.items():
                    decimal_values = print_hex(data)
                    print(f" {decimal_values}")
        except Exception as e:
            print(e)


async def scan_ble():
    while True:
        try:
            async with BleakScanner(detection_callback=advertisement_handler) as scanner:
                await asyncio.sleep(SCAN_TIMEOUT)
            await asyncio.sleep(RESCAN_DELAY)

        except Exception as e:
            print(f"Scan error: {e}")
            await asyncio.sleep(RESCAN_DELAY)

if __name__ == "__main__":
    asyncio.run(scan_ble())
