#############################################################################
#
# Copyright (c) 2009 Victorian Partnership for Advanced Computing Ltd and
# Contributors.
# All Rights Reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

__docformat__ = 'restructuredtext'

import os, sys

import unittest
from slick.settings import Settings


class testSettings(unittest.TestCase):
    """
    test cases for the settings class
    """
    def setUp(self):
        self.current_dir = os.path.dirname(__file__)
        cfg = """[slcs]
url = http://localhost
idp = TestIDP
"""
        cfg_file = open(os.path.join(self.current_dir,
                                     'test_settings.cfg'), 'w')
        cfg_file.write(cfg)
        cfg_file.close()

        sys.argv = []

    def testLoadFromFile(self):
        settings = Settings(config_file=os.path.join(self.current_dir,
                                                     'test_settings.cfg'))
        self.failUnless(settings.idp == "TestIDP")
        self.failUnless(settings.slcs == "http://localhost",
                        "instead has value %s" % settings.slcs)

    def testCommandLine(self):
        sys.argv = ['./bin/slick-init', '-i', 'TestIDP-cl', '-s',
                    'http://localhost-cl']
        settings = Settings(config_file=os.path.join(self.current_dir,
                                                     'test_settings.cfg'))
        self.failUnless(settings.idp == "TestIDP-cl")
        self.failUnless(settings.slcs == "http://localhost-cl",
                        "instead has value %s" % settings.slcs)

        sys.argv = ['./bin/slick-init', 'University', 'of', 'Testing']
        settings = Settings(config_file=os.path.join(self.current_dir,
                                                     'test_settings.cfg'))

        self.failUnless(settings.idp == "University of Testing",
                        'instead has value %s' % settings.idp)

    def tearDown(self):
        os.remove(os.path.join(self.current_dir, 'test_settings.cfg'))

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(testSettings))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
