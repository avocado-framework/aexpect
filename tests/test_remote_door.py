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

import unittest

import remote_door


class DummySession(object):  # pylint: disable=R0903
    """Dummy class for a session."""

    def __init__(self):
        self.recorded_calls = []

    def cmd(self, command, print_func=None):  # pylint: disable=W0613
        """Dummy cmd call."""
        self.recorded_calls.append(command)


class RemoteDoorTest(unittest.TestCase):
    """Unit test class for the remote door."""

    def setUp(self):
        self.session = DummySession()

    def test_run_remote_util(self):
        """Test that a remote utility can be run properly."""
        remote_door.run_remote_util(self.session, "foo_util", "bar_func",
                                    42, "spring", sing="zazz")
        self.assertIn("> /tmp/control", self.session.recorded_calls[0],
                      "A control file has to be generated for the peer")
        self.assertIn("import foo_util", self.session.recorded_calls[0])
        self.assertIn("foo_util.bar_func(42, \'\"\'\"\'spring\'\"\'\"\', "
                      "sing=\'\"\'\"\'zazz\'\"\'\"\')",
                      self.session.recorded_calls[0])
        self.assertEqual(self.session.recorded_calls[1],
                         "python3 /tmp/control",
                         "The peer has to be called to run the generated control")

    def test_run_remote_util_object(self):
        """Test that a remote utility object can be run properly."""
        util_object = "BarClass(val1, 'val2')"
        remote_door.run_remote_util(self.session, "foo_util",
                                    "%s.baz_func" % util_object,
                                    "Wonderland is fun", wanderer=None)
        self.assertIn("> /tmp/control", self.session.recorded_calls[0],
                      "A control file has to be generated for the peer")
        self.assertIn("import foo_util", self.session.recorded_calls[0])
        self.assertIn("foo_util.BarClass(val1, \'\"\'\"\'val2\'\"\'\"\').baz_func("
                      "\'\"\'\"\'Wonderland is fun\'\"\'\"\', wanderer=None)",
                      self.session.recorded_calls[0])
        self.assertEqual(self.session.recorded_calls[1],
                         "python3 /tmp/control",
                         "The peer has to be called to run the generated control")
