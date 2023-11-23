"""logical.py - Logical view on an Amiga disk"""

from . import physical
from . import util

BOOT_BLOCK_FLAG_FFS               = 1
BOOT_BLOCK_FLAG_INTL_ONLY         = 2
BOOT_BLOCK_FLAG_DIRCACHE_AND_INTL = 4

# Special blocks
BLOCK_ID_BOOT       = "DOS"
BLOCK_ID_RIGID_DISK = "RDSK"
BLOCK_ID_BAD_BLOCK  = "BADB"
BLOCK_ID_PARTITION  = "PART"
BLOCK_ID_FILESSYS   = "FSHD"
BLOCK_ID_LOADSEG    = "LSEG"

BLOCK_TYPE_HEADER   = 2
BLOCK_TYPE_DATA     = 8
BLOCK_TYPE_LIST     = 16
BLOCK_TYPE_DIRCACHE = 33

BLOCK_SEC_TYPE_ROOT     = 1
BLOCK_SEC_TYPE_USERDIR  = 2
BLOCK_SEC_TYPE_SOFTLINK = 3
BLOCK_SEC_TYPE_LINKDIR  = 4
BLOCK_SEC_TYPE_FILE     = -3
BLOCK_SEC_TYPE_LINKFILE = -4

class BootBlock:
    """The Boot block in an Amiga DOS volume.
    It stores information about the file system and a checksum of this block
    """
    def __init__(self, logical_volume):
        self.logical_volume = logical_volume

    def block_size(self):
        # TODO: this is currently hardcoded to double density disks
        return physical.FLOPPY_BYTES_PER_SECTOR * physical.FLOPPY_TRACKS_PER_CYLINDER

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
    or file."""
    def __init__(self, logical_volume, blocknum):
        self.logical_volume = logical_volume
        self.blocknum = blocknum

    def block_size(self):
        return self.sector().size_in_bytes()

    def sector(self):
        return self.physical_volume().sector(self.blocknum)

    def data(self):
        return self.sector().data

    def physical_volume(self):
        return self.logical_volume.physical_volume

    def primary_type(self):
        return self.sector().u32_at(0)

    def secondary_type(self):
        sector = self.sector()
        return sector.i32_at(sector.size_in_bytes() - 4)

    def is_directory(self):
        return self.secondary_type() == BLOCK_SEC_TYPE_USERDIR

    def name(self):
        sector = self.sector()
        soffset = sector.size_in_bytes() - 80
        slen = sector[soffset]
        result = ""
        for i in range(slen):
            result += chr(sector[soffset + i + 1])
        return result

    def _amigados_time_at(self, offset):
        sector = self.sector()
        days = sector.i32_at(sector.size_in_bytes() - offset)
        minutes = sector.i32_at(sector.size_in_bytes() - offset + 4)
        ticks = sector.i32_at(sector.size_in_bytes() - offset + 8)
        return util.amigados_time_to_datetime(days, minutes, ticks)

    def last_modification_time(self):
        return self._amigados_time_at(92)

    def header_key(self):
        return self.sector().u32_at(4)

    def hashtable_size(self):
        """This is hard coded, because header blocks don't contain the size.
        Adjust according to the disk type"""
        return 72

    def hashtable_entry_at(self, index):
        sector = self.sector()
        if index > self.hashtable_size():
            raise IndexError("Index out of bounds: %d, hash table size: %d" %
                             (index, self.hashtable_size()))
        return sector.u32_at(24 + (index * 4))

    def stored_checksum(self):
        return self.sector().u32_at(20)

    def computed_checksum(self):
        return util.headerblock_checksum(self.data(), self.block_size())

    def bitmap_flag(self):
        return self.sector().i32_at(self.block_size() - 200)

    # Directory only
    def find_header(self, filename):
        hash_index = util.compute_hash(filename, self.block_size())
        sector_num = self.hashtable_entry_at(hash_index)
        header = self.logical_volume.header_block_at(sector_num)
        if header.name().upper() != filename.upper():
            # TODO follow hash chain
            raise Exception("Hash collision, resolve by following next hash (TODO)")

        return header

    #################################
    # File header block only
    def file_comment(self):
        sector = self.sector()
        comm_len = sector[self.block_size() - 184]
        result = ""
        for i in range(comm_len):
            result += chr(sector[self.block_size() - 183 + i])
        return result

    def high_seq(self):
        """number of data block pointers"""
        return self.sector().u32_at(8)

    def file_size(self):
        return self.sector().u32_at(self.block_size() - 188)

    def data_blocks(self):
        """Returns all the data block numbers of this file
        TODO: handle extension blocks for large files"""
        result = []
        sector = self.sector()
        for i in range(self.high_seq()):
            datablock_num = sector.u32_at((self.block_size() - DATABLOCK_OFFSET) - (i * 4))
            result.append(datablock_num)
        return result


class RootBlock(HeaderBlock):
    """A logical view on the root block, a special header block, which is at a
    fixed position (880 for DD disks).
    These are the methods that only apply to the root block"""
    def __init__(self, logical_volume, blocknum):
        super().__init__(logical_volume, blocknum)

    def hashtable_size(self):
        return self.sector().u32_at(12)

    def last_disk_modification_time(self):
        return self._amigados_time_at(40)

    def last_filesys_modification_time(self):
        return self._amigados_time_at(28)


class DataBlock:
    """A logical view on header blocks. Those are the first block of a directory
    or file."""
    def __init__(self, logical_volume, blocknum):
        self.logical_volume = logical_volume
        self.blocknum = blocknum

    def sector(self):
        return self.physical_volume().sector(self.blocknum)

    def block_size(self):
        return self.sector().size_in_bytes()

    def data(self):
        return self.sector().data

    def physical_volume(self):
        return self.logical_volume.physical_volume

    def block_type(self):
        return self.sector().u32_at(0)

    def seq_num(self):
        return self.sector().u32_at(8)

    def data_size(self):
        return self.sector().u32_at(12)


DATABLOCK_OFFSET = 204

class LogicalVolume:

    def __init__(self, physical_volume):
        self.physical_volume = physical_volume

    def initialize(self, fs_type="FFS", is_international=False, use_dircache=False):
        self.boot_block().initialize(fs_type, is_international, use_dircache)

    def filesystem_type(self):
        return self.boot_block().filesystem_type()

    def boot_block(self):
        return BootBlock(self)

    def root_block(self):
        """returns the root block of this logical volume

        TODO: this works for disks, but might not for HDFs, because
           1. they can have any size
           2. we should look at the root block number inside the boot block
        """
        return RootBlock(self, int(self.physical_volume.num_sectors() / 2))

    def header_block_at(self, sector_num):
        return HeaderBlock(self, sector_num)

    def data_block_at(self, sector_num):
        return DataBlock(self, sector_num)

    def header_for_path(self, path):
        path = [p for p in path.split("/") if p != '']
        cur_header = self.root_block()
        for pathcomp in path:
            cur_header = cur_header.find_header(pathcomp)
        return cur_header

    def file_data(self, path):
        result = bytearray()
        file_header = self.header_for_path(path)
        data_blocks = file_header.data_blocks()
        remain_size = file_header.file_size()
        # Now concatenate the data from the data blocks. Be aware that OFS
        # and FFS data blocks have different formats
        if self.filesystem_type() == 'OFS':
            for i in data_blocks:
                data_block = self.data_block_at(i)
                result.extend(data_block.data()[24:24+data_block.data_size()])

        elif self.filesystem_type() == 'FFS':
            # data_blocks only contain data, no size
            for i in data_blocks:
                data_block = self.data_block_at(i)
                if remain_size >= data_block.block_size():
                    result.extend(data_block.data())
                    remain_size -= data_block.block_size()
                else:
                    result.extend(data_block.data()[0:remain_size])
                    remain_size = 0
        else:
            raise Exception("Unsupported file system type: %s" % self.filesystem_type())
        return result
