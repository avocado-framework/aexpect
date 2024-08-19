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
# Copyright: Red Hat Inc. 2024
# Author: Lukas Doktor <ldoktor@redhat.com>

# selftests pylint: disable=C0111,C0111

import unittest

from aexpect.utils import astring


class Astring(unittest.TestCase):

    def test_strip_console_codes(self):
        """
        Try various strip_console_codes
        """
        strip = astring.strip_console_codes
        self.assertEqual("simple color test",
                         strip("simple\x1b[33;1m color \x1b[0mtest"))
        self.assertEqual("[33;1mstarts with code", "[33;1mstarts with code")
        self.assertEqual("ends with escape\x1b", "ends with escape\x1b")


if __name__ == '__main__':
    unittest.main()