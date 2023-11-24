#!/usr/bin/env python3

"""adftools_logical_test.py"""

import unittest
import xmlrunner
import sys
from amigados.adftools import physical
from amigados.adftools import logical


class ADFToolsLogicalTest(unittest.TestCase):  # pylint: disable-msg=R0904
    """Test class for logical module"""

    def test_uninitialized_logical(self):
        """uninitialized logical volume"""
        disk = physical.DoubleDensityDisk()
        volume = logical.LogicalVolume(disk)
        self.assertFalse(volume.boot_block().is_dos())


    def test_initialized_logical(self):
        """initialized logical volume"""
        disk = physical.DoubleDensityDisk()
        volume = logical.LogicalVolume(disk)
        volume.initialize(fs_type="FFS")
        self.assertTrue(volume.boot_block().is_dos())
        self.assertEqual("FFS", volume.boot_block().filesystem_type())

    def test_read_wbdisk(self):
        """read WB disk"""
        with open("testdata/wbench1.3.adf", "rb") as infile:
            disk = physical.read_adf_image(infile)
        volume = logical.LogicalVolume(disk)

        # Boot block
        self.assertTrue(volume.boot_block().is_dos())
        self.assertEqual("OFS", volume.boot_block().filesystem_type())
        # verify checksum computation
        self.assertEqual(volume.boot_block().stored_checksum(),
                         volume.boot_block().computed_checksum())

        # Root block
        self.assertEqual(logical.BLOCK_TYPE_HEADER, volume.root_block().primary_type())
        self.assertEqual(logical.BLOCK_SEC_TYPE_ROOT, volume.root_block().secondary_type())
        self.assertEqual(0, volume.root_block().header_key())
        self.assertEqual("Workbench1.3", volume.root_block().name())
        modified = volume.root_block().last_modification_time()
        #1989-08-17 18:21:31.480000
        self.assertEqual(1989, modified.year)
        self.assertEqual(8, modified.month)
        self.assertEqual(17, modified.day)
        self.assertEqual(18, modified.hour)
        self.assertEqual(21, modified.minute)
        self.assertEqual(31, modified.second)
        self.assertEqual(0x48, volume.root_block().hashtable_size())
        self.assertEqual(volume.root_block().stored_checksum(),
                         volume.root_block().computed_checksum())
        self.assertEqual(-1, volume.root_block().bitmap_flag())

    def test_allocate_block(self):
        """allocate 1 block on the disk"""
        with open("testdata/wbench1.3.adf", "rb") as infile:
            disk = physical.read_adf_image(infile)
        volume = logical.LogicalVolume(disk)
        root_block = volume.root_block()
        sector = root_block.sector()
        bitmap_block = logical.BitmapBlock(volume, sector.u32_at(root_block.block_size() - 196))

        orig_checksum = bitmap_block.stored_checksum()
        self.assertEqual(orig_checksum, bitmap_block.computed_checksum())
        free_blocks, used_blocks = root_block.block_allocation()
        free_block0 = free_blocks[0]
        root_block.allocate_block(free_block0)
        free_blocks, used_blocks = root_block.block_allocation()
        self.assertFalse(free_block0 in free_blocks)
        new_checksum = bitmap_block.computed_checksum()
        self.assertEqual(bitmap_block.stored_checksum(), new_checksum)


if __name__ == '__main__':
    SUITE = []
    SUITE.append(unittest.TestLoader().loadTestsFromTestCase(ADFToolsLogicalTest))
    if len(sys.argv) > 1 and sys.argv[1] == 'xml':
      xmlrunner.XMLTestRunner(output='test-reports').run(unittest.TestSuite(SUITE))
    else:
      unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(SUITE))
