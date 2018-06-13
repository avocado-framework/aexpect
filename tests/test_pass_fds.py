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

# selftests pylint: disable=C0111,C0111

import os
import unittest

from aexpect import client


LIST_FD_CMD = ('''python -c "import os; os.system('ls -l /proc/%d/fd' % '''
               '''os.getpid())"''')


class PassfdsTest(unittest.TestCase):

    @unittest.skipUnless(os.path.exists('/proc/1/fd'), "requires Linux")
    def test_pass_fds_spawn(self):
        """
        Tests fd passing for `client.Spawn`
        """
        with open(os.devnull, "r") as devnull:
            fd_null = devnull.fileno()

            child = client.Spawn(LIST_FD_CMD)
            self.assertFalse(bool(child.get_status()),
                             "child terminated abnormally")
            self.assertFalse(os.devnull in child.get_output())
            child.close()

            child = client.Spawn(LIST_FD_CMD, pass_fds=[fd_null])
            self.assertFalse(bool(child.get_status()),
                             "child terminated abnormally")
            self.assertTrue(os.devnull in child.get_output())
            child.close()


if __name__ == '__main__':
    unittest.main()
