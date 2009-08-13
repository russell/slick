##############################################################################
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
##############################################################################

from optparse import OptionParser
from urllib2 import urlparse
import os, sys
from os import path
import logging
import struct, fcntl, termios

from shibboleth import open_shibprotected_url, list_shibboleth_idps
from cert import slcs
from passmgr import CredentialManager
from settings import Settings, settings_options

spUri = "https://slcs1.arcs.org.au/SLCS/login"


def terminal_dimensions():
    fd = os.open(os.ctermid(), os.O_RDONLY)
    if not os.isatty(fd):
        return (0,0)
    return struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))


def print_list_wide(items):
    lmax = max([len(x) for x in items]) + 1
    width = terminal_dimensions()[1]
    if width:
        col = width/lmax
        i = 1
        for item in items:
            if not i%col:
                print item
            else:
                print item.ljust(lmax),
            i = i + 1
    else:
        for item in items:
            print item

usage = "usage: %prog [options] [idp]"
parser = OptionParser(usage)

settings_options(parser)
parser.add_option("-f", "--find", dest="idp_search",
                  help="find IdP(s) whose name or unique ID contain a \
                  specified string",
                  metavar="SEARCHSTRING")
parser.add_option("-k", "--key", action='store_true',
                  help="prompt for key-passphrase (use Shibboleth password \
                  by default)")
parser.add_option("-l", "--list", action='store_true',
                  help="list all available IdP(s)")
parser.add_option("-w", "--write",
                  action="store_true",
                  help="write the arguments specified on the command line to \
                  a config file")
parser.add_option("-v", "--verbose",
                  action="count",
                  help="print status messages to stdout")

# Set up a specific logger with our desired output level
log = logging.getLogger('slick-client')
log_handle = logging.StreamHandler()
DEBUG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


def main():
    try:
        (options, args) = parser.parse_args()

        if not path.exists(options.store_dir):
            os.mkdir(options.store_dir)

        formatter = None
        log_level = logging.WARNING # default
        if options.verbose == 1:
            formatter = "%(message)s"
            log_level = logging.INFO
        elif options.verbose >= 2:
            formatter = DEBUG_FORMAT
            log_level = logging.DEBUG

        # Set up basic configuration, out to stderr with a reasonable default format.
        if formatter:
            logging.basicConfig(level=log_level, format=formatter)
        else:
            logging.basicConfig(level=log_level)

        settings = Settings(options)
        spUri = settings.slcs
        config_idp = settings.idp

        if options.idp_search:
            log.debug("List IDPs")
            idp_search = options.idp_search.lower()
            slcs_login_url = urlparse.urljoin(spUri, 'login')
            idps = list_shibboleth_idps(slcs_login_url)
            idps = dict(filter(lambda item: idp_search in item[0].lower(),
                               idps.items()))
            idp_keys = idps.keys()
            idp_keys.sort()
            print_list_wide(idp_keys)
            return

        # List idps
        if options.list:
            log.debug("List IDPs")
            slcs_login_url = urlparse.urljoin(spUri, 'login')
            idps = list_shibboleth_idps(slcs_login_url)
            idp_keys = idps.keys()
            idp_keys.sort()
            print_list_wide(idp_keys)
            return

        # Cert cert using specific IdP
        if args or config_idp:
            idp = " ".join(args) or config_idp
            print "Using IdP: %s" % idp
            slcs_login_url = spUri
            c = CredentialManager()
            slcsresp = open_shibprotected_url(idp, slcs_login_url, c)

            log.info('Writing to files')
            key, pubKey, cert = slcs(slcsresp)
            key_path = path.join(options.store_dir, 'userkey.pem')
            if options.key:
                def callback(verify=False):
                    from getpass import getpass
                    while 1:
                        p1=getpass('Enter passphrase:')
                        p2=getpass('Verify passphrase:')
                        if not p1:
                            print "Passphrase cannot be blank"
                            continue
                        if p1==p2:
                            return p1
            else:
                def callback(verify=False):
                    return c.get_password()

            key._key.save_pem(key_path, callback=callback)
            os.chmod(key_path, 0600)
            cert_path = path.join(options.store_dir, 'usercert.pem')
            cert_file = open(path.join(options.store_dir, 'usercert.pem'), 'w')
            cert_file.write(cert.as_pem())
            cert_file.close()
            os.chmod(cert_path, 0644)

            if options.write:
                log.info('Writing a config')
                settings.save()

            print "\nexport X509_USER_CERT=%s \nexport X509_USER_KEY=%s" % (cert_path, key_path)
            return
    except KeyboardInterrupt:
        print "\Cancelled"
        return

    if len(sys.argv) == 1:
        parser.print_help()

if __name__ == '__main__':
    main()

