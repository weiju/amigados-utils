"""logical.py - Logical view on an Amiga disk"""

from . import physical
from . import util

BOOT_BLOCK_FLAG_FFS               = 1
BOOT_BLOCK_FLAG_INTL_ONLY         = 2
BOOT_BLOCK_FLAG_DIRCACHE_AND_INTL = 4

OFFSET_ROOTBLOCK_NUMBER = 8
DDD_ROOT_BLOCK_NUMBER   = 880
DDD_BITMAP_BLOCK_NUMBER = 881

# for root block
MAX_BITMAP_BLOCKS = 25

BLOCK_TYPE_HEADER   = 2
BLOCK_SEC_TYPE_ROOT = 1

class BootBlock:
    """The Boot block in an Amiga DOS volume.
    It stores information about the file system and a checksum of this block
    """
    def __init__(self, logical_volume):
        self.logical_volume = logical_volume

    def block_size(self):
        # TODO: this is currently hardcoded to double density disks
        return physical.DDD_BYTES_PER_SECTOR * physical.DDD_TRACKS_PER_CYLINDER

    def data(self):
        return self.logical_volume.physical_volume.data[0:self.block_size()]

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

    def computed_checksum(self):
        return util.bootblock_checksum(self.data(), self.block_size())

    def stored_checksum(self):
        return self.logical_volume.physical_volume.u32_at(4)


class HeaderBlock:
    """A logical view on header blocks. Those are the first block of a directory
    or file. A special type of block is the root block, which is at a fixed position (880)"""
    def __init__(self, logical_volume, blocknum):
        self.logical_volume = logical_volume
        self.blocknum = blocknum

    def physical_volume(self):
        return self.logical_volume.physical_volume

    def primary_type(self):
        return self.physical_volume().sector(self.blocknum).i32_at(0)

    def secondary_type(self):
        sector = self.physical_volume().sector(self.blocknum)
        return sector.i32_at(sector.size_in_bytes() - 4)

    def name(self):
        sector = self.physical_volume().sector(self.blocknum)
        soffset = sector.size_in_bytes() - 80
        slen = sector[soffset]
        result = ""
        for i in range(slen):
            result += chr(sector[soffset + i + 1])
        return result


class LogicalVolume:

    def __init__(self, physical_volume):
        self.physical_volume = physical_volume

    def boot_block(self):
        return BootBlock(self)

    def root_block(self):
        return HeaderBlock(self, DDD_ROOT_BLOCK_NUMBER)

    def initialize(self, fs_type="FFS", is_international=False, use_dircache=False):
        self.boot_block().initialize(fs_type, is_international, use_dircache)
