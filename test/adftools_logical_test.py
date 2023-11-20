#!/usr/bin/env python3

"""adftools_logical_test.py"""

import unittest
import xmlrunner
import sys
from amigadev.adftools import physical
from amigadev.adftools import logical


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
            disk = physical.read_ddd_image(infile)
        volume = logical.LogicalVolume(disk)
        self.assertTrue(volume.boot_block().is_dos())
        self.assertEqual("OFS", volume.boot_block().filesystem_type())
        self.assertEqual(logical.BLOCK_TYPE_HEADER, volume.root_block().primary_type())
        self.assertEqual(logical.BLOCK_SEC_TYPE_ROOT, volume.root_block().secondary_type())
        self.assertEqual("Workbench1.3", volume.root_block().name())
        # verify checksum computation
        self.assertEqual(volume.boot_block().stored_checksum(),
                         volume.boot_block().computed_checksum())


if __name__ == '__main__':
    SUITE = []
    SUITE.append(unittest.TestLoader().loadTestsFromTestCase(ADFToolsLogicalTest))
    if len(sys.argv) > 1 and sys.argv[1] == 'xml':
      xmlrunner.XMLTestRunner(output='test-reports').run(unittest.TestSuite(SUITE))
    else:
      unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(SUITE))
