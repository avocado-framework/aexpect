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
# selftests pylint: disable=C0111,C0111,W0613,R0913,E1101

import glob
import html
import os
import re
import shutil
import unittest.mock

from aexpect import client, remote, remote_door
from aexpect.client import RemoteSession

mock = unittest.mock


# noinspection PyUnusedLocal
def _local_login(
    _client,
    host,
    port,
    username,
    password,
    prompt,
    linesep="\n",
    log_filename=None,
    log_function=None,
    timeout=10,
    internal_timeout=10,
    interface=None,
):
    return RemoteSession("sh", prompt=prompt, client=_client)


# noinspection PyUnusedLocal
def _local_copy(
    address,
    _client,
    username,
    password,
    port,
    local_path,
    remote_path,
    limit="",
    log_filename=None,
    log_function=None,
    verbose=False,
    timeout=600,
    interface=None,
    filesize=None,
    directory=True,
):
    shutil.copy(local_path, remote_path)


@mock.patch("aexpect.remote_door.remote.copy_files_to", _local_copy)
@mock.patch("aexpect.remote_door.remote.wait_for_login", _local_login)
class RemoteDoorTest(unittest.TestCase):
    """Unit test class for the remote door."""

    def setUp(self):
        self.session = RemoteSession("sh", client="ssh")
        if not os.path.isdir(remote_door.REMOTE_PYTHON_PATH):
            os.mkdir(remote_door.REMOTE_PYTHON_PATH)

        self.has_remote_objects = hasattr(remote_door, "Pyro4")
        if self.has_remote_objects:
            self.pyro = mock.patch(remote_door.Pyro4)
            self.server = mock.patch(remote_door.server)
            self.nameserver = mock.patch(remote_door.nameserver)
        else:
            self.pyro = remote_door.Pyro4 = mock.MagicMock()
            self.server = remote_door.server = mock.MagicMock()
            self.nameserver = remote_door.nameserver = mock.MagicMock()

    def tearDown(self):
        for control_file in glob.glob("tmp*.control"):
            os.unlink(control_file)
        for control_file in glob.glob(
            os.path.join(remote_door.REMOTE_CONTROL_DIR, "tmp*.control")
        ):
            os.unlink(control_file)
        deployed_remote_door = os.path.join(
            remote_door.REMOTE_PYTHON_PATH, "remote_door.py"
        )
        if os.path.exists(deployed_remote_door):
            os.unlink(deployed_remote_door)
        os.rmdir(remote_door.REMOTE_PYTHON_PATH)
        self.session.close()

        if self.has_remote_objects:
            self.pyro.stop()
            self.server.stop()
            self.nameserver.stop()
        else:
            del remote_door.Pyro4
            del remote_door.server
            del remote_door.nameserver

    def test_run_remote_util(self):
        """Test that a remote utility runs properly."""
        result = remote_door.run_remote_util(self.session, "math", "gcd", 2, 3)
        self.assertEqual(int(result), 1)
        local_controls = glob.glob("tmp*.control")
        remote_controls = glob.glob(
            os.path.join(remote_door.REMOTE_CONTROL_DIR, "tmp*.control")
        )
        self.assertEqual(len(local_controls), len(remote_controls))
        self.assertEqual(len(remote_controls), 1)
        self.assertEqual(
            os.path.basename(local_controls[0]),
            os.path.basename(remote_controls[0]),
        )
        with open(remote_controls[0], encoding="utf-8") as handle:
            control_lines = handle.readlines()
        self.assertIn("import math\n", control_lines)
        self.assertIn("result = math.gcd(2, 3)\n", control_lines)

    def test_run_remote_util_arg_types(self):
        """Test that a remote utility runs properly with different argument types."""
        result = remote_door.run_remote_util(
            self.session,
            "json",
            "dumps",
            ["foo", {"bar": ["baz", None, 1.0, 2]}],
            skipkeys=False,
            separators=None,
            # must be boolean but we want to test string
            allow_nan="string for yes",
        )
        self.assertEqual(result, '["foo", {"bar": ["baz", null, 1.0, 2]}]')
        local_controls = glob.glob("tmp*.control")
        remote_controls = glob.glob(
            os.path.join(remote_door.REMOTE_CONTROL_DIR, "tmp*.control")
        )
        self.assertEqual(len(local_controls), len(remote_controls))
        self.assertEqual(len(remote_controls), 1)
        self.assertEqual(
            os.path.basename(local_controls[0]),
            os.path.basename(remote_controls[0]),
        )
        with open(remote_controls[0], encoding="utf-8") as handle:
            control_lines = handle.readlines()
        self.assertIn("import json\n", control_lines)
        self.assertIn(
            "result = json.dumps(['foo', {'bar': ['baz', None, 1.0, 2]}], "
            "allow_nan=r'string for yes', separators=None, skipkeys=False)\n",
            control_lines,
        )

    def test_run_remote_util_object(self):
        """Test that a remote utility object runs properly."""
        result = remote_door.run_remote_util(
            self.session, "collections", "OrderedDict().get", "akey"
        )
        self.assertEqual(result, "None")

        local_controls = glob.glob("tmp*.control")
        remote_controls = glob.glob(
            os.path.join(remote_door.REMOTE_CONTROL_DIR, "tmp*.control")
        )
        self.assertEqual(len(local_controls), len(remote_controls))
        self.assertEqual(len(remote_controls), 1)
        self.assertEqual(
            os.path.basename(local_controls[0]),
            os.path.basename(remote_controls[0]),
        )
        with open(remote_controls[0], encoding="utf-8") as handle:
            control_lines = handle.readlines()
        self.assertIn(
            "result = collections.OrderedDict().get(r'akey')\n", control_lines
        )

    def test_run_remote_decorator(self):
        """Test that a remote decorated function runs properly."""

        @remote_door.run_remotely
        def add_one(number):
            """A small decorated test function with extra nesting."""

            def do_nothing():

                pass

            do_nothing()
            return number + 1

        result = add_one(self.session, 3)  # pylint: disable=E1121
        self.assertEqual(int(result), 4)

        local_controls = glob.glob("tmp*.control")
        remote_controls = glob.glob(
            os.path.join(remote_door.REMOTE_CONTROL_DIR, "tmp*.control")
        )
        self.assertEqual(len(local_controls), len(remote_controls))
        self.assertEqual(len(remote_controls), 1)
        self.assertEqual(
            os.path.basename(local_controls[0]),
            os.path.basename(remote_controls[0]),
        )
        with open(remote_controls[0], encoding="utf-8") as handle:
            control_lines = handle.readlines()
        self.assertIn("def add_one(number):\n", control_lines)
        self.assertIn("result = add_one(3)\n", control_lines)

    def test_get_remote_object(self):
        """Test that a remote object can be retrieved properly."""
        self.session = mock.MagicMock(name="session")
        self.session.client = "ssh"
        disconnect = self.pyro.errors.PyroError = Exception
        self.pyro.Proxy.side_effect = [
            disconnect("no such object"),
            mock.DEFAULT,
        ]
        self.session.get_output.return_value = "Local object sharing ready\n"
        self.session.get_output.return_value += "RESULT = None\n"

        remote_door.get_remote_object("html", self.session, "testhost", 4242)

        if hasattr(self.session.cmd, "assert_called_once"):
            self.session.sendline.assert_called_once()
        else:
            self.assertEqual(self.session.sendline.call_count, 1)
        command = self.session.sendline.call_args[0][0]
        match = re.match(r"python3 /tmp/(tmp.+\.control)", command)
        self.assertIsNotNone(
            match, "A control file has to be called on the peer side"
        )
        control_file = match.group(1)
        local_controls = glob.glob("tmp*.control")
        remote_controls = glob.glob(
            os.path.join(remote_door.REMOTE_CONTROL_DIR, "tmp*.control")
        )
        self.assertEqual(len(local_controls), len(remote_controls))
        self.assertEqual(len(remote_controls), 1)
        self.assertEqual(
            os.path.basename(local_controls[0]),
            os.path.basename(remote_controls[0]),
        )
        self.assertEqual(control_file, os.path.basename(remote_controls[0]))
        with open(control_file, encoding="utf-8") as handle:
            control_lines = handle.readlines()
            self.assertIn("import remote_door\n", control_lines)
            self.assertIn(
                "result = remote_door.share_local_object(r'html', "
                "expose_wl=None, host=r'testhost', object_wl=None, "
                "port=4242)\n",
                control_lines,
            )

        # since the local run was fake redo it here
        self.server.is_private_attribute = lambda x: False
        remote_door.share_local_object("html", "testhost", 4242)
        self.server.expose.assert_called()
        # TODO: to make the remote door usable with nearly no dependencies
        # we use a lot of internal classes and functions to make sharing a
        # local object possible but this makes testing these less accessible
        self.server.expose.assert_any_call(html.escape)
        self.server.expose.assert_any_call(html.unescape)

    def test_share_remote_objects(self):
        """Test that a remote object can be shared properly and remotely."""
        self.session = mock.MagicMock(name="session")
        self.session.client = "ssh"
        remote_door.NS_MODULE = "pyro.name.server"

        control_file = os.path.join(
            remote_door.REMOTE_CONTROL_DIR, "tmpxxxxxxxx.control"
        )
        with open(control_file, "wt", encoding="utf-8") as handle:
            handle.write("print('Remote objects shared over the network')")

        middleware = remote_door.share_remote_objects(
            self.session, control_file, "testhost", 4242, os_type="linux"
        )
        # we just test dummy initialization for the remote object control server
        middleware.close()

        if hasattr(self.session.cmd, "assert_called_once"):
            self.session.cmd.assert_called_once()
        else:
            self.assertEqual(self.session.cmd.call_count, 1)
        command = self.session.cmd.call_args[0][0]
        self.assertEqual(
            f"python -m {remote_door.NS_MODULE} -n testhost -p 4242 &", command
        )

    def test_import_remote_exceptions(self):
        """Test that selected remote exceptions are properly imported and deserialized."""
        preselected_exceptions = [
            "aexpect.remote.RemoteError",
            "aexpect.remote.LoginError",
            "aexpect.remote.TransferError",
        ]
        remote_door.import_remote_exceptions(preselected_exceptions)
        register_method = self.pyro.util.SerializerBase.register_dict_to_class
        self.assertEqual(len(register_method.mock_calls), 3)

        def get_first_arg(call):
            # python 3.8 and above only have the much simpler call:
            # return call.args[0]
            call_args = str(call).replace("call(", "").rstrip(")").split(", ")
            return call_args[0].replace("'", "")

        for i, exception in enumerate(preselected_exceptions):
            self.assertEqual(
                exception, get_first_arg(register_method.mock_calls[i])
            )

        register_method.reset_mock()
        preselected_modules = ["aexpect.exceptions", "aexpect.remote"]
        remote_door.import_remote_exceptions([], modules=preselected_modules)
        imported_classes = [
            get_first_arg(c) for c in register_method.mock_calls
        ]
        # assert some detected exceptions from the exceptions module
        self.assertIn("aexpect.exceptions.ExpectError", imported_classes)
        self.assertIn("aexpect.exceptions.ShellError", imported_classes)
        # assert some detected exceptions from the remote module
        self.assertIn("aexpect.remote.RemoteError", imported_classes)
        self.assertIn("aexpect.remote.UDPError", imported_classes)

    def test_expose_remote_classes(self):
        """Test that selected remote classes are properly exposed."""
        preselected_classes = [
            "aexpect.client.ShellSession",
            "aexpect.remote.LoginError",
        ]
        remote_door.expose_remote_classes(preselected_classes)
        expose_method = self.server.expose
        self.assertEqual(
            expose_method.mock_calls[0], mock.call(client.ShellSession)
        )
        self.assertEqual(expose_method.mock_calls[1], mock.call(client.Expect))
        self.assertEqual(expose_method.mock_calls[2], mock.call(client.Tail))
        self.assertEqual(expose_method.mock_calls[3], mock.call(client.Spawn))
        self.assertNotEqual(expose_method.mock_calls[4], mock.call(object))
        self.assertEqual(
            expose_method.mock_calls[4], mock.call(remote.LoginError)
        )
        self.assertEqual(
            expose_method.mock_calls[5], mock.call(remote.RemoteError)
        )

        expose_method.reset_mock()
        preselected_modules = ["aexpect.client"]
        remote_door.expose_remote_classes([], modules=preselected_modules)
        self.assertIn(
            mock.call(client.ExpectError),
            expose_method.mock_calls,
            "classes imported from elsewhere are exposed",
        )
        self.assertIn(
            mock.call(client.ShellSession),
            expose_method.mock_calls,
            "defined classes are exposed",
        )
