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

import subprocess
import signal
import sys
import os
import fcntl


def getoutput(cmd):
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    return proc.communicate()[0].decode().rstrip("\n\r")


class CmdError(Exception):

    def __init__(self, command=None, result=None):
        self.command = command
        self.result = result

    def __str__(self):
        if self.result is not None:
            if self.result.interrupted:
                return "Command %s interrupted by user (Ctrl+C)" % self.command
            if self.result.exit_status is None:
                msg = "Command '%s' failed and is not responding to signals"
                msg %= self.command
            else:
                msg = "Command '%s' failed (rc=%d)"
                msg %= (self.command, self.result.exit_status)
            return msg
        else:
            return "CmdError"


def safe_kill(pid, sig):
    """
    Attempt to send a signal to a given process that may or may not exist.

    :param sig: Signal number.
    """
    try:
        os.kill(pid, sig)
        return True
    except OSError:
        return False


def kill_process_tree(pid, sig=signal.SIGKILL):
    """
    Signal a process and all of its children.

    If the process does not exist -- return.

    :param pid: The pid of the process to signal.
    :param sig: The signal to send to the processes.
    """
    if not safe_kill(pid, signal.SIGSTOP):
        return
    children = getoutput("ps --ppid=%d -o pid=" % pid).split()
    for child in children:
        kill_process_tree(int(child), sig)
    safe_kill(pid, sig)
    safe_kill(pid, signal.SIGCONT)


def get_children_pids(ppid):
    """
    Get all PIDs of children/threads of parent ppid
    param ppid: parent PID
    return: list of PIDs of all children/threads of ppid
    """
    return getoutput("ps -L --ppid=%d -o lwp" % ppid).split('\n')[1:]


def process_in_ptree_is_defunct(ppid):
    """
    Verify if any processes deriving from PPID are in the defunct state.

    Attempt to verify if parent process and any children from PPID is defunct
    (zombie) or not.

    :param ppid: The parent PID of the process to verify.
    """
    defunct = False
    try:
        pids = get_children_pids(ppid)
    except CmdError:  # Process doesn't exist
        return True
    for pid in pids:
        cmd = "ps --no-headers -o cmd %d" % int(pid)
        proc_name = getoutput(cmd)
        if '<defunct>' in proc_name:
            defunct = True
            break
    return defunct


PIPE = subprocess.PIPE
STDOUT = subprocess.STDOUT


if sys.version_info < (3, 2):
    # Actually we should rewrite `subprocess.Popen` with a complete
    # implementation, but it is not easy to be done and will be
    # defective, so just tweak it according to our needs.
    def Popen(*args, **kwargs):
        """
        A helper function to simulate fd passing feature for python
        lower than 3.2
        """
        kwargs.setdefault("pass_fds", ())
        kwargs.setdefault("close_fds", True)
        pass_fds = kwargs.pop("pass_fds")
        if bool(pass_fds):
            kwargs["close_fds"] = False
        # Make sure all the fds have CLOEXEC unset
        for fd in pass_fds:
            fd = int(fd)
            fflags = fcntl.fcntl(fd, fcntl.F_GETFD)
            fflags &= ~fcntl.FD_CLOEXEC
            fcntl.fcntl(fd, fcntl.F_SETFD, fflags)
        return subprocess.Popen(*args, **kwargs)
else:
    Popen = subprocess.Popen
