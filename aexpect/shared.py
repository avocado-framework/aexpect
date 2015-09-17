import os
import fcntl
import termios

BASE_DIR = os.environ.get('TMPDIR', '/tmp')


def get_lock_fd(filename):
    if not os.path.exists(filename):
        open(filename, "w").close()
    fd = os.open(filename, os.O_RDWR)
    fcntl.lockf(fd, fcntl.LOCK_EX)
    return fd


def unlock_fd(fd):
    fcntl.lockf(fd, fcntl.LOCK_UN)
    os.close(fd)


def is_file_locked(filename):
    try:
        fd = os.open(filename, os.O_RDWR)
    except OSError:
        return False
    try:
        fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        os.close(fd)
        return True
    fcntl.lockf(fd, fcntl.LOCK_UN)
    os.close(fd)
    return False


def wait_for_lock(filename):
    fd = get_lock_fd(filename)
    unlock_fd(fd)


def makeraw(shell_fd):
    attr = termios.tcgetattr(shell_fd)
    attr[0] &= ~(termios.IGNBRK | termios.BRKINT | termios.PARMRK |
                 termios.ISTRIP | termios.INLCR | termios.IGNCR |
                 termios.ICRNL | termios.IXON)
    attr[1] &= ~termios.OPOST
    attr[2] &= ~(termios.CSIZE | termios.PARENB)
    attr[2] |= termios.CS8
    attr[3] &= ~(termios.ECHO | termios.ECHONL | termios.ICANON |
                 termios.ISIG | termios.IEXTEN)
    termios.tcsetattr(shell_fd, termios.TCSANOW, attr)


def makestandard(shell_fd, echo):
    attr = termios.tcgetattr(shell_fd)
    attr[0] &= ~termios.INLCR
    attr[0] &= ~termios.ICRNL
    attr[0] &= ~termios.IGNCR
    attr[1] &= ~termios.OPOST
    if echo:
        attr[3] |= termios.ECHO
    else:
        attr[3] &= ~termios.ECHO
    termios.tcsetattr(shell_fd, termios.TCSANOW, attr)


def get_filenames(base_dir):
    return [os.path.join(base_dir, s) for s in
            "shell-pid", "status", "output", "inpipe", "ctrlpipe",
            "lock-server-running", "lock-client-starting",
            "server-log"]


def get_reader_filename(base_dir, reader):
    return os.path.join(base_dir, "outpipe-%s" % reader)
