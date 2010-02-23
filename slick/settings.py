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
    parser.add_option("-c", "--proxy", action='store_true',
                      default=False,
                      dest='slick_proxy',
                      help="create a local 12 hour proxy.")
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

    mp = OptionGroup(parser, "MyProxy Options",)
    mp.add_option("-a", "--myproxy-autostore",
                  dest='slick_myproxy',
                  default=False,
                  action="store_true",
                  help="upload the proxy to myproxy each time.")
    mp.add_option("-u", "--myproxy-user",
                  dest='myproxy_user',
                  help="the username to connect to the myproxy server as.")
    mp.add_option("-m", "--myproxy-host",
                  dest='myproxy_host',
                  default='myproxy.arcs.org.au',
                  help="the hostname of the myproxy server")
    mp.add_option("-p", "--myproxy-port",
                  dest='myproxy_port',
                  default='7512',
                  help="the port of the myproxy server")
    mp.add_option("-l", "--myproxy-lifetime",
                  dest='myproxy_lifetime',
                  help="the lifetime of the certificate to put in myproxy")
    parser.add_option_group(mp)


class Settings:
    """
    parse out the variables
    """
    env = {
        'slcs_url': 'SLCS_SERVER',
        'slcs_idp': 'SLCS_IDP',
        'myproxy_user': 'MYPROXY_USER',
        'myproxy_host': 'MYPROXY_HOST',
        'myproxy_port': 'MYPROXY_PORT',
        'myproxy_lifetime': 'MYPROXY_LIFETIME',
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

        self.slick_proxy = self.get('slick', 'proxy')
        self.slick_myproxy = self.get('slick', 'myproxy')

        self.slcs_url = self.get('slcs', 'url')
        self.slcs_idp = self.get('slcs', 'idp')

        self.myproxy_user = self.get('myproxy', 'user')
        self.myproxy_host = self.get('myproxy', 'host')
        self.myproxy_port = self.get('myproxy', 'port')
        self.myproxy_lifetime = self.get('myproxy', 'lifetime')


    def get(self, *args):
        """
        get a value from the configuration
        """

        opt = '_'.join(args)
        default = self.optparser.defaults[opt]

        if getattr(self.options, opt) != default:
            sect, option = args
            # add base section if it's missing
            if not self.config.has_section(sect):
                self.config.add_section(sect)

            self.config.set(sect, option, getattr(self.options, opt))
            return getattr(self.options, opt)

        if opt == 'slcs_idp':
            if " ".join(self.optargs):
                sect, option = args

                # add base section if it's missing
                if not self.config.has_section(sect):
                    self.config.add_section(sect)

                idp = " ".join(self.optargs)
                self.config.set(sect, option, idp)
                return idp

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
        config = self.config

        # Writing our configuration file to 'example.cfg'
        if not configfile:
            configfile = open(self.config_file, 'wb')
            config.write(configfile)
            configfile.close()
        else:
            config.write(configfile)


