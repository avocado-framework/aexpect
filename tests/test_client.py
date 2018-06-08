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
# Copyright: Red Hat Inc. 2018
# Author: Cleber Rosa <crosa@redhat.com>

import random
import string
import sys
import unittest

from aexpect import client


class ClientTest(unittest.TestCase):

    def test_client_spawn(self):
        """
        Tests the basic spawning of an interactive process
        """
        key = "".join([random.choice(string.ascii_uppercase)
                       for _ in range(10)])
        python = client.Spawn(sys.executable)
        self.assertTrue(python.is_alive())
        python.sendline("print('%s')" % key)
        python.sendline("quit()")
        self.assertEqual(python.get_status(), 0)
        self.assertIn(key, python.get_output())
        self.assertFalse(python.is_alive())
