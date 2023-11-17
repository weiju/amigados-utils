#!/usr/bin/env python3

"""adftools_physical_test.py"""

import unittest
import xmlrunner
import sys
from amigadev.adftools import physical


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
        self.assertEqual(23, disk[0])
        self.assertEqual(23, sector0[0])

        sector0[1] = 25
        self.assertEqual(25, disk[1])
        self.assertEqual(25, sector0[1])


if __name__ == '__main__':
    SUITE = []
    SUITE.append(unittest.TestLoader().loadTestsFromTestCase(ADFToolsPhysicalTest))
    if len(sys.argv) > 1 and sys.argv[1] == 'xml':
      xmlrunner.XMLTestRunner(output='test-reports').run(unittest.TestSuite(SUITE))
    else:
      unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(SUITE))
