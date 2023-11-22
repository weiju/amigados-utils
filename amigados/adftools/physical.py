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


FLOPPY_CYLINDERS_PER_DISK = 80
FLOPPY_BYTES_PER_SECTOR = 512
FLOPPY_TRACKS_PER_CYLINDER = 2

# Double Density Disk numbers
DDD_SECTORS_PER_TRACK = 11
DDD_SECTORS_TOTAL = FLOPPY_CYLINDERS_PER_DISK * FLOPPY_TRACKS_PER_CYLINDER * DDD_SECTORS_PER_TRACK
DDD_IMAGE_SIZE = FLOPPY_BYTES_PER_SECTOR * DDD_SECTORS_TOTAL

# High density floppies have 22 sectors per track
HDD_SECTORS_PER_TRACK = 22
HDD_SECTORS_TOTAL = FLOPPY_CYLINDERS_PER_DISK * FLOPPY_TRACKS_PER_CYLINDER * HDD_SECTORS_PER_TRACK
HDD_IMAGE_SIZE = FLOPPY_BYTES_PER_SECTOR * HDD_SECTORS_TOTAL

class FloppyDisk:
    def __init__(self):
        self.data = None

    def __getitem__(self, bytenum):
        return self.data[bytenum]

    def __setitem__(self, bytenum, value):
        self.data[bytenum] = value

    def i32_at(self, bytenum):
        """returns signed 32 bit integer value"""
        return struct.unpack(">i", self.data[bytenum:bytenum + 4])[0]

    def u32_at(self, bytenum):
        """returns signed 32 bit integer value"""
        return struct.unpack(">I", self.data[bytenum:bytenum + 4])[0]

    def sector(self, sector_num):
        idx = sector_num * FLOPPY_BYTES_PER_SECTOR
        # slicing the bytearray creates an independent copy, but we want a
        # Sector be a view that writes to the underlying array, so we create
        # memoryview, and slice it to achive the dessired effect
        return Sector(memoryview(self.data)[idx:idx + FLOPPY_BYTES_PER_SECTOR])

    def write_image(file):
        file.write(self.data)

class DoubleDensityDisk(FloppyDisk):
    def __init__(self):
        self.data = bytearray(DDD_IMAGE_SIZE)

    def num_sectors(self):
        return DDD_SECTORS_TOTAL


class HighDensityDisk(FloppyDisk):
    def __init__(self):
        self.data = bytearray(HDD_IMAGE_SIZE)

    def num_sectors(self):
        return HDD_SECTORS_TOTAL

def read_adf_image(file):
    data = file.read()
    if len(data) == DDD_IMAGE_SIZE:
        result = DoubleDensityDisk()
    elif len(data) == HDD_IMAGE_SIZE:
        result = HighDensityDisk()
    else:
        raise Exception("Wrong image size !!! (expected %d but was %d)" % (DDD_IMAGE_SIZE, len(data)))
    result.data = data
    return result
