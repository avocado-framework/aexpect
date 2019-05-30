#!/usr/bin/env python

import unittest

import remote_door


class DummySession(object):

    def __init__(self):
        self.recorded_calls = []

    def cmd(self, command, print_func=None):
        self.recorded_calls.append(command)


class Guest2GuestTest(unittest.TestCase):

    def setUp(self):
        self.session = DummySession()

    def test_run_remote_util(self):
        remote_door.run_remote_util(self.session, "foo_util", "bar_func",
                                    42, "spring", sing="zazz")
        self.assertIn("> /tmp/control", self.session.recorded_calls[0],
                      "A control file has to be generated for the peer")
        self.assertIn("import foo_util", self.session.recorded_calls[0])
        self.assertIn("foo_util.bar_func(42, \'\"\'\"\'spring\'\"\'\"\', sing=\'\"\'\"\'zazz\'\"\'\"\')",
                      self.session.recorded_calls[0])
        self.assertEqual(self.session.recorded_calls[1],
                         "python3 /tmp/control",
                         "The peer has to be called to run the generated control")

    def test_run_remote_util_object(self):
        util_object = "BarClass(val1, 'val2')"
        remote_door.run_remote_util(self.session, "foo_util",
                                    "%s.baz_func" % util_object,
                                    "Wonderland is fun", wanderer=None)
        self.assertIn("> /tmp/control", self.session.recorded_calls[0],
                      "A control file has to be generated for the peer")
        self.assertIn("import foo_util", self.session.recorded_calls[0])
        self.assertIn("foo_util.BarClass(val1, \'\"\'\"\'val2\'\"\'\"\').baz_func(\'\"\'\"\'Wonderland is fun\'\"\'\"\', wanderer=None)",
                      self.session.recorded_calls[0])
        self.assertEqual(self.session.recorded_calls[1],
                         "python3 /tmp/control",
                         "The peer has to be called to run the generated control")
