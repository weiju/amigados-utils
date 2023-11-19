#!/usr/bin/env python3

"""adftools_logical_test.py"""

import unittest
import xmlrunner
import sys
from amigadev.adftools import util


class ADFToolsUtilTest(unittest.TestCase):  # pylint: disable-msg=R0904
    """Test class for logical module"""

    def test_amigados_time_to_datetime(self):
        d = util.amigados_time_to_datetime(2, 15, 0)
        self.assertEqual(1978, d.year)
        self.assertEqual(1, d.month)
        self.assertEqual(3, d.day)
        self.assertEqual(0, d.hour)
        self.assertEqual(15, d.minute)
        self.assertEqual(0, d.second)


if __name__ == '__main__':
    SUITE = []
    SUITE.append(unittest.TestLoader().loadTestsFromTestCase(ADFToolsUtilTest))
    if len(sys.argv) > 1 and sys.argv[1] == 'xml':
      xmlrunner.XMLTestRunner(output='test-reports').run(unittest.TestSuite(SUITE))
    else:
      unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(SUITE))
