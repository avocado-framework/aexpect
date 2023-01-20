#!/bin/env python3
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
# Copyright: Red Hat Inc. 2023
# Author: Lukas Doktor <ldoktor@redhat.com>
# pylint: disable=R,C

from setuptools import setup

# Handle systems with setuptools < 40
try:
    from setuptools import find_namespace_packages
except ImportError:
    packages = ["aexpect_ops"]
else:
    packages = find_namespace_packages(include=["aexpect_ops"])

setup(
    name="aexpect-remote",
    description="Features that extends aexpect functionalities of remote execution",
    version=1,
    author="Avocado Developers",
    author_email="avocado-devel@redhat.com",
    url="http://avocado-framework.github.io/",
    packages=packages,
    include_package_data=True,
    install_requires=["aexpect"]
)
