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
import pprint
import logging
import struct, fcntl, termios

from shibboleth import run, list_idps
from cert import slcs
from passmgr import getPassphrase, getPassphrase_noinput


homedir = os.getenv('USERPROFILE') or os.getenv('HOME')

spUri = "https://slcs1.arcs.org.au/SLCS/login"


def terminal_dimensions():
    fd = os.open(os.ctermid(), os.O_RDONLY)
    if not os.isatty(fd):
        return (0,0)
    return struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))


def print_list_wide(items):
    lmax = len(max(items, key=len))
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

parser.add_option("-d", "--storedir", dest="store_dir",
                  help="find IdP(s) whose name or unique ID contain a \
                  specified string",
                  metavar="DIR",
                  default=path.join(homedir, ".globus-slcs"))
parser.add_option("-f", "--find", dest="idp_search",
                  help="find IdP(s) whose name or unique ID contain a \
                  specified string",
                  metavar="SEARCHSTRING")
parser.add_option("-i", "--idp",
                  help="unique ID of the IdP used to log in")
parser.add_option("-k", "--key", action='store_true',
                  help="prompt for key-passphrase (use Shibboleth password \
                  by default)")
parser.add_option("-l", "--list", action='store_true',
                  help="list all available IdP(s)")
parser.add_option("-s", "--slcs",
                  help="location of SLCS server (if not specified, use \
                  SLCS_SERVER system variable or settings from \
                  slcs-client.properties")
parser.add_option("-v", "--verbose",
                  action="store_true",
                  help="print status messages to stdout")
parser.add_option("", "--debug",
                  action="store_true",
                  help="print alot of messages to stdout")


# Set up a specific logger with our desired output level
log = logging.getLogger()
log_handle = logging.StreamHandler()
DEBUG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

verbose = logging.getLogger('slick-client-verbose')

def main():

    try:
        (options, args) = parser.parse_args()

        if len(sys.argv) == 1:
            parser.print_help()
            return

        if not path.exists(options.store_dir):
            os.mkdir(options.store_dir)

        # Verbose
        if options.verbose:
            formatter = logging.Formatter("%(message)s")
            log_handle.setFormatter(formatter)
            log.setLevel(logging.INFO)
            log.addHandler(log_handle)

        # Debug
        if options.debug:
            formatter = logging.Formatter(DEBUG_FORMAT)
            log_handle.setFormatter(formatter)
            log.setLevel(logging.DEBUG)
            log.addFilter(logging.Filter('slcs-client'))
            log.addHandler(log_handle)

        if options.idp_search:
            log.debug("List IDPs")
            idp_search = options.idp_search.lower()
            slcs_login_url = urlparse.urljoin(spUri, 'login')
            idps = list_idps(slcs_login_url)
            idps = dict(filter(lambda item: idp_search in item[0].lower(),
                               idps.items()))
            idp_keys = idps.keys()
            idp_keys.sort()
            print_list_wide(idp_keys)

        # List idps
        if options.list:
            log.debug("List IDPs")
            slcs_login_url = urlparse.urljoin(spUri, 'login')
            idps = list_idps(slcs_login_url)
            idp_keys = idps.keys()
            idp_keys.sort()
            print_list_wide(idp_keys)

        # Cert cert using specific IdP
        if options.idp or args:
            idp = options.idp or " ".join(args)
            slcs_login_url = spUri
            slcsresp = run(idp, slcs_login_url)

            verbose.info('Writing to files')
            key, pubKey, cert = slcs(slcsresp)
            key_path = path.join(options.store_dir, 'userkey.pem')
            if options.key:
                key.save_pem(key_path, callback=getPassphrase)
            else:
                key.save_pem(key_path, callback=getPassphrase_noinput)
            cert_path = path.join(options.store_dir, 'usercert.pem')
            cert_file = open(path.join(options.store_dir, 'usercert.pem'), 'w')
            cert_file.write(cert.as_pem())
            cert_file.close()
            verbose.info('DONE')
            print "\nexport X509_USER_CERT=%s \nexport X509_USER_KEY=%s" % (cert_path, key_path)
    except KeyboardInterrupt:
        print "\nCanceled"


if __name__ == '__main__':
    main()

