"""logical.py - Logical view on an Amiga disk"""

from datetime import datetime
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

ROOT_BLOCK_OFFSET_HASHTABLE_SIZE  = 12

ROOT_BLOCK_SIZE_OFFSET_BITMAP_FLAG           = -200
ROOT_BLOCK_SIZE_OFFSET_BITMAP_PAGES          = -196
ROOT_BLOCK_SIZE_OFFSET_LAST_DISK_ALTERATION  = -40
ROOT_BLOCK_SIZE_OFFSET_FILESYS_CREATION_TIME = -28

ROOT_BLOCK_VALID_BITMAP = -1

HEADER_BLOCK_OFFSET_HEADER_KEY = 4
HEADER_BLOCK_OFFSET_CHECKSUM   = 20
HEADER_BLOCK_OFFSET_HASHTABLE  = 24

HEADER_BLOCK_SIZE_OFFSET_LAST_MODIFIED = -92
HEADER_BLOCK_SIZE_OFFSET_COMMENT_LEN   = -184
HEADER_BLOCK_SIZE_OFFSET_COMMENT       = -183
HEADER_BLOCK_SIZE_OFFSET_NAME_LEN      = -80
HEADER_BLOCK_SIZE_OFFSET_NAME          = -79
HEADER_BLOCK_SIZE_OFFSET_NEXT_HASH     = -16
HEADER_BLOCK_SIZE_OFFSET_PARENT        = -12
HEADER_BLOCK_SIZE_OFFSET_EXT           = -8
HEADER_BLOCK_SIZE_OFFSET_SECTYPE       = -4

BITMAP_BLOCK_OFFSET_CHECKSUM = 0

class DiskBlock:
    def __init__(self, logical_volume):
        self.logical_volume = logical_volume

    def physical_volume(self):
        return self.logical_volume.physical_volume


class BootBlock(DiskBlock):
    """The Boot block in an Amiga DOS volume.
    It stores information about the file system and a checksum of this block
    """
    def __init__(self, logical_volume):
        super().__init__(logical_volume)

    def block_size(self):
        # TODO: this is currently hardcoded to floppy disks
        return physical.FLOPPY_BYTES_PER_SECTOR * physical.FLOPPY_TRACKS_PER_CYLINDER

    def data(self):
        return self.logical_volume.physical_volume.data[0:self.block_size()]

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


class HeaderBlock(DiskBlock):
    """A logical view on header blocks. Those are the first block of a directory
    or file."""
    def __init__(self, logical_volume, blocknum):
        super().__init__(logical_volume)
        self.blocknum = blocknum

    def block_size(self):
        return self.sector().size_in_bytes()

    def sector(self):
        return self.physical_volume().sector(self.blocknum)

    def data(self):
        return self.sector().data

    def primary_type(self):
        return self.sector().u32_at(0)

    def secondary_type(self):
        sector = self.sector()
        return sector.i32_at(sector.size_in_bytes() - 4)

    def is_directory(self):
        return self.secondary_type() == BLOCK_SEC_TYPE_USERDIR

    def name(self):
        sector = self.sector()
        soffset = sector.size_in_bytes() + HEADER_BLOCK_SIZE_OFFSET_NAME_LEN
        slen = sector[soffset]
        result = ""
        for i in range(slen):
            result += chr(sector[soffset + i + 1])
        return result

    def _amigados_time_at(self, offset):
        sector = self.sector()
        days = sector.u32_at(sector.size_in_bytes() + offset)
        minutes = sector.u32_at(sector.size_in_bytes() + offset + 4)
        ticks = sector.u32_at(sector.size_in_bytes() + offset + 8)
        return util.amigados_time_to_datetime(days, minutes, ticks)

    def _set_amigados_time_at(self, offset,
                              days_since_1978, minutes_past_midnight,
                              ticks):
        sector = self.sector()
        sector.set_u32_at(sector.size_in_bytes() + offset, days_since_1978)
        sector.set_u32_at(sector.size_in_bytes() + offset + 4, minutes_past_midnight)
        sector.set_u32_at(sector.size_in_bytes() + offset + 8, ticks)

    def last_modification_time(self):
        return self._amigados_time_at(HEADER_BLOCK_SIZE_OFFSET_LAST_MODIFIED)

    def update_last_modification_time(self):
        now = datetime.now()
        days, minutes, ticks = util.datetime_to_amigados_time(now)
        self._set_amigados_time_at(HEADER_BLOCK_SIZE_OFFSET_LAST_MODIFIED,
                                   days, minutes, ticks)

    def header_key(self):
        return self.sector().u32_at(HEADER_BLOCK_OFFSET_HEADER_KEY)

    def stored_checksum(self):
        return self.sector().u32_at(HEADER_BLOCK_OFFSET_CHECKSUM)

    def computed_checksum(self):
        return util.headerblock_checksum(self.data(), self.block_size())

    def update_checksum(self):
        self.sector().set_u32_at(HEADER_BLOCK_OFFSET_CHECKSUM, self.computed_checksum())

    def file_comment(self):
        sector = self.sector()
        comm_len = sector[self.block_size() + HEADER_BLOCK_SIZE_OFFSET_COMMENT_LEN]
        result = ""
        for i in range(comm_len):
            result += chr(sector[self.block_size() + HEADER_BLOCK_SIZE_OFFSET_COMMENT + i])
        return result

    def parent(self):
        return self.sector().u32_at(self.block_size() + HEADER_BLOCK_SIZE_OFFSET_PARENT)

    def set_parent(self, blocknum):
        return self.sector().set_u32_at(self.block_size() + HEADER_BLOCK_SIZE_OFFSET_PARENT,
                                        blocknum)

    def next_hash(self):
        return self.sector().u32_at(self.block_size() + HEADER_BLOCK_SIZE_OFFSET_NEXT_HASH)

    def set_next_hash(self, blocknum):
        return self.sector().set_u32_at(self.block_size() + HEADER_BLOCK_SIZE_OFFSET_NEXT_HASH,
                                        blocknum)

    #################################
    # Directory header block only

    def find_header(self, filename):
        hash_index = util.compute_hash(filename, self.block_size())
        sector_num = self.hashtable_entry_at(hash_index)
        header = self.logical_volume.header_block_at(sector_num)
        while (header.name().upper() != filename.upper() and
               header.next_hash() != 0):
            # follow hash chain
            header = self.logical_volume.header_block_at(header.next_hash())
        if header.name().upper() != filename.upper():
            raise Exception("can't find file/dir '%s'" % filename)

        return header

    def hashtable_size(self):
        """This is hard coded, because header blocks don't contain the size.
        Adjust according to the disk type"""
        return 72

    def hashtable_entry_at(self, index):
        sector = self.sector()
        if index > self.hashtable_size():
            raise IndexError("Index out of bounds: %d, hash table size: %d" %
                             (index, self.hashtable_size()))
        return sector.u32_at(HEADER_BLOCK_OFFSET_HASHTABLE + (index * 4))

    def append_hashtable_entry_at(self, index, blocknum):
        """add block number to the bucket at the specified hash table index"""
        sector = self.sector()
        if index > self.hashtable_size():
            raise IndexError("Index out of bounds: %d, hash table size: %d" %
                             (index, self.hashtable_size()))
        cur_blocknum = sector.u32_at(HEADER_BLOCK_OFFSET_HASHTABLE + (index * 4))
        if cur_blocknum == 0:  # no collisions
            sector.set_u32_at(HEADER_BLOCK_OFFSET_HASHTABLE + (index * 4),
                              blocknum)
        else:
            # collision -> append blocknum to end of chain
            curblock = self.logical_volume.header_block_at(cur_blocknum)
            while curblock.next_hash() != 0:
                curblock = self.logical_volume.header_block_at(curblock.next_hash())
            curblock.set_next_hash(blocknum)

    def _set_name(self, name):
        """Sets the name field in the block. Never use this directly,
        since it can change the hash value of this block"""
        namelen = len(name)
        sector = self.sector()
        sector[self.block_size() + HEADER_BLOCK_SIZE_OFFSET_NAME_LEN] = namelen
        for i in range(namelen):
            sector[self.block_size() + HEADER_BLOCK_SIZE_OFFSET_NAME + i] = ord(name[i])

    def init_directory(self, name, parent_block):
        """Initialize this block as a new directory block"""
        sector = self.sector()
        sector.clear_data()
        sector.set_u32_at(0, BLOCK_TYPE_HEADER)
        sector.set_u32_at(HEADER_BLOCK_OFFSET_HEADER_KEY, self.blocknum)
        sector.set_u32_at(self.block_size() + HEADER_BLOCK_SIZE_OFFSET_SECTYPE,
                          BLOCK_SEC_TYPE_USERDIR)
        self._set_name(name)
        self.set_parent(parent_block)
        self.update_last_modification_time()
        self.update_checksum()

    #################################
    # File header block only
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
        return self.sector().u32_at(ROOT_BLOCK_OFFSET_HASHTABLE_SIZE)

    def last_disk_modification_time(self):
        return self._amigados_time_at(ROOT_BLOCK_SIZE_OFFSET_LAST_DISK_ALTERATION)

    def update_last_disk_modification_time(self):
        now = datetime.now()
        days, minutes, ticks = util.datetime_to_amigados_time(now)
        self._set_amigados_time_at(ROOT_BLOCK_SIZE_OFFSET_LAST_DISK_ALTERATION,
                                   days, minutes, ticks)

    def filesys_creation_time(self):
        return self._amigados_time_at(ROOT_BLOCK_SIZE_OFFSET_FILESYS_CREATION_TIME)

    def bitmap_flag(self):
        return self.sector().i32_at(self.block_size() + ROOT_BLOCK_SIZE_OFFSET_BITMAP_FLAG)

    def block_allocation(self):
        sector = self.sector()
        bm_pages = []
        if self.bitmap_flag() == ROOT_BLOCK_VALID_BITMAP:
            # we only need 1 bitmap block on a floppy disk
            bitmap_block = BitmapBlock(self.logical_volume,
                                       sector.u32_at(self.block_size() + ROOT_BLOCK_SIZE_OFFSET_BITMAP_PAGES))
            bm_sector = bitmap_block.sector()
            block_idx = 2
            free_blocks = []
            used_blocks = []
            for bytenum in range(4, bitmap_block.block_size(), 4):
                l = bm_sector.u32_at(bytenum)

                # don't try to check more than we have !!!
                if block_idx > self.physical_volume().num_sectors():
                    break

                mask = 0x80000000
                for i in range(32):
                    if (mask & l) == mask:
                        free_blocks.append(block_idx)
                    else:
                        used_blocks.append(block_idx)
                    mask >>= 1
                    block_idx += 1
                    if block_idx > self.physical_volume().num_sectors():
                        break

        return free_blocks, used_blocks

    def allocate_block(self, blocknum):
        free_blocks, used_blocks = self.block_allocation()
        if not blocknum in free_blocks:
            raise Exception("ERROR: can't allocate block %d - already used !!!" % blocknum)
        # we only need 1 bitmap block on a floppy disk
        bitmap_block = BitmapBlock(self.logical_volume,
                                   self.sector().u32_at(self.block_size() + ROOT_BLOCK_SIZE_OFFSET_BITMAP_PAGES))
        bitmap_block.mark_block_used(blocknum)


class BitmapBlock(DiskBlock):
    def __init__(self, logical_volume, blocknum):
        super().__init__(logical_volume)
        self.blocknum = blocknum

    def block_size(self):
        return self.sector().size_in_bytes()

    def sector(self):
        return self.physical_volume().sector(self.blocknum)

    def data(self):
        return self.sector().data

    def stored_checksum(self):
        return self.sector().u32_at(BITMAP_BLOCK_OFFSET_CHECKSUM)

    def computed_checksum(self):
        return util.headerblock_checksum(self.data(), self.block_size(),
                                         exclude_offset=BITMAP_BLOCK_OFFSET_CHECKSUM)

    def mark_block_used(self, blocknum):
        # 1. determine the long word in the bitmap that contains the bit
        # 2. set the bit mask and do bitwise "and" with that long word and store it back
        # 3. update checksum
        wordnum = int((blocknum - 2) / 32)
        bytenum = (wordnum + 1) * 4
        bitnum = (blocknum - 2) % 32
        # clear the bit by shifting + inverting
        mask = 0x80000000 >> bitnum
        mask ^= 0xffffffff

        sector = self.sector()
        orig = sector.u32_at(bytenum)
        sector.set_u32_at(bytenum, mask & orig)

        # update checksum
        sector.set_u32_at(BITMAP_BLOCK_OFFSET_CHECKSUM, self.computed_checksum())


class DataBlock(HeaderBlock):
    """A logical view on header blocks. Those are the first block of a directory
    or file."""
    def __init__(self, logical_volume, blocknum):
        super().__init__(logical_volume, blocknum)

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
