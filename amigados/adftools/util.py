import struct
from datetime import datetime
import time


# AmigaDOS time is based on 1978/01/01, unlike UNIX time
AMIGADOS_BASE_TIME = datetime.strptime("1978-01-01 00:00:00.000", "%Y-%m-%d %H:%M:%S.%f")
AMIGADOS_BASE_MILLIS = int(AMIGADOS_BASE_TIME.timestamp() * 1000)
MILLISECONDS_PER_TICK = 20
MILLISECONDS_PER_MINUTE = 1000 * 60
MILLISECONDS_PER_DAY = MILLISECONDS_PER_MINUTE * 60 * 24


def amigados_time_to_datetime(days_since_jan_1_78,
                              minutes_past_midnight,
                              ticks_past_last_minute):
    """Convert an AmigaDOS format time to a regular datetime object"""
    millis = (days_since_jan_1_78 * MILLISECONDS_PER_DAY +
              minutes_past_midnight * MILLISECONDS_PER_MINUTE +
              ticks_past_last_minute * MILLISECONDS_PER_TICK)
    return datetime.fromtimestamp((millis + AMIGADOS_BASE_MILLIS) / 1000)


def bootblock_checksum(data, num_bytes):
    """bootblock checksum function"""
    result = 0
    for i in range(0, num_bytes, 4):
        if i == 4:
            # ignore the checksum field itself for the computation
            continue
        d = struct.unpack(">I", data[i:i + 4])[0]
        result += d

        # 32-bit overflow, but Python has unlimited range, so we need to
        # simulate the overflow
        if result > 0xffffffff:
            result -= 0xffffffff

    return ~result & 0xffffffff


def headerblock_checksum(data, num_bytes, exclude_offset=20):
    """header block checksum function"""
    result = 0
    for i in range(0, num_bytes, 4):
        # ignore the checksum field itself for the computation
        if i == exclude_offset:
            continue
        d = struct.unpack(">I", data[i:i + 4])[0]
        result += d

        # 32-bit overflow, but Python has unlimited range, so we need to
        # simulate the overflow
        if result > 0xffffffff:
            result = result - 0xffffffff - 1

    return (-result) & 0xffffffff


def compute_hash(name, block_size):
    """non-international hash function"""
    hash = len(name)
    for i in range(len(name)):
        hash *= 13
        hash += ord(name[i].upper())
        hash &= 0x7ff
    hash %= ((block_size / 4) - 56)
    return int(hash)
