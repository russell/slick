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
from optparse import OptionParser, OptionGroup
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
    slcs = OptionGroup(parser, "SLCS Options",)
    slcs.add_option("-i", "--idp",
                    dest='slcs_idp',
                    help="unique ID of the IdP used to log in")
    slcs.add_option("-s", "--slcs",
                    help="location of SLCS server (if not specified, use \
                    SLCS_SERVER system variable or settings from \
                    [storedir]/slcs-client.properties",
                    dest='slcs_url',
                    default="https://slcs1.arcs.org.au/SLCS/login")
    parser.add_option_group(slcs)


class Settings:
    """
    parse out the variables
    """
    env = {
        'slcs_url': 'SLCS_SERVER',
        'slcs_idp': 'SLCS_IDP',
    }

    def __init__(self, options=None, args=None, config_file=None):
        self.optparser = OptionParser()
        settings_options(self.optparser)

        if not options:
            options, args = self.optparser.parse_args()

        self.options = options
        self.optargs = args

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
        self.slcs_url = self.get('slcs', 'url')

        # read idp
        self.slcs_idp = self.get('slcs', 'idp')

    def get(self, *args):
        """
        get a value from the configuration
        """
        opt = '_'.join(args)
        default = self.optparser.defaults[opt]

        if getattr(self.options, opt) != default:
            return getattr(self.options, opt)

        if opt == 'slcs_idp':
            if " ".join(self.optargs):
                return " ".join(self.optargs)

        # parse env variables
        if self.env.has_key(opt):
            if os.environ.get(self.env[opt]):
                return os.environ.get(self.env[opt])

        # parse config
        try:
            return self.config.get(*args)
        except ConfigParser.NoSectionError:
            return default
        except ConfigParser.NoOptionError:
            return default


    def save(self, configfile=None):
        """
        save the contents of the settings instance to a file
        """
        config = ConfigParser.ConfigParser()
        config.add_section('slcs')

        def set_config(*args):
            opt = '_'.join(args)
            default = self.optparser.defaults[opt]
            if getattr(self, opt) and getattr(self, opt) != default:
                sect, option = args
                config.set(sect, option, getattr(self, opt))

        set_config('slcs', 'url')
        set_config('slcs', 'idp')

        # Writing our configuration file to 'example.cfg'
        if not configfile:
            configfile = open(self.config_file, 'wb')
            config.write(configfile)
            configfile.close()
        else:
            config.write(configfile)


