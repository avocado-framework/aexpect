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
import time
import unittest

from aexpect import client


class ClientTest(unittest.TestCase):

    def test_client_spawn(self):
        """
        Tests the basic spawning of an interactive process
        """
        key = "".join(
            [random.choice(string.ascii_uppercase) for _ in range(10)]
        )
        python = client.Spawn(sys.executable)
        self.assertTrue(python.is_alive())
        python.sendline(f"print('{key}')")
        python.sendline("quit()")
        self.assertEqual(python.get_status(), 0)
        self.assertIn(key, python.get_output())
        self.assertFalse(python.is_alive())


class CommandsTests(unittest.TestCase):

    def setUp(self):
        non_get_cmds = (
            "get_id",
            "get_output",
            "get_pid",
            "get_status",
            "get_stripped_output",
        )
        self.cmds = [
            cmd
            for cmd in dir(client.ShellSession)
            if cmd.startswith("get") and cmd not in non_get_cmds
        ]
        self.cmds.extend(
            cmd for cmd in dir(client.ShellSession) if cmd.startswith("cmd")
        )

    def test_cmd_true(self):
        """Check that the true command finishes properly"""
        for cmd in self.cmds:
            if cmd in (
                "get_id",
                "get_output",
                "get_pid",
                "get_status",
                "get_stripped_output",
            ):
                # These are not commands
                continue
            session = client.ShellSession("sh")
            getattr(session, cmd)("true")

    def test_cmd_terminated(self):
        """
        Check that when we kill ourselves, ShellProcessTerminatedError is
        raised
        """
        for cmd in self.cmds:
            if cmd in (
                "get_id",
                "get_output",
                "get_pid",
                "get_status",
                "get_stripped_output",
            ):
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
                out += getattr(session, cmd)("true")
                self.fail(
                    "Killed session did not produce 'ShellError' using "
                    f"command {cmd} ({self.cmds})\n{out}"
                )
            except client.ShellError as details:
                if cmd in ("cmd_output", "cmd_output_safe"):
                    if not isinstance(
                        details, client.ShellProcessTerminatedError
                    ):
                        self.fail(
                            f"Incorrect exception '{details}' "
                            f"({type(details)}) was raised using command"
                            f" {cmd} ({self.cmds})\n{out}"
                        )

    def test_cmd_timeout(self):
        """Check that 0s timeout timeouts"""
        for cmd in self.cmds:
            if cmd in (
                "get_id",
                "get_output",
                "get_pid",
                "get_status",
                "get_stripped_output",
            ):
                # These are not commands
                continue
            session = client.ShellSession("sh")
            try:
                execute = (
                    f"{sys.executable} -c " "'import time; time.sleep(10)'"
                )
                out = getattr(session, cmd)(execute, timeout=0)
                self.fail(
                    "Killed session did not produce 'ShellError' using "
                    f"command {cmd} ({self.cmds})\n{out}"
                )
            except client.ShellError as details:
                if cmd in ("cmd_output", "cmd_output_safe"):
                    if not isinstance(details, client.ShellTimeoutError):
                        self.fail(
                            f"Incorrect exception '{details}' "
                            f"({type(details)}) was raised "
                            f"using command {cmd} ({self.cmds})"
                        )

    @unittest.skipUnless(
        os.environ.get("AEXPECT_TIME_SENSITIVE"),
        "AEXPECT_TIME_SENSITIVE env variable not set",
    )
    def test_cmd_output_with_inner_timeout(self):
        """
        cmd_output_safe uses 0.5s inner timeout, make sure all lines are
        present in the output.
        """
        session = client.ShellSession("sh")
        out = session.cmd_output_safe(
            "echo FIRST LINE; sleep 2; "
            "echo SECOND LINE; sleep 2; "
            "echo THIRD LINE"
        )
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
        self.assertEqual(
            fds_after,
            fds_before,
            msg="fd leak: Closing the session didn't close "
            "the file descriptors",
        )


class EncodingTest(unittest.TestCase):

    DEBUG = False

    # Encoding used to translate between Unicode text and bytes
    ENCODING = "utf-8"

    # text whose characters decode to multiple byte
    TEXT = "嗨😀"

    REPETITIONS_FOR_TAIL = 3

    MAX_OFFSET = 10

    def analyze_output(self, offset, new_output):
        """Helper; Compare output to expectation"""
        # remove the leading offset whitespace
        idx = 0
        for idx, char in enumerate(new_output):
            if char.isspace():
                continue
            if char == self.TEXT[0]:
                break
            self.fail(
                f"Unexpected char found at {idx=}: {char!r} ({char.encode(self.ENCODING)}). "
                f"Line start: {new_output[:50]}, line length: {len(new_output)}"
            )
        if idx == len(new_output):
            self.fail("Test text not found!")
        if idx > 0:
            new_output = new_output[idx:]
        if self.DEBUG:
            print(f"Skipping {idx} whitespace chars at start")

        # print start and end, count chars
        n_chars = len(new_output)
        if self.DEBUG:
            print(f"Output for offset {offset}: len={n_chars}.")
            for idx, char in enumerate(new_output[:3]):
                print_char = chr(0x21B2) if char == "\n" else char
                print(
                    f"char {idx}: {print_char} ({char.encode(self.ENCODING)})",
                    end="; ",
                )
            print("...", end="")
            for idx, char in enumerate(new_output[-3:]):
                print_char = chr(0x21B2) if char == "\n" else char
                print(
                    f"char {n_chars-3+idx}: {print_char} ({char.encode(self.ENCODING)})",
                    end="; ",
                )
            print()
        return n_chars

    def analyze_results(self, all_lengths: list):
        """Helper: compare results, decide whether test was successful"""
        if not all_lengths:
            self.fail("no successful output analyses")
        expect = all_lengths[0]
        if any(curr_length != expect for curr_length in all_lengths[1:]):
            self.fail("There were differences in encoded output lengths")
        elif self.DEBUG:
            print("SUCCESS")

    @unittest.skipUnless(os.name == "posix", "Unix/Linux/macOS only")
    def test_shell(self):
        """
        Tests correct decoding of multibyte characters in ShellSession.

        Even if reading is interrupted with incomplete characters, we
        expect correct output.

        Spawns a python session that produces multibyte output
        with various single-byte offsets.
        """
        sess = client.ShellSession("/bin/sh")
        sess.cmd_output(
            "echo 'Just removing potential initial prompt from output'"
        )
        all_lengths = []
        output = self.TEXT.encode(self.ENCODING)
        repetitions = 1024 // len(output) + 1
        for offset in range(self.MAX_OFFSET):
            if self.DEBUG:
                print(f"Start testing with shell and offset {offset}")
            cmd = (
                f"import os; import sys; t=b' '*{offset}+{output!r}*{repetitions}+b'\\n'; "
                f"f=os.fdopen(sys.stdout.fileno(), 'wb', closefd=False); f.write(t); f.flush()"
            )
            new_output = sess.cmd_output(f'{sys.executable} -c "{cmd}"')
            all_lengths.append(self.analyze_output(offset, new_output))
        sess.close()
        self.analyze_results(all_lengths)

    def test_tail(self):
        """
        Tests correct decoding of multibyte characters in Tail.

        Like test_shell, but using a Tail and repeating the output to get
        multiple lines of output. Requires custom output gatherer and
        termination function
        """
        output_buffer = []
        terminated = False

        def remember_output(new_output):
            nonlocal output_buffer
            output_buffer.append(new_output)

        def termination_func(_status):
            nonlocal terminated
            terminated = True

        output = self.TEXT.encode(self.ENCODING)
        repetitions = 1024 // len(output) + 1
        all_lengths = []
        for offset in range(self.MAX_OFFSET):
            terminated = False
            output_buffer = []
            cmd = (
                f"import os; import sys; t=b' '*{offset}+{output!r}*{repetitions}+b'\\n';"
                f"f=os.fdopen(sys.stdout.fileno(), 'wb', closefd=False); f.write(t); f.flush()"
            )
            for _ in range(self.REPETITIONS_FOR_TAIL - 1):
                cmd += "; f.write(t); f.flush()"
            if self.DEBUG:
                print("Spawning Tail")
            python = client.Tail(
                f'{sys.executable} -c "{cmd}"',
                output_func=remember_output,
                termination_func=termination_func,
            )
            if self.DEBUG:
                print(f"Listening for subproc {python.get_pid()}")
            for _ in range(1000):
                if terminated:
                    break
                if self.DEBUG:
                    print(".", end="", flush=True)
                time.sleep(0.01)
            if self.DEBUG:
                print("\nDone")
            python.close()
            for line in output_buffer:
                if line.startswith("(Process terminated "):
                    continue
                all_lengths.append(self.analyze_output(offset, line))

        self.analyze_results(all_lengths)


if __name__ == "__main__":
    unittest.main()
