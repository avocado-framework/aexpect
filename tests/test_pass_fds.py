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
# Author: Xu Han <xuhan@redhat.com>

import time
import unittest

from aexpect import client


SLEEP = 1

DEVNULL = "/dev/null"
LIST_FD_CMD = ('''python -c "import os; os.system('ls -l /proc/%d/fd' % '''
               '''os.getpid())"''')


class PassfdsTest(unittest.TestCase):

    def test_pass_fds_spawn(self):
        """
        Tests fd passing for `client.Spawn`
        """
        with open(DEVNULL, "r") as devnull:
            fd = devnull.fileno()

            child = client.Spawn(LIST_FD_CMD)
            time.sleep(SLEEP)
            self.assertFalse(DEVNULL in child.get_output())
            child.close()

            child = client.Spawn(LIST_FD_CMD, pass_fds=[fd])
            time.sleep(SLEEP)
            self.assertTrue(DEVNULL in child.get_output())
            child.close()

    def test_pass_fds_tail(self):
        """
        Tests fd passing for `client.Tail`
        """
        with open(DEVNULL, "r") as devnull:
            fd = devnull.fileno()

            child = client.Tail(LIST_FD_CMD)
            time.sleep(SLEEP)
            self.assertFalse(DEVNULL in child.get_output())
            child.close()

            child = client.Tail(LIST_FD_CMD, pass_fds=[fd])
            time.sleep(SLEEP)
            self.assertTrue(DEVNULL in child.get_output())
            child.close()

    def test_pass_fds_expect(self):
        """
        Tests fd passing for `client.Expect`
        """
        with open(DEVNULL, "r") as devnull:
            fd = devnull.fileno()

            child = client.Expect(LIST_FD_CMD)
            time.sleep(SLEEP)
            self.assertFalse(DEVNULL in child.get_output())
            child.close()

            child = client.Expect(LIST_FD_CMD, pass_fds=[fd])
            time.sleep(SLEEP)
            self.assertTrue(DEVNULL in child.get_output())
            child.close()

    def test_pass_fds_session(self):
        """
        Tests fd passing for `client.ShellSession`
        """
        with open(DEVNULL, "r") as devnull:
            fd = devnull.fileno()

            child = client.ShellSession(LIST_FD_CMD)
            time.sleep(SLEEP)
            self.assertFalse(DEVNULL in child.get_output())
            child.close()

            child = client.ShellSession(LIST_FD_CMD, pass_fds=[fd])
            time.sleep(SLEEP)
            self.assertTrue(DEVNULL in child.get_output())
            child.close()
