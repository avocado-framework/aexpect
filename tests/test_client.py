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

import os
import sys
import time
import unittest

from aexpect import client


SLEEP = 0.2


class ClientTest(unittest.TestCase):

    def test_client_spawn_python(self):
        """
        Tests the basic spawning of an interactive process

        This test uses the Python interpreter itself, and to make sure
        lines sent are effective, python code that creates a temporary
        file is send to the interpreter and checked by the test.

        The sending of lines is not synchronous to their execution, so
        some level of wait is necessary for somewhat reliable results.
        """
        python = client.Spawn(sys.executable)
        self.assertTrue(python.is_alive())
        # it may take some time for the process to start **and**
        # produce output
        python.sendline("import tempfile")
        python.sendline("tempfile.mkstemp()")
        time.sleep(SLEEP)
        lines = python.get_output().splitlines()
        # this line should look like: ">>> >>> (5, '/tmp/tmpxxxx')"
        _, tempfile_quote = lines[-2][9:-1].split(' ', 1)
        tempfile = tempfile_quote[1:-1]
        self.assertTrue(os.path.exists(tempfile))
        python.sendline("import os")
        python.sendline("os.unlink('%s')" % tempfile)
        time.sleep(SLEEP)
        self.assertFalse(os.path.exists(tempfile))
