# This Python file uses the following encoding: utf-8

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

"""
A list of frequent operations performed through remote sessions.

Most commands passed to a session are routine invocations of common userland
tools. Nevertheless some of them require a certain effort to set up because
they are squeezed through the eye of the needle, the shell session.

The functionality in this module assumes a guest with the ordinary userland
tools available. Some of it might just work on Windows guests if the proper
environment (i. e. Cygwin) is present.

This module aims to provide convenient wrappers for butter-and-bread
functionality on a Linux system. Currently, the implemented functions fall
under four categories: ``grep``, ``stat``, ``test``, and common file ops.

grep:
Standard case search operations. It is always assumed that binaries in the path
should be searched (the ``-a`` flag).

stat:
Allows passing an optional format argument (``-c``). Custom wrappers for
extracting *atime*, *ctime*, and *mtime*, etc exist.

test:
Allows for testing existence, permissions and other properties of files.

file ops:
Simple file operations executed through sessions. Most functions boil down to
executing simple commands like ls, tar, md5sum, etc. If these operations return
non-0, a :py:class:`RuntimeError` is raised, containing the commands's error
message. All functions :py:func:`shlex.quote` their args for better security.

"""

import re
from os.path import join
from os.path import split as path_split
from shlex import quote

from aexpect.exceptions import ShellCmdError

# Need this import for sphinx and other documentation to produce links later on
# from .client import ShellSession


###############################################################################
# grep(1)
###############################################################################


def grep(session, expr, path, check=False, flags=None):
    """
    Invoke ``grep`` on guest searching for *expr* in *path*. Throws a
    ``TypeError`` in case the API assumptions are violated.

    :param session: session to run the command on
    :type session: ShellSession
    :param str expr: search expression
    :param str path: file to search
    :param bool check: whether to quietly run grep for a boolean check
    :param str flags: extra flags passed to ``grep`` on the command line
    :returns: whether there is a match or not or what ``grep`` emits on stdout
              if the check mode is disabled
    :rtype: bool or str
    """
    flags = flags if flags else ["a"]
    flagstr = " ".join(["-" + flag for flag in flags if flag.isalnum()])
    grep_command = "grep %s '%s' '%s'" % (flagstr, expr, path)
    status, output = session.cmd_status_output(grep_command)
    if check:
        return status == 0
    if status != 0:
        raise ShellCmdError(grep_command, status, output)
    return output


###############################################################################
# stat(2)
###############################################################################


def stat(session, path, fmt=None):
    """
    Wrapper for ``stat``.

    :param session: session to run the command on
    :type session: ShellSession
    :param str path: path to the filesystem entry to stat
    :param str fmt: optional format passed to ``-d``
    :returns: standard output of stat(1) on ``path``
    :rtype: str
    """
    if fmt is None:
        return session.cmd_output(r"stat '%s'" % path)

    if not isinstance(fmt, str) or fmt[0] != "%":
        raise RuntimeError("%s is not a valid format string for stat(1)" % fmt)

    return session.cmd_output(r"stat -c %s '%s'" % (fmt, path))


def get_atime(session, path, human_readable=False):
    """
    Query the access time.

    :param session: session to run the command on
    :type session: ShellSession
    :param str path: path to the filesystem entry to stat
    :param bool human_readable: whether to use human readable format or seconds
                                since Epoch
    :returns: standard output of stat(1) querying the access time of ``path``
    :rtype: str
    """
    return stat(session, path, fmt="%x" if human_readable else "%X")


def get_mtime(session, path, human_readable=False):
    """
    Query the modification time.

    :param session: session to run the command on
    :type session: ShellSession
    :param str path: path to the filesystem entry to stat
    :param bool human_readable: whether to use human readable format or seconds
                                since Epoch
    :returns: standard output of stat(1) querying the last modification time
              of ``path``
    :rtype: str
    """
    return stat(session, path, fmt="%z" if human_readable else "%Z")


def get_ctime(session, path, human_readable=False):
    """
    Query the change time.

    :param session: session to run the command on
    :type session: ShellSession
    :param str path: path to the filesystem entry to stat
    :param bool human_readable: whether to use human readable format or seconds
                                since Epoch
    :returns: standard output of stat(1) querying the last change time of
              ``path``
    :rtype: str
    """
    return stat(session, path, fmt="%y" if human_readable else "%Y")


def get_size(session, path, human_readable=False):
    """
    Query the file size.

    :param session: session to run the command on
    :type session: ShellSession
    :param str path: path to the filesystem entry to stat
    :param bool human_readable: whether to use human readable format or seconds
                                since Epoch
    :returns: standard output of stat(1) querying the size of ``path``
    :rtype: int
    """
    return int(stat(session, path, fmt="%s" if human_readable else "%S"))


###############################################################################
# test(1)
###############################################################################


def test(session, path, flag):
    """
    Wrapper for ``test``.

    :param session: session to run the command on
    :type session: ShellSession
    :param str path: path to the filesystem entry to test
    :param str flag: Flag passed to test
    :returns: status of test(1) on ``path``
    :rtype: int
    """
    if not isinstance(flag, str) or flag[0] != "-":
        raise RuntimeError("%s is not a valid flag string for test(1)" % flag)

    return int(session.cmd_status(r"test %s '%s'" % (flag, path)))


def is_directory(session, path):
    """
    Check if a directory exists on a given guest.

    :param session: session to run the command on
    :type session: ShellSession
    :param str path: path to the directory to check
    :returns: whether the directory exists
    :rtype: bool
    """
    return test(session, path, flag="-d") == 0


def is_regular_file(session, path):
    """
    Check if a regular file exists on a given guest.

    :param session: session to run the command on
    :type session: ShellSession
    :param str path: path to the regular file to check
    :returns: whether the regular file exists
    :rtype: bool
    """
    return test(session, path, flag="-f") == 0


def is_nonzero_size_file(session, path):
    """
    Check if a regular file exists on a given guest.

    :param session: session to run the command on
    :type session: ShellSession
    :param str path: path to the regular file to check
    :returns: whether the regular file exists and is nonzero size
    :rtype: bool
    """
    return test(session, path, flag="-s") == 0


###############################################################################
# file ops
###############################################################################


def hash_file(session, filename, method='md5'):
    """
    Calculate hash of given file from a session.

    :param session: session to run the command on
    :type session: ShellSession
    :param str filename: full path of file that should be hashed
    :param str method: method for hashing
    :returns: hash of file, a hex number
    :rtype: str
    :raises: :py:class:`RuntimeError` if hash command failed (e.g. file not
             found) or resulting output does not have expected format
    :raises: :py:class:`ValueError` if given method is not (yet) supported
    """
    if method not in ['md5']:
        raise ValueError('only method "md5" supported yet')

    cmd = 'md5sum'
    expect_len = 32

    # run cmd on shell
    status, output = session.cmd_status_output(cmd + ' ' + quote(filename))
    if output:
        output = output.strip()
    if status != 0 or not output:
        raise RuntimeError('Could not hash {} using {}: {}'
                           .format(filename, cmd, output))

    # parse output
    hash_str = output.split(maxsplit=1)[0].lower()

    # check length and all chars are hex
    if expect_len and len(hash_str) != expect_len:
        raise RuntimeError('Resulting hash string has unexpected length {}: {}'
                           .format(len(hash_str), hash_str))
    if hash_str.strip('0123456789abcdef'):
        raise RuntimeError('Resulting hash string has unexpected characters: '
                           + hash_str)
    return hash_str


def extract_tarball(session, tarball, target_dir):
    """
    Extract tarball to given dir from a session.

    :param session: session to run the command on
    :type session: ShellSession
    :param str tarball: full path of tar file that should be extracted
    :param str target_dir: name of directory where tarball should be extracted
    :raises: :py:class:`RuntimeError` if tar command returned non-null
    """
    cmd = 'tar -C {} --strip-components=1 -xapf {}' \
          .format(quote(target_dir), quote(tarball))
    status, output = session.cmd_status_output(cmd)
    if output:
        output = output.strip()
    if status != 0:
        raise RuntimeError('Failed to extract {} to {}: {}'
                           .format(tarball, target_dir, output))


def ls(session, dir_name):  # pylint: disable=C0103
    """
    Run `ls` in given directory through a session.

    :param session: session to run the command on
    :type session: ShellSession
    :param str dir_name: name of directory
    :returns: names of files in dir (without path components)
    :rtype: [str]

    Just like :py:func:`os.listdir`, does not include file names starting with
    dot (`'.'`)
    """
    cmd = 'ls -1UNq {}'.format(quote(dir_name))
    status, output = session.cmd_status_output(cmd)
    if output:
        output = output.strip()
    if status == 2:      # probably just nothing found
        return []
    if status != 0:
        raise RuntimeError('Failed to ls {}: {}'
                           .format(dir_name, output))
    return output.splitlines()


def glob(session, glob_pattern):
    """
    Find files matching given pattern through a session.

    :param session: session to run the command on
    :type session: ShellSession
    :param str glob_pattern: pattern of filenames where `*`, `?` and such match
                             any string or not-empty-string and so on.
    :returns: file names matching pattern, including path (like glob.glob)
    :rtype: [str]
    :raises: :py:class:`RuntimeError` if tar ls-command returned non-null and
             non-2 status

    Much like :py:func:`glob.glob` but implemented using `ls`.

    The glob matching is done locally, not with `ls` since quoting also makes
    the glob characters '*' and '?' regular characters, so are not interpreted
    any more in shell.
    """
    path_part, name_pattern = path_split(glob_pattern)
    all_filenames = ls(session, path_part)

    # convert pattern: escape \ . ? *
    pattern = re.escape(name_pattern)

    # convert pattern: convert shell globs to regex
    pattern = pattern.replace(r'\*', '.*').replace(r'\?', '.')

    # convert pattern: require match whole file name; compile for speed-up
    pattern = re.compile(pattern + '$')
    return [join(path_part, filename) for filename in all_filenames
            if pattern.match(filename)]


def cat(session, filename):
    """
    Get contents of a text file from a session.

    :param session: session to run the command on
    :type session: ShellSession
    :param str filename: full path of file
    :returns: file contents
    :rtype: str
    :raises: :py:class:`RuntimeError` if cat command fails

    Should only be used for very short files without tabs or other fancy
    contents. Otherwise better download file or use some other method.
    """
    cmd = 'cat ' + quote(filename)
    status, output = session.cmd_status_output(cmd)
    if output:
        output = output.strip()
    if status != 0:
        raise RuntimeError('Failed to cat {}: {}'.format(filename, output))
    return output


def tempdir(session):
    """
    Create a temporary directory in a safe way through a session.

    :param session: session to run the command on
    :type session: ShellSession
    :returns: name of temporary directory
    :rtype: str
    :raises: :py:class:`RuntimeError` if mktemp returns non-zero exit status

    Calls `mktemp -d`, refer to `man` for more info.
    """
    status, output = session.cmd_status_output('mktemp -d')
    if output:
        output = output.strip()
    if status != 0:
        raise RuntimeError('Failed to create temporary directory: {}'
                           .format(output))
    return output


def tempfile(session):
    """
    Create a temporary file in a safe way through a session.

    :param session: session to run the command on
    :type session: ShellSession
    :returns: name of temporary file
    :rtype: str
    :raises: :py:class:`RuntimeError` if mktemp returns non-zero exit status

    Calls `mktemp`, refer to `man` for more info.
    """
    status, output = session.cmd_status_output('mktemp')
    if output:
        output = output.strip()
    if status != 0:
        raise RuntimeError('Failed to create temporary file: {}'
                           .format(output))
    return output


def move(session, source, target):
    """
    Move file or directory from source to target / Rename source to target.

    :param session: session to run the command on
    :type session: ShellSession
    :param str source: full path of existing file or directory
    :param str target: full path of new file or directory
    :raises: :py:class:`RuntimeError` if mv returns non-zero exit status

    Calls `mv source target` through a session. See `man mv` for what source
    and target can be and what behavior to expect.
    """
    cmd = 'mv {} {}'.format(quote(source), quote(target))
    status, output = session.cmd_status_output(cmd)
    if status != 0:
        raise RuntimeError('Failed to mv {} to {}: {}'
                           .format(source, target,
                                   output.strip() if output else ''))


def copy(session, source, target):
    """
    Copy file or directory from source to target.

    :param session: session to run the command on
    :type session: ShellSession
    :param str source: full path of existing file or directory
    :param str target: full path of new file or directory
    :raises: :py:class:`RuntimeError` if cp returns non-zero exit status

    Calls `cp source target` through a session. See `man cp` for what source
    and target can be and what behavior to expect.
    """
    cmd = 'cp {} {}'.format(quote(source), quote(target))
    status, output = session.cmd_status_output(cmd)
    if status != 0:
        raise RuntimeError('Failed to cp {} to {}: {}'
                           .format(source, target,
                                   output.strip() if output else ''))


def rmtree(session, path):
    """
    Remove a directory including its contents.

    :param session: session to run the command on
    :type session: ShellSession
    :param str path: directory to remove
    :raises: :py:class:`RuntimeError` if deletion fails

    Calls `rm -rf`.
    """
    cmd = 'rm -rf ' + quote(path)
    status, output = session.cmd_status_output(cmd)
    if status != 0:
        raise RuntimeError('Failed to remove {}: {}'
                           .format(path, output.strip() if output else ''))
