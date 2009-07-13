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
password = ''
user_name = os.getenv('USERNAME')

def readpass():
    from getpass import getpass
    global password
    password = getpass("Password:")
    return password

def readuser():
    return raw_input("Username [%s]:" % user_name) or user_name

def getPassword():
    return password


def getPassphrase(verify):
    from getpass import getpass
    while 1:
        p1=getpass('Enter passphrase:')
        p2=getpass('Verify passphrase:')
        if p1==p2:
            break
    return p1


def getPassphrase_noinput(verify):
    return password

