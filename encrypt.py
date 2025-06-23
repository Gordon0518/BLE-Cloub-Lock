import struct

def print_hex(bytes):
    l = [hex(int(i)) for i in bytes]
    return " ".join(l)

def hex_to_bytes(hex_str):
    return bytes.fromhex(hex_str)

def short_to_long(source):
    sourlen = len(source)
    turn = sourlen // 4
    remainder = sourlen % 4
    tarlen = turn + (1 if remainder else 0)
    target = [0] * tarlen
    for turn_iter in range(tarlen):
        for iter in range(4):
            if turn_iter != turn - 1 or (turn_iter == turn - 1 and (iter < remainder or remainder == 0)):
                target[turn_iter] = (target[turn_iter] << 8) + source[turn_iter * 4 + (3 - iter)]
    return target

def long_to_short(source):
    target = []
    ubfilter = 0xff
    for i in range(len(source)):
        for move in range(0, 32, 8):  
            target.append((source[i] >> move) & ubfilter)
    return target

def tea_encrypt_block(plain, key):
    if len(plain) != 8 or len(key) != 16:
        raise ValueError(f"Plaintext must be 8 bytes (got {len(plain)}), key must be 16 bytes (got {len(key)})")

    
    plain_bytes = list(plain)
    key_bytes = list(key)

    
    v = short_to_long(plain_bytes)
    k = short_to_long(key_bytes)

    
    delta = 0x9e3779b9
    sum_val = 0
    rounds = 8  
    mask = 0xffffffff

    y, z = v[0], v[1]
    a, b, c, d = k[0], k[1], k[2], k[3]

    
    for _ in range(rounds):
        sum_val = (sum_val + delta) & mask
        y = (y + (((z << 4) + a) ^ (z + sum_val) ^ ((z >> 5) + b))) & mask
        z = (z + (((y << 4) + c) ^ (y + sum_val) ^ ((y >> 5) + d))) & mask

    
    w = [y, z]
    result = long_to_short(w)
    return bytes(result[:8])  

def encrypt_frame(instruction_code, rolling_code, mac, params, timestamp, key):
   
    
    try:
        instruction_code_bytes = hex_to_bytes(instruction_code)
        rolling_code_bytes = hex_to_bytes(rolling_code)
        mac_bytes = hex_to_bytes(mac)
        params_bytes = hex_to_bytes(params) if params else b''
        timestamp_bytes = hex_to_bytes(timestamp)
        key_bytes = key  
    except ValueError as e:
        raise ValueError(f"Invalid hex string input: {e}")

   
    if len(instruction_code_bytes) != 1 or not (0x00 <= instruction_code_bytes[0] <= 0xff):
        raise ValueError(f"Instruction code must be 1 byte (0-255), got {instruction_code}")
    if len(rolling_code_bytes) != 1 or not (0x00 <= rolling_code_bytes[0] <= 0x7f):
        raise ValueError(f"Rolling code must be 1 byte (0-127), got {rolling_code}")
    if len(mac_bytes) != 6:
        raise ValueError(f"MAC must be 6 bytes, got {len(mac_bytes)}")
    if len(key_bytes) != 16: 
        raise ValueError(f"Key must be 16 bytes, got {len(key_bytes)}")
    if len(timestamp_bytes) != 6:
        raise ValueError(f"Timestamp must be 6 bytes, got {len(timestamp_bytes)}")

    
    data_to_encrypt = mac_bytes + params_bytes + timestamp_bytes

    
    data_length = len(data_to_encrypt) + 1  

    
    header = instruction_code_bytes + rolling_code_bytes + data_length.to_bytes(2, 'big')

    
    checksum_data = header + data_to_encrypt
    checksum = sum(checksum_data) & 0xff
    data_to_encrypt += bytes([checksum])

    
    if len(data_to_encrypt) % 8 != 0:
        data_to_encrypt += b'\x00' * (8 - len(data_to_encrypt) % 8)

    
    encrypted_data = b''
    for i in range(0, len(data_to_encrypt), 8):
        block = data_to_encrypt[i:i+8]
        encrypted_data += tea_encrypt_block(block, key_bytes)

    
    frame = header + encrypted_data
    return frame

# # Test
# if __name__ == "__main__":
#     # Default key
#     default_key = bytes.fromhex("11223344112233441122334411223344")

#     # Verify key length
#     print(f"Key length: {len(default_key)} bytes")

#     # Test case inputs as hex strings
#     instruction_code = "1f"
#     rolling_code = "00"
#     mac = "c10101017608"
#     params = ""  # No parameters
#     timestamp = "19060C0A011E"  # 2025-06-12 10:01:30

#     # Encrypt frame
#     try:
#         frame = encrypt_frame(instruction_code, rolling_code, mac, params, timestamp, default_key)
#         print(f"Encrypted frame: {frame.hex().upper()}")
#     except Exception as e:
#         print(f"Error: {e}")


        