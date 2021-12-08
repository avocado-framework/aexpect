#!/bin/env python
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See LICENSE for more details.
#
# Copyright: Red Hat Inc. 2013-2015
# Author: Lucas Meneghel Rodrigues <lmr@redhat.com>

"""Aexpect setup script"""

from setuptools import setup

if __name__ == '__main__':
    setup(name='aexpect',
          version='1.6.4',
          description='Aexpect',
          author='Aexpect developers',
          author_email='avocado-devel@redhat.com',
          url='http://avocado-framework.github.io/',
          packages=['aexpect',
                    'aexpect.utils'],
          scripts=['scripts/aexpect_helper'],
          test_suite='tests',
          install_requires=['six'])
