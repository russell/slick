Introduction
============

This tool provides an easy way for users to retrieve their SLCS certificates from a SWITCH SLCS server.

slick-init Usage
----------------

.. program:: slick-init

.. cmdoption:: -d <dir>, --storedir=<dir>

   the directory to store the certificate/key and config file.

.. cmdoption:: -i <idp>, --idp=<idp>

   the name of the IDP to use

.. cmdoption:: -s <slcs>, --slcs=<slcs>

    location of SLCS server (if not specified, use
    SLCS_SERVER system variable or settings from
    [storedir]/slcs-client.properties

.. cmdoption:: -k, --key

   prompt for key-passphrase (use Shibboleth password
   by default)

.. cmdoption:: -l, --list

   list all available IdP(s

.. cmdoption:: -w, --write

   write the arguments specified on the command line to
   a config file

.. cmdoption:: -v, --verbose

   print status messages to stdout

.. cmdoption:: -h, --help

   show the help message and exit


Config File
-----------

The contents of a simple config file::

  $ cat ~/slcs-client.properties
  [slcs]
  idp = VPAC
  url = https://slcs1.arcs.org.au/SLCS/login

Install
=======

Ubuntu
------
::

  apt-get install python-setuptools python-m2crypto

  easy_install --find-links 'http://code.arcs.org.au/pypi/slick/ http://code.arcs.org.au/pypi/arcs.shibboleth.client/ http://code.arcs.org.au/pypi/arcs.gsi/' slick

Centos5
-------

Change to a directory where you would install optional software. When using ``virutalenv`` a subdirectory will be created with it's own ``bin/`` ``lib/`` directories.

::

  $ yum install python-setuptools swig openssl-devel gcc subversion

  $ sudo easy_install virtualenv
  $ virtualenv slick
  $ cd slick

Once we activate the virtual envionment the PATH will be changed so that 
files within slick/bin/ will take precidence.

::

  $ . ./bin/activate
  (slick)$ svn co http://svn.osafoundation.org/m2crypto/tags/0.19.1/ m2crypto
  (slick)$ cd m2crypto
  (slick)$ python setup.py build_ext -I/usr/include/openssl install
  (slick)$ easy_install --find-links 'http://code.arcs.org.au/pypi/slick/ http://code.arcs.org.au/pypi/arcs.shibboleth.client/ http://code.arcs.org.au/pypi/arcs.gsi/' slick
  (slick)$ deactivate

Once the virtulenv is deactivated you can still run the command directly

::

  ./bin/slick-init

