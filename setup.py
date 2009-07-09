from setuptools import setup, find_packages
import sys, os

version = '1.0'

setup(name='slick',
      version=version,
      description="Commandline tool for generating and signing a SWITCH SLCS certificate.",
      long_description=open(os.path.join("README")).read() + "\n" +
                       open(os.path.join("CHANGES")).read(),
      classifiers=[
        "Topic :: Security :: Cryptography",
        "Programming Language :: Python",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Topic :: System :: Distributed Computing",
        "Intended Audience :: End Users/Desktop",
        "Environment :: Console",
        "Topic :: Security",
        ],
      keywords='',
      author='Russell Sim',
      author_email='russell.sim@arcs.org.au',
      url='http://code.arcs.org.au/gitorious/shibboleth/slick',
      download_url='http://code.arcs.org.au/pypi/slick/',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
          'arcs.gsi',
      ],
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      slick-init = slick.client:main
      """,
      )
