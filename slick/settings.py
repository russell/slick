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

import os
from os import path
from optparse import OptionParser
import ConfigParser

homedir = os.getenv('USERPROFILE') or os.getenv('HOME')
store_dir = path.join(homedir, ".globus-slcs")


def settings_options(parser):
    """adds extra options to the optparser"""
    parser.add_option("-d", "--storedir", dest="store_dir",
                      help="the directory to store the certificate/key and \
                      config file",
                      metavar="DIR",
                      default=path.join(homedir, ".globus-slcs"))
    parser.add_option("-i", "--idp",
                      help="unique ID of the IdP used to log in")
    parser.add_option("-s", "--slcs",
                      help="location of SLCS server (if not specified, use \
                      SLCS_SERVER system variable or settings from \
                      [storedir]/slcs-client.properties",
                      default="https://slcs1.arcs.org.au/SLCS/login")

class Settings:
    """
    parse out the variables
    """
    def __init__(self, options=None, args=None, config_file=None):
        self.optparser = OptionParser()
        settings_options(self.optparser)

        if not options:
            options, args = self.optparser.parse_args()

        if not path.exists(options.store_dir):
            os.mkdir(options.store_dir)


        self.config = ConfigParser.ConfigParser()
        if config_file:
            self.config_file = config_file
        else:
            self.config_file = path.join(options.store_dir,
                                         'slcs-client.properties')
        if path.exists(self.config_file):
            self.config.read(self.config_file)
        # add base section if it's missing
        if not self.config.has_section('slcs'):
            self.config.add_section('slcs')

        # Read SP urls
        try:
            self.slcs = self.config.get('slcs', 'url')
        except ConfigParser.NoSectionError:
            self.slcs = ''
        except ConfigParser.NoOptionError:
            self.slcs = ''

        if os.environ.get('SLCS_SERVER'):
            self.slcs = os.environ.get('SLCS_SERVER')
        if options.slcs != self.optparser.get_default_values().slcs:
            self.slcs = options.slcs
        if not self.slcs:
            self.slcs = options.slcs


        try:
            self.idp = self.config.get('slcs', 'idp')
        except ConfigParser.NoSectionError:
            self.idp = None
        except ConfigParser.NoOptionError:
            self.idp = None

        if options.idp:
            self.idp = options.idp
        if " ".join(args):
            self.idp = " ".join(args)


    def save(self):
        """
        save the contents of the settings instance to a file
        """
        config = ConfigParser.ConfigParser()
        config.add_section('slcs')
        if self.slcs and self.slcs != self.optparser.defaults['slcs']:
            config.set('slcs', 'url', self.slcs)
        if self.idp and self.idp != self.optparser.defaults['idp']:
            config.set('slcs', 'idp', self.idp)

        # Writing our configuration file to 'example.cfg'
        configfile = open(self.config_file, 'wb')
        config.write(configfile)
        configfile.close()


