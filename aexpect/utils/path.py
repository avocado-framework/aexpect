import os


class CmdNotFoundError(Exception):

    """
    Indicates that the command was not found in the system after a search.

    :param cmd: String with the command.
    :param paths: List of paths where we looked after.
    """

    def __init__(self, cmd, paths):
        super(CmdNotFoundError, self)
        self.cmd = cmd
        self.paths = paths

    def __str__(self):
        return ("Command '%s' could not be found in any of the PATH dirs: %s" %
                (self.cmd, self.paths))


def find_command(cmd, default=None):
    """
    Try to find a command in the PATH, paranoid version.

    :param cmd: Command to be found.
    :param default: Command path to use as a fallback if not found
                    in the standard directories.
    :raise: :class:`aexpect.utils.path.CmdNotFoundError` in case the
            command was not found and no default was given.
    """
    common_bin_paths = ["/usr/libexec", "/usr/local/sbin", "/usr/local/bin",
                        "/usr/sbin", "/usr/bin", "/sbin", "/bin"]
    try:
        path_paths = os.environ['PATH'].split(":")
    except IndexError:
        path_paths = []
    path_paths = list(set(common_bin_paths + path_paths))

    for dir_path in path_paths:
        cmd_path = os.path.join(dir_path, cmd)
        if os.path.isfile(cmd_path):
            return os.path.abspath(cmd_path)

    if default is not None:
        return default
    else:
        raise CmdNotFoundError(cmd, path_paths)


def init_dir(*args):
    """
    Wrapper around os.path.join that creates dirs based on the final path.

    :param args: List of dir arguments that will be os.path.joined.
    :type directory: list
    :return: directory.
    :rtype: str
    """
    directory = os.path.join(*args)
    if not os.path.isdir(directory):
        os.makedirs(directory)
    return directory
