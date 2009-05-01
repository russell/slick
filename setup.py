from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='slick',
      version=version,
      description="Client tools for slcs",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Russell Sim',
      author_email='russell.sim@arcs.org.au',
      url='',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
          'M2Crypto',
      ],
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      slick-init = slick.client:main
      """,
      )
