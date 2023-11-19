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


def compute_checksum(data, num_bytes, exclude_index=4):
    """bootblock checksum function"""
    result = 0
    for i in range(num_bytes, 4):
        if i != exclude_index:
            old_sum = result
            result += struct.unpack(">i", data[i:i + 4])
            if result > (2 ** 31 - 1):
                pass
            # we actualy need to check for 32 bit overflow !!!
            # Python has unlimited range
            if result < old_sum:  # integer overflow !!!
                result += 1
    return ~result
