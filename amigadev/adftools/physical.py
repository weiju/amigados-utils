"""physical.py - Physical aspects of an Amiga Volume"""
import struct

class Sector:
    """Sector is a partial view on a physical volume"""
    def __init__(self, data):
        self.data = data  # array of bytes

    def __getitem__(self, bytenum):
        return self.data[bytenum]

    def size_in_bytes(self):
        return len(self.data)

    def __setitem__(self, bytenum, value):
        self.data[bytenum] = value

    def u16_at(self, bytenum):
        return struct.unpack(">H", self.data[bytenum:bytenum + 2])[0]

    def u32_at(self, bytenum):
        return struct.unpack(">I", self.data[bytenum:bytenum + 4])[0]

    def i32_at(self, bytenum):
        return struct.unpack(">i", self.data[bytenum:bytenum + 4])[0]


# Double Density Disk numbers
DDD_BYTES_PER_SECTOR = 512
DDD_SECTORS_PER_TRACK = 11
DDD_TRACKS_PER_CYLINDER = 2
DDD_CYLINDERS_PER_DISK = 80
DDD_SECTORS_TOTAL = DDD_CYLINDERS_PER_DISK * DDD_TRACKS_PER_CYLINDER * DDD_SECTORS_PER_TRACK
DDD_IMAGE_SIZE = DDD_BYTES_PER_SECTOR * DDD_SECTORS_TOTAL


class DoubleDensityDisk:
    def __init__(self):
        self.data = bytearray(DDD_IMAGE_SIZE)

    def __getitem__(self, bytenum):
        return self.data[bytenum]

    def __setitem__(self, bytenum, value):
        self.data[bytenum] = value

    def i32_at(self, bytenum):
        """returns signed 32 bit integer value"""
        return struct.unpack(">i", self.data[bytenum:bytenum + 4])[0]

    def sector(self, sector_num):
        idx = sector_num * DDD_BYTES_PER_SECTOR
        # slicing the bytearray creates an independent copy, but we want a
        # Sector be a view that writes to the underlying array, so we create
        # memoryview, and slice it to achive the dessired effect
        return Sector(memoryview(self.data)[idx:idx + DDD_BYTES_PER_SECTOR])

    def write_image(file):
        file.write(self.data)


def read_ddd_image(file):
    data = file.read()
    if len(data) != DDD_IMAGE_SIZE:
        raise Exception("Wrong image size !!! (expected %d but was %d)" % (DDD_IMAGE_SIZE, len(data)))
    result = DoubleDensityDisk()
    result.data = data
    return result
