import commands
import signal
import os


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
    children = commands.getoutput("ps --ppid=%d -o pid=" % pid).split()
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
    return commands.getoutput("ps -L --ppid=%d -o lwp" % ppid).split('\n')[1:]


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
        proc_name = commands.getoutput(cmd)
        if '<defunct>' in proc_name:
            defunct = True
            break
    return defunct
