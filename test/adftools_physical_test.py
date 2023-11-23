#!/usr/bin/env python3

"""adftools_physical_test.py"""

import unittest
import xmlrunner
import sys
from amigados.adftools import physical


class ADFToolsPhysicalTest(unittest.TestCase):  # pylint: disable-msg=R0904
    """Test class for physical module"""

    def test_disk(self):
        disk = physical.DoubleDensityDisk()
        disk[0] = 23
        self.assertEqual(23, disk[0])

    def test_sector(self):
        disk = physical.DoubleDensityDisk()
        sector0 = disk.sector(0)
        disk[0] = 23
        self.assertEqual(physical.FLOPPY_BYTES_PER_SECTOR, sector0.size_in_bytes())
        self.assertEqual(23, disk[0])
        self.assertEqual(23, sector0[0])

        sector0[1] = 25
        self.assertEqual(25, disk[1])
        self.assertEqual(25, sector0[1])

    def test_sector_u16_at(self):
        disk = physical.DoubleDensityDisk()
        disk[2] = 0x47
        disk[3] = 0x11

        sector0 = disk.sector(0)
        self.assertEqual(0x4711, sector0.u16_at(2))

    def test_sector_u32_at(self):
        disk = physical.DoubleDensityDisk()
        disk[0] = 0x08
        disk[1] = 0x15
        disk[2] = 0x47
        disk[3] = 0x11

        sector0 = disk.sector(0)
        self.assertEqual(0x08154711, sector0.u32_at(0))

    def test_disk_i32_at(self):
        disk = physical.DoubleDensityDisk()
        disk[0] = 0x08
        disk[1] = 0x15
        disk[2] = 0x47
        disk[3] = 0x11

        self.assertEqual(0x08154711, disk.i32_at(0))


if __name__ == '__main__':
    SUITE = []
    SUITE.append(unittest.TestLoader().loadTestsFromTestCase(ADFToolsPhysicalTest))
    if len(sys.argv) > 1 and sys.argv[1] == 'xml':
      xmlrunner.XMLTestRunner(output='test-reports').run(unittest.TestSuite(SUITE))
    else:
      unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(SUITE))
