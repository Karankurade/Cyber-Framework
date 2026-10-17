def hashing_algo(password):
    h = 0xABCDEF01
    for char in password:
        h ^= ord(char)
        h = (h << 5) | (h >> 27)
        h *= 0x45d9f3b
        h &= 0xFFFFFFFF

    return hex(h)



