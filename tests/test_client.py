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

# selftests pylint: disable=C0111,C0111

import os
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
        python.sendline(f"print('{key}')")
        python.sendline("quit()")
        self.assertEqual(python.get_status(), 0)
        self.assertIn(key, python.get_output())
        self.assertFalse(python.is_alive())


class CommandsTests(unittest.TestCase):

    def setUp(self):
        non_get_cmds = ('get_id', 'get_output', 'get_pid', 'get_status',
                        'get_stripped_output')
        self.cmds = [cmd for cmd in dir(client.ShellSession)
                     if cmd.startswith('get') and cmd not in non_get_cmds]
        self.cmds.extend(cmd for cmd in dir(client.ShellSession)
                         if cmd.startswith("cmd"))

    def test_cmd_true(self):
        """Check that the true command finishes properly"""
        for cmd in self.cmds:
            if cmd in ('get_id', 'get_output', 'get_pid', 'get_status',
                       'get_stripped_output'):
                # These are not commands
                continue
            session = client.ShellSession("sh")
            getattr(session, cmd)('true')

    def test_cmd_terminated(self):
        """
        Check that when we kill ourselves, ShellProcessTerminatedError is
        raised
        """
        for cmd in self.cmds:
            if cmd in ('get_id', 'get_output', 'get_pid', 'get_status',
                       'get_stripped_output'):
                # These are not commands
                continue
            session = client.ShellSession("sh")
            try:
                # We are executing the subprocess using "shell=True" which
                # creates a sub-shell. When we kill only that sub-shell,
                # our shell can still produce one prompt after it's
                # parent is killed making this command to succeed. Let's
                # make sure we try this at least twice as the second
                # command will be processed after the helper realizes
                # it's dead.
                out = getattr(session, cmd)(f"kill {session.get_pid()}")
                out += getattr(session, cmd)('true')
                self.fail("Killed session did not produce 'ShellError' using "
                          f"command {cmd} ({self.cmds})\n{out}")
            except client.ShellError as details:
                if cmd in ("cmd_output", "cmd_output_safe"):
                    if not isinstance(details,
                                      client.ShellProcessTerminatedError):
                        self.fail(f"Incorrect exception '{details}' "
                                  f"({type(details)}) was raised using command"
                                  f" {cmd} ({self.cmds})\n{out}")

    def test_cmd_timeout(self):
        """Check that 0s timeout timeouts"""
        for cmd in self.cmds:
            if cmd in ('get_id', 'get_output', 'get_pid', 'get_status',
                       'get_stripped_output'):
                # These are not commands
                continue
            session = client.ShellSession("sh")
            try:
                execute = (f"{sys.executable} -c "
                           "'import time; time.sleep(10)'")
                out = getattr(session, cmd)(execute, timeout=0)
                self.fail("Killed session did not produce 'ShellError' using "
                          f"command {cmd} ({self.cmds})\n{out}")
            except client.ShellError as details:
                if cmd in ("cmd_output", "cmd_output_safe"):
                    if not isinstance(details,
                                      client.ShellTimeoutError):
                        self.fail(f"Incorrect exception '{details}' "
                                  f"({type(details)}) was raised "
                                  f"using command {cmd} ({self.cmds})")

    @unittest.skipUnless(os.environ.get('AEXPECT_TIME_SENSITIVE'),
                         "AEXPECT_TIME_SENSITIVE env variable not set")
    def test_cmd_output_with_inner_timeout(self):
        """
        cmd_output_safe uses 0.5s inner timeout, make sure all lines are
        present in the output.
        """
        session = client.ShellSession("sh")
        out = session.cmd_output_safe("echo FIRST LINE; sleep 2; "
                                      "echo SECOND LINE; sleep 2; "
                                      "echo THIRD LINE")
        self.assertIn("FIRST LINE", out)
        self.assertIn("SECOND LINE", out)
        self.assertIn("THIRD LINE", out)

    def test_fd_leak(self):
        """
        Check file descriptors are not being leaked
        """
        def get_proc_fds():
            """
            Returns a set containing the fd names opened under the process

            :returns: set
            """
            # Omitting the last one since it is the one opened to
            # get the result from running the listdir method
            process_fds = os.listdir(f"/proc/{os.getpid()}/fd")[:-1]
            return set(process_fds)

        fds_before = get_proc_fds()
        session = client.ShellSession("sh")
        session.close()
        fds_after = get_proc_fds()
        self.assertEqual(fds_after, fds_before,
                         msg="fd leak: Closing the session didn't close "
                             "the file descriptors")
        session = None


if __name__ == '__main__':
    unittest.main()
