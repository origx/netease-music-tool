import binascii


def meta_key_bytes():
    return binascii.a2b_hex("2331346C6A6B5F215C5D2630553C2728")


def unpad_bytes(data):
    pad_len = data[-1] if isinstance(data[-1], int) else ord(data[-1])
    return data[:-pad_len]