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
# selftests pylint: disable=C0111,C0111,W0613,R0913,E1101,C0301

import unittest.mock

from aexpect import remote
from aexpect.client import RemoteSession

mock = unittest.mock


class TestRemoteFunctions(unittest.TestCase):

    def setUp(self):
        session_read = mock.MagicMock()
        session_read.return_value = 12, remote.PROMPT_LINUX
        session_patch = mock.patch.object(
            RemoteSession, "read_until_last_line_matches", session_read
        )
        session_patch.start()
        self.addCleanup(session_patch.stop)

    def test_handle_prompts(self):
        output = remote.handle_prompts(
            RemoteSession(), "user", "pass", remote.PROMPT_LINUX
        )
        self.assertEqual(output, remote.PROMPT_LINUX)

    def test_remote_login(self):
        session = remote.remote_login(
            "ssh", "127.0.0.1", 22, "user", "pass", remote.PROMPT_LINUX
        )
        self.assertEqual(
            session.command,
            "ssh  -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -p 22"
            " -o PreferredAuthentications=password user@127.0.0.1",
        )

    def test_wait_for_login(self):
        session = remote.wait_for_login(
            "ssh", "127.0.0.1", 22, "user", "pass", remote.PROMPT_LINUX
        )
        self.assertEqual(
            session.command,
            "ssh  -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -p 22"
            " -o PreferredAuthentications=password user@127.0.0.1",
        )

    @mock.patch("aexpect.remote._remote_copy")
    def test_scp_to_remote(self, mock_remote_copy):
        remote.scp_to_remote(
            "127.0.0.1", 22, "user", "pass", "/local/path", "/remote/path"
        )
        mock_remote_copy.assert_called_once_with(mock.ANY, ["pass"], 600, 300, "scp")
        self.assertEqual(
            mock_remote_copy.call_args[0][0].command,
            r"scp -r -v -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o PreferredAuthentications=password  -P 22 /local/path user@\[127.0.0.1\]:/remote/path"
        )

    @mock.patch("aexpect.remote._remote_copy")
    def test_scp_from_remote(self, mock_remote_copy):
        remote.scp_from_remote(
            "127.0.0.1", 22, "user", "pass", "/remote/path", "/local/path"
        )
        mock_remote_copy.assert_called_once_with(mock.ANY, ["pass"], 600, 300, "scp")
        self.assertEqual(
            mock_remote_copy.call_args[0][0].command,
            r"scp -r -v -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o PreferredAuthentications=password  -P 22 user@\[127.0.0.1\]:/remote/path /local/path"
        )

    @mock.patch("aexpect.remote._remote_copy")
    def test_rsync_to_remote(self, mock_remote_copy):
        remote.rsync_to_remote(
            "127.0.0.1", 22, "user", "pass", "/local/path", "/remote/path"
        )
        mock_remote_copy.assert_called_once_with(mock.ANY, ["pass"], 600, 300, "rsync")
        self.assertEqual(
            mock_remote_copy.call_args[0][0].command,
            r"rsync -r -avz -e 'ssh -p 22 -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'  /local/path user@127.0.0.1:/remote/path"
        )

    @mock.patch("aexpect.remote._remote_copy")
    def test_scp_between_remotes(self, mock_remote_copy):
        remote.scp_between_remotes(
            "src_host",
            "dst_host",
            22,
            "src_pass",
            "dst_pass",
            "src_user",
            "dst_user",
            "/src/path",
            "/dst/path",
        )
        mock_remote_copy.assert_called_once_with(
            mock.ANY, ["src_pass", "dst_pass"], 600, 300, "scp"
        )
        self.assertEqual(
            mock_remote_copy.call_args[0][0].command,
            r"scp -r -v -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o PreferredAuthentications=password  -P 22 src_user@\[src_host\]:/src/path dst_user@\[dst_host\]:/dst/path"
        )

    @mock.patch("aexpect.remote._remote_copy")
    def test_rsync_from_remote(self, mock_remote_copy):
        remote.rsync_from_remote(
            "127.0.0.1", 22, "user", "pass", "/remote/path", "/local/path"
        )
        mock_remote_copy.assert_called_once_with(mock.ANY, ["pass"], 600, 300, "rsync")
        self.assertEqual(
            mock_remote_copy.call_args[0][0].command,
            r"rsync -r -avz -e 'ssh -p 22 -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'  user@127.0.0.1:/remote/path /local/path"
        )
