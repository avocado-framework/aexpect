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

import os
# pylint: disable=E0611

from distutils.core import setup

VIRTUAL_ENV = 'VIRTUAL_ENV' in os.environ


def get_dir(system_path=None, virtual_path=None):
    """
    Retrieve VIRTUAL_ENV friendly path
    :param system_path: Relative system path
    :param virtual_path: Overrides system_path for virtual_env only
    :return: VIRTUAL_ENV friendly path
    """
    if virtual_path is None:
        virtual_path = system_path
    if VIRTUAL_ENV:
        if virtual_path is None:
            virtual_path = []
        return os.path.join(*virtual_path)
    else:
        if system_path is None:
            system_path = []
        return os.path.join(*(['/'] + system_path))


def get_avocado_libexec_dir():
    if VIRTUAL_ENV:
        return get_dir(['libexec'])
    elif os.path.exists('/usr/libexec'):    # RHEL-like distro
        return get_dir(['usr', 'libexec', 'avocado'])
    else:                                   # Debian-like distro
        return get_dir(['usr', 'lib', 'avocado'])


if __name__ == '__main__':
    setup(name='aexpect',
          version='1.2.0',
          description='Aexpect',
          author='Aexpect developers',
          author_email='avocado-devel@redhat.com',
          url='http://avocado-framework.github.io/',
          packages=['aexpect',
                    'aexpect.utils'],
          scripts=['scripts/aexpect-helper'])
