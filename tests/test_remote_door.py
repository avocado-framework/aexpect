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
# Copyright: Intra2net AG and aexpect contributors
# Author: Plamen Dimitrov <plamen.dimitrov@intra2net.com>
#
# selftests pylint: disable=C0111,C0111

import os
import glob
import re
import unittest
import unittest.mock as mock

from aexpect import remote_door


@remote_door.run_remotely
def add_one(number):
    """A small decorated test function."""
    return number + 1


@mock.patch('aexpect.remote_door.remote', mock.MagicMock())
class RemoteDoorTest(unittest.TestCase):
    """Unit test class for the remote door."""

    def setUp(self):
        self.session = mock.MagicMock(name='session')
        self.session.client = "ssh"

    def tearDown(self):
        for control_file in glob.glob("tmp*.control"):
            os.unlink(control_file)

    def test_run_remote_util(self):
        """Test that a remote utility can be run properly."""
        remote_door.run_remote_util(self.session, "foo_util", "bar_func",
                                    42, "spring", sing="zazz")
        # python 3.6 and above
        if hasattr(self.session.cmd, "assert_called_once"):
            self.session.cmd.assert_called_once()
        else:
            self.assertEqual(self.session.cmd.call_count, 1)
        command = self.session.cmd.call_args[0][0]
        self.assertTrue(re.match(r"python3 /tmp/tmp.+\.control", command),
                        "A control file has to be generated and called on the peer")
        control = os.path.basename(command.lstrip("python3 "))
        with open(control) as handle:
            control_lines = handle.readlines()
            self.assertIn("import foo_util\n", control_lines)
            self.assertIn("result = foo_util.bar_func(42, r'spring', sing=r'zazz')\n",
                          control_lines)

    def test_run_remote_util_object(self):
        """Test that a remote utility object can be run properly."""
        util_object = "BarClass(val1, 'val2')"
        remote_door.run_remote_util(self.session, "foo_util",
                                    "%s.baz_func" % util_object,
                                    "Wonderland is fun", wanderer=None)
        # python 3.6 and above
        if hasattr(self.session.cmd, "assert_called_once"):
            self.session.cmd.assert_called_once()
        else:
            self.assertEqual(self.session.cmd.call_count, 1)
        command = self.session.cmd.call_args[0][0]
        self.assertTrue(re.match(r"python3 /tmp/tmp.+\.control", command),
                        "A control file has to be generated and called on the peer")
        control = os.path.basename(command.lstrip("python3 "))
        with open(control) as handle:
            control_lines = handle.readlines()
            self.assertIn("import foo_util\n", control_lines)
            self.assertIn("result = foo_util.BarClass(val1, 'val2').baz_func("
                          "r'Wonderland is fun', wanderer=None)\n",
                          control_lines)

    def test_run_remote_decorator(self):
        """Test that a remote utility object can be run properly."""
        _ = add_one(self.session, 3)  # pylint: disable=E1121
        # python 3.6 and above
        if hasattr(self.session.cmd, "assert_called_once"):
            self.session.cmd.assert_called_once()
        else:
            self.assertEqual(self.session.cmd.call_count, 1)
        command = self.session.cmd.call_args[0][0]
        self.assertTrue(re.match(r"python3 /tmp/tmp.+\.control", command),
                        "A control file has to be generated and called on the peer")
        control = os.path.basename(command.lstrip("python3 "))
        with open(control) as handle:
            control_lines = handle.readlines()
            self.assertIn("def add_one(number):\n", control_lines)
            self.assertIn("    return number + 1\n", control_lines)
            self.assertIn("result = add_one(3)\n", control_lines)

    def test_run_remote_object(self):
        """Test that a remote utility object can be run properly."""
        remote_door.Pyro4 = mock.MagicMock()
        disconnect = remote_door.Pyro4.errors.PyroError = Exception
        remote_door.Pyro4.Proxy.side_effect = [disconnect("no such object"), mock.DEFAULT]
        self.session.get_output.return_value = "ready"
        remote_door.get_remote_object("module.MyClass", self.session,
                                      "testhost", 4242)
        if hasattr(self.session.cmd, "assert_called_once"):
            self.session.sendline.assert_called_once()
        else:
            self.assertEqual(self.session.sendline.call_count, 1)
        command = self.session.sendline.call_args[0][0]
        self.assertTrue(re.match(r"python3 /tmp/tmp.+\.control", command),
                        "A control file has to be generated and called on the peer")
        control = os.path.basename(command.lstrip("python3 "))
        with open(control) as handle:
            control_lines = handle.readlines()
            self.assertIn("import remote_door\n", control_lines)
            self.assertIn("result = remote_door.share_local_object(r'module.MyClass', "
                          "host=r'testhost', port=4242)\n",
                          control_lines)
