Aexpect: Control your interactive applications
==============================================

This project provides services similar to the `pexpect` python library,
so to speak, spawn and control interactive applications, such as `ssh`,
`sftp` and others although it can be useful for pure streams as well.

It's enhanced with multi-pattern matching, convenience features for
not-only-linux terminals as well as support for terminals that "spit"
extra output from time to time (eg. kernel messages) over the output.

There are also extra classes to simplify executing parts of a program
on a different location (distributed programming) or writing controls
executed on another host (metaprogramming).

Simple usage
------------

.. code-block:: python

    >>> import aexpect
    >>> import time
    >>> dir(aexpect)
    ['Expect', 'ExpectError', 'ExpectProcessTerminatedError', 'ExpectTimeoutError', 'ShellCmdError', 'ShellError', 'ShellProcessTerminatedError', 'ShellSession', 'ShellStatusError', 'ShellTimeoutError', 'Spawn', 'Tail', '__builtins__', '__cached__', '__doc__', '__file__', '__loader__', '__name__', '__package__', '__path__', '__spec__', 'client', 'exceptions', 'kill_tail_threads', 'remote', 'rss_client', 'run_bg', 'run_fg', 'run_tail', 'shared', 'utils']
    >>> session = aexpect.ShellSession("bash")
    >>> session.cmd("ls /tmp/b")
    '1  2\n'
    >>> session.cmd("cat /tmp/b/1")
    'Hello\n'
    >>> session.cmd("cat /tmp/b/2")
    'World\n'
    >>> dir(session)
    ['_ShellSession__RE_STATUS', '__class__', '__del__', '__delattr__', '__dict__', '__dir__', '__doc__', '__enter__', '__eq__', '__exit__', '__format__', '__ge__', '__getattribute__', '__getinitargs__', '__getstate__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__setstate__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_add_close_hook', '_add_reader', '_aexpect_helper', '_close_aexpect_helper', '_close_reader_fds', '_get_fd', '_join_thread', '_read_nonblocking', '_start_thread', '_tail', 'a_id', 'auto_close', 'close', 'close_hooks', 'closed', 'cmd', 'cmd_output', 'cmd_output_safe', 'cmd_status', 'cmd_status_output', 'command', 'ctrlpipe_filename', 'echo', 'encoding', 'get_command_output', 'get_command_status', 'get_command_status_output', 'get_id', 'get_output', 'get_pid', 'get_status', 'get_stripped_output', 'inpipe_filename', 'is_alive', 'is_defunct', 'is_responsive', 'kill', 'linesep', 'lock_client_starting_filename', 'lock_server_running_filename', 'log_file', 'log_file_fd', 'match_patterns', 'match_patterns_multiline', 'output_filename', 'output_func', 'output_params', 'output_prefix', 'prompt', 'read_nonblocking', 'read_until_any_line_matches', 'read_until_last_line_matches', 'read_until_last_word_matches', 'read_until_output_matches', 'read_up_to_prompt', 'reader_fds', 'reader_filenames', 'readers', 'remove_command_echo', 'remove_last_nonempty_line', 'send', 'send_ctrl', 'sendcontrol', 'sendline', 'server_log_filename', 'set_linesep', 'set_log_file', 'set_output_func', 'set_output_params', 'set_output_prefix', 'set_prompt', 'set_status_test_command', 'set_termination_func', 'set_termination_params', 'shell_pid_filename', 'status_filename', 'status_test_command', 'tail_thread', 'termination_func', 'termination_params', 'thread_name']
    >>> session.sendline("for I in $(seq 10); do echo $I; sleep 1; done")
    >>> session.read_nonblocking(0.1, 2)
    >>> time.sleep(10)
    >>> session.read_nonblocking(0.1, 2)
    '2\n3\n4\n5\n6\n7\n8\n9\n10\n[medic@fedora ~ \x1b[1;31m\x1b[0m]$ '
    >>> session.sendline("for I in $(seq 10); do echo $I; sleep 1; done")
    >>> session.read_nonblocking(1.5, 2)
    '1\n2\n3\n4\n'
    >>> session.sendline("for I in $(seq 10); do echo $I; sleep 1; done")
    >>> session.read_until_output_matches("3", timeout=10)
    (0, '1\n2\n3\n')
    >>> session.sendline("for I in $(seq 10); do echo $I; sleep 1; done")
    >>> session.read_until_output_matches(["5", "7", "2", "foo"], timeout=10)
    (2, '1\n2\n')
    >>> session.cmd_status("true")
    0
    >>> session.cmd_status("false")
    1
    >>> session.is_alive()
    True
    >>> session.is_responsive()
    True
    >>> session.sendline("exit")
    >>> session.is_alive()
    False
    >>> session.is_responsive()
    False

To get more information use the python `help()` command on various objects,
we do keep our docstrings updated. To get details about all `aexpect.client`
objects simply run `python -c "import aexpect; [print(f'\n{name}\n{len(name)
* '='}', func.__doc__) for name, func in aexpect.__dict__.items() if
hasattr(func, '__doc__')]"`

Debugging
---------

Using this even for purely bash-like constructs is good as you can leverage
the python debugger to interactively walk your issues. Especially the
`pydevd` project is great as you can debug code from multiple machines on
in a single Eclipse to see concurency issues. Execution is as simple as
`pip install pydevd` on all machines, adding
`pydevd.settrace(eclipse_machine_ip, True, True)` directly into the code
replacing the `eclipse_machine_ip` with IP address of the machine where
Eclipse will be running (eg. 127.0.0.1 for localhost). The following `True`
are to redirect stdout/stderr which is usually useful but sometimes might
lead to issues. Then you need to start the python debugger inside Eclipse
by entering debug view and starting the pydev server
`pydev->Start debug server`. Now you are ready and simply execute your
application the way you are used to, once it reaches the `pydev.settrace`
line it will dial to the Eclipse server and show up in your debug view,
showing the code you are debugging even though it's on a different machine,
allowing you to single-step across multiple processes.
