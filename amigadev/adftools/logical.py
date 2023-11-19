"""logical.py - Logical view on an Amiga disk"""

from . import physical

BOOT_BLOCK_FLAG_FFS               = 1
BOOT_BLOCK_FLAG_INTL_ONLY         = 2
BOOT_BLOCK_FLAG_DIRCACHE_AND_INTL = 4

OFFSET_ROOTBLOCK_NUMBER = 8
DDD_ROOT_SECTOR_NUMBER  = 880
DDD_ROOT_BLOCK_NUMBER   = 880
DDD_BITMAP_BLOCK_NUMBER = 881

# for root block
MAX_BITMAP_BLOCKS = 25


class BootBlock:
    """The Boot block in an Amiga DOS volume.
    It stores information about the file system and a checksum of this block
    """
    def __init__(self, logical_volume):
        self.logical_volume = logical_volume

    def physical_volume(self):
        return self.logical_volume.physical_volume

    def initialize(self, fs_type, is_international=False, use_dircache=False):
        self.physical_volume()[0] = ord('D')
        self.physical_volume()[1] = ord('O')
        self.physical_volume()[2] = ord('S')
        fs_flags = 0 if fs_type == 'OFS' else 1
        if is_international and use_dircache:
            fs_flags += 4
        elif is_international:
            fs_flags += 2
        self.physical_volume()[3] = fs_flags

    def is_dos(self):
        return (self.physical_volume()[0] == ord('D')
                and self.physical_volume()[1] == ord('O') and
                self.physical_volume()[2] == ord('S'))

    def flags(self):
        return self.physical_volume()[3] & 0x07

    def filesystem_type(self):
        return "FFS" if (self.flags() & 1) == 1 else "OFS"


class RootBlock:
    def __init__(self, logical_volume, blocknum):
        self.logical_volume = logical_volume
        self.blocknum = blocknum



class LogicalVolume:

    def __init__(self, physical_volume):
        self.physical_volume = physical_volume
        self.boot_block = BootBlock(self)


    def initialize(self, fs_type="FFS", is_international=False, use_dircache=False):
        self.boot_block.initialize(fs_type, is_international, use_dircache)
