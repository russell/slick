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
import os, sys
from os import path
import logging
from cookielib import MozillaCookieJar

from arcs.shibboleth.client import Shibboleth, CredentialManager, Idp
from arcs.gsi.slcs import slcs_handler as slcs
from slick.settings import Settings, settings_options


usage = "usage: %prog [options] [idp]"
parser = OptionParser(usage)

settings_options(parser)
parser.add_option("-k", "--key", action='store_true',
                  help="use Shibboleth password as key passphrase")
parser.add_option("-w", "--write",
                  action="store_true",
                  help="write the idp specified on the command line to \
                  a config file")
parser.add_option("-v", "--verbose",
                  action="count",
                  help="print status messages to stdout")
parser.add_option("-V", "--version", action='store_true',
                  help="print version number and exit")

# Set up a specific logger with our desired output level
log = logging.getLogger('slick-client')
log_handle = logging.StreamHandler()
DEBUG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

def main(*arg):
    try:
        (options, args) = parser.parse_args()

        if options.version:
            from slick.common import version
            print version
            return

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

        settings = Settings(options, args)
        spUri = settings.slcs_url
        config_idp = settings.slcs_idp

        # Cert cert using specific IdP
        idp = Idp(config_idp)
        slcs_login_url = spUri
        c = CredentialManager()
        cj = MozillaCookieJar()
        shibopener = Shibboleth(idp, c, cj)
        slcsresp = shibopener.openurl(slcs_login_url)

        # Set the settings class idp to equal the idp handlers idp
        settings.slcs_idp = idp.idp

        log.info('Writing to files')
        cert = slcs(slcsresp)
        key_path = path.join(options.store_dir, 'userkey.pem')
        if not options.key:
            def callback(verify=False):
                from getpass import getpass
                while 1:
                    p1 = getpass('Enter passphrase(or none for idp password):')
                    if not p1:
                        p1 = c.get_password()
                        return p1
                    p2 = getpass('Verify passphrase:')
                    if p1 == p2:
                        return p1
                    print "Password doesn't match"
        else:
            def callback(verify=False):
                return c.get_password()

        cert.get_key()._key.save_pem(key_path, callback=callback)
        os.chmod(key_path, 0600)
        cert_path = path.join(options.store_dir, 'usercert.pem')
        cert_file = open(path.join(options.store_dir, 'usercert.pem'), 'w')
        cert_file.write(repr(cert))
        cert_file.close()
        os.chmod(cert_path, 0644)

        if options.write:
            log.info('Writing the config file')
            settings.save()

        print "\nexport X509_USER_CERT=%s\nexport X509_USER_KEY=%s" % \
                (cert_path, key_path)
        return
    except KeyboardInterrupt:
        print "\nCancelled"
        return

    if len(sys.argv) == 1:
        parser.print_help()

if __name__ == '__main__':
    main()

