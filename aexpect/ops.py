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
tools. Nevertheless, some of them require a certain effort to set up because
they are squeezed through the eye of the needle, the shell session.

The functionality in this module assumes a remote host with the ordinary userland
tools available. Some of it might just work on Windows remote hosts if the proper
environment (i. e. Cygwin) is present.

This module aims to provide convenient wrappers for butter-and-bread
functionality on a Linux system. Currently, the implemented functions fall
under a few categories: ``stat``, ``test``, common file ops, common utilities,
and system utilities.

stat:
Allows passing an optional format argument (``-c``). Custom wrappers for
extracting *atime*, *ctime*, and *mtime*, etc exist.

test:
Allows for testing existence, permissions and other properties of files.

file ops:
Simple file operations executed through sessions. Most functions boil down to
executing simple commands like ls, tar, md5sum, etc. If these operations return
non-0, a :py:class:`RuntimeError` is raised, containing the command's error
message. All functions :py:func:`shlex.quote` their args for better security.

utilities:
More complex linux utilities for tarball extraction, file hashing, etc.

system:
System related operations like restarting or stopping services.

..warning:: This module runs commands on raw shell sessions and although we usually
    quote the main arguments, we do not perform complex checks for escapes. It is
    meant only for some convenience in simple enough use cases and using it might
    result in data loss or worse.
"""

import logging
from shlex import quote

from aexpect.exceptions import ShellCmdError
# Need this import for sphinx and other documentation to produce links later on
# from .client import ShellSession

LOG = logging.getLogger(__name__)


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
        return session.cmd_output(f"stat {quote(path)}")

    if not isinstance(fmt, str) or fmt[0] != "%":
        raise RuntimeError(f"{fmt} is not a valid format string for stat(1)")

    return session.cmd_output(f"stat -c {fmt} {quote(path)}")


def get_atime(session, path, human_readable=False):
    """
    Query the access time.

    :param session: session to run the command on
    :type session: ShellSession
    :param str path: path to the filesystem entry to stat
    :param bool human_readable: whether to use human-readable format or seconds
                                since Epoch
    :returns: standard output of stat(1) querying the access time of ``path``
    :rtype: str
    """
    return stat(session, path, fmt=r"%x" if human_readable else "%X")


def get_mtime(session, path, human_readable=False):
    """
    Query the modification time.

    :param session: session to run the command on
    :type session: ShellSession
    :param str path: path to the filesystem entry to stat
    :param bool human_readable: whether to use human-readable format or seconds
                                since Epoch
    :returns: standard output of stat(1) querying the last modification time
              of ``path``
    :rtype: str
    """
    return stat(session, path, fmt=r"%z" if human_readable else r"%Z")


def get_ctime(session, path, human_readable=False):
    """
    Query the change time.

    :param session: session to run the command on
    :type session: ShellSession
    :param str path: path to the filesystem entry to stat
    :param bool human_readable: whether to use human-readable format or seconds
                                since Epoch
    :returns: standard output of stat(1) querying the last change time of
              ``path``
    :rtype: str
    """
    return stat(session, path, fmt=r"%y" if human_readable else r"%Y")


def get_size(session, path):
    """
    Query the file size.

    :param session: session to run the command on
    :type session: ShellSession
    :param str path: path to the filesystem entry to stat
    :returns: standard output of stat(1) querying the size of ``path``
    :rtype: int
    """
    return int(stat(session, path, fmt=r"%s"))


###############################################################################
# test(1)
###############################################################################


def test(session, path, flags):
    """
    Wrapper for ``test``.

    :param session: session to run the command on
    :type session: ShellSession
    :param str path: path to the filesystem entry to test
    :param str flags: flags passed to test
    :returns: status of test(1) on ``path`` as True or False
    :rtype: bool
    """
    return session.cmd_status(f"test {flags} {quote(path)}") == 0


def is_directory(session, path):
    """
    Check if a directory exists on a given remote host.

    :param session: session to run the command on
    :type session: ShellSession
    :param str path: path to the directory to check
    :returns: whether the directory exists
    :rtype: bool
    """
    return test(session, path, flags="-d")


def is_regular_file(session, path):
    """
    Check if a regular file exists on a given remote host.

    :param session: session to run the command on
    :type session: ShellSession
    :param str path: path to the regular file to check
    :returns: whether the regular file exists
    :rtype: bool
    """
    return test(session, path, flags="-f")


def is_nonzero_size_file(session, path):
    """
    Check if a regular file exists on a given remote host.

    :param session: session to run the command on
    :type session: ShellSession
    :param str path: path to the regular file to check
    :returns: whether the regular file exists and is nonzero size
    :rtype: bool
    """
    return test(session, path, flags="-s")


###############################################################################
# file ops
###############################################################################


def ls(session, path, quote_path=True, flags="-1UNq"):  # pylint: disable=C0103
    """
    Run `ls` in given directory through a session.

    :param session: session to run the command on
    :type session: ShellSession
    :param str path: absolute or relative path to list
    :param bool quote_path: whether to quote (escape) or not (expand) the path
    :param str flags: raw flags to pass to ls command
    :returns: names of files in dir (without path components)
    :rtype: [str]

    Just like :py:func:`os.listdir`, does not include file names starting with
    dot (`'.'`)
    """
    cmd = f'ls {flags} {quote(path)}' if quote_path else f'ls {flags} {path}'
    status, output = session.cmd_status_output(cmd)
    if output:
        output = output.strip()
    if status != 0:
        raise RuntimeError(f'Failed to ls {path}: {output}')
    return output.splitlines()


def move(session, source, target, quote_path=True, flags=""):
    """
    Move file or directory from source to target / rename source to target.

    :param session: session to run the command on
    :type session: ShellSession
    :param str source: full path of existing file or directory
    :param str target: full path of new file or directory
    :param bool quote_path: whether to quote (escape) or not (expand) the path
    :param str flags: raw flags to pass to mv command
    :raises: :py:class:`RuntimeError` if mv returns non-zero exit status

    Calls `mv source target` through a session. See `man mv` for what source
    and target can be and what behavior to expect.
    """
    cmd = f'mv {flags} {quote(source)} {quote(target)}' if quote_path \
        else f'mv {flags} {source} {target}'
    status, output = session.cmd_status_output(cmd)
    if status != 0:
        raise RuntimeError(f"Failed to move {source} to {target}: "
                           f"{output.strip() if output else ''}")


def copy(session, source, target, quote_path=True, flags=""):
    """
    Copy file or directory from source to target.

    :param session: session to run the command on
    :type session: ShellSession
    :param str source: full path of existing file or directory
    :param str target: full path of new file or directory
    :param bool quote_path: whether to quote (escape) or not (expand) the path
    :param str flags: raw flags to pass to cp command
    :raises: :py:class:`RuntimeError` if cp returns non-zero exit status

    Calls `cp source target` through a session. See `man cp` for what source
    and target can be and what behavior to expect.
    """
    cmd = f'cp {flags} {quote(source)} {quote(target)}' if quote_path \
        else f'cp {flags} {source} {target}'
    status, output = session.cmd_status_output(cmd)
    if status != 0:
        raise RuntimeError(f"Failed to copy {source} to {target}: "
                           f"{output.strip() if output else ''}")


def remove(session, path, quote_path=True, flags="-fr"):
    """
    Remove a directory including its contents.

    :param session: session to run the command on
    :type session: ShellSession
    :param str path: directory to remove
    :param bool quote_path: whether to quote (escape) or not (expand) the path
    :param str flags: raw flags to pass to rm command
    :raises: :py:class:`RuntimeError` if deletion fails

    Calls `rm -rf`.
    """
    cmd = f'rm {flags} {quote(path)}' if quote_path else f'rm {flags} {path}'
    status, output = session.cmd_status_output(cmd)
    if status != 0:
        raise RuntimeError(f"Failed to remove {path}: "
                           f"{output.strip() if output else ''}")


def make_tempdir(session, template=None):
    """
    Create a temporary directory in a safe way through a session.

    :param session: session to run the command on
    :type session: ShellSession
    :param template: directory name template as used in the standard command
    :type template: str or None
    :returns: name of temporary directory
    :rtype: str
    :raises: :py:class:`RuntimeError` if mktemp returns non-zero exit status

    Calls `mktemp -d`, refer to `man` for more info.
    """
    cmd = f'mktemp -d {template}' if template is not None else 'mktemp -d'
    status, output = session.cmd_status_output(cmd)
    if output:
        output = output.strip()
    if status != 0:
        raise RuntimeError(f'Failed to create temporary directory: {output}')
    return output


def make_tempfile(session, template=None):
    """
    Create a temporary file in a safe way through a session.

    :param session: session to run the command on
    :type session: ShellSession
    :param template: file name template as used in the standard command
    :type template: str or None
    :returns: name of temporary file
    :rtype: str
    :raises: :py:class:`RuntimeError` if mktemp returns non-zero exit status

    Calls `mktemp`, refer to `man` for more info.
    """
    cmd = f'mktemp {template}' if template is not None else 'mktemp'
    status, output = session.cmd_status_output(cmd)
    if output:
        output = output.strip()
    if status != 0:
        raise RuntimeError(f'Failed to create temporary file: {output}')
    return output


def cat(session, filename, quote_path=True, flags=""):
    """
    Get contents of a text file from a session.

    :param session: session to run the command on
    :type session: ShellSession
    :param str filename: full path of file
    :param bool quote_path: whether to quote (escape) or not (expand) the path
    :param str flags: raw flags to pass to cat command
    :returns: file contents
    :rtype: str
    :raises: :py:class:`RuntimeError` if cat command fails

    Should only be used for very small files without tabs or other fancy
    contents. Otherwise, it is better to download the file or use some other method.
    """
    cmd = f'cat {flags} {quote(filename)}' if quote_path else f'cat {flags} {filename}'
    status, output = session.cmd_status_output(cmd)
    if output:
        output = output.strip()
    if status != 0:
        raise RuntimeError(f'Failed to cat {filename}: {output}')
    return output


def sed_replace(session, pattern, replacement, filename):
    """
    Replace a pattern in a file using sed, raising an error if nothing is found.

    :param session: session of the remote host
    :type session: :py:class:`RemoteSession`
    :param str pattern: pattern to replace
    :param str replacement: string to replace the pattern for
    :param str filename: file with content to be replaced
    :raises: :py:class:`AssertionError` if nothing was replaced

    Using sed is convenient, but it does not error out when nothing is replaced
    and this can lead to false-positives when used inside tests.
    """
    LOG.info("Replacing {pattern} with {replacement} in {filename}")
    # for lines matching pattern, replace and print them (the p command won't work)
    cmd = f"""sed -ri '/{pattern}/{{
s//{replacement}/g
w /dev/stdout
}}' {filename}"""
    output = session.cmd(cmd)
    # make sure we have at least one line replaced
    if len(output.splitlines()) == 0:
        raise RuntimeError(f"No matches found by sed for pattern {pattern}")


def grep(session, expr, path, check=False, flags="-a"):
    """
    Invoke ``grep`` remotely searching for an expression in a path.

    :param session: session to run the command on
    :type session: ShellSession
    :param str expr: search expression
    :param str path: file to search
    :param bool check: whether to quietly run grep for a boolean check
    :param str flags: extra flags passed to ``grep`` on the command line
    :returns: whether there is a match or not or what ``grep`` emits on stdout
              if the check mode is disabled
    :rtype: bool or str
    :raises: ShellCmdError if the check mode is disabled and status is nonzero
    """
    grep_command = f"grep {flags} '{expr}' {quote(path)}"
    status, output = session.cmd_status_output(grep_command)
    if check:
        return status == 0
    if status != 0:
        raise ShellCmdError(grep_command, status, output)
    return output


###############################################################################
# utilities
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
    """
    cmd = f"{method}sum"

    # run cmd on shell
    status, output = session.cmd_status_output(cmd + ' ' + quote(filename))
    if output:
        output = output.strip()
    if status != 0 or not output:
        raise RuntimeError(f'Could not hash {filename} using {cmd}: {output}')

    # parse output
    hash_str = output.split(maxsplit=1)[0].lower()

    # check that all chars are hex
    if hash_str.strip('0123456789abcdef'):
        raise RuntimeError('Resulting hash string has unexpected characters: '
                           + hash_str)
    return hash_str


def extract_tarball(session, tarball, target_dir, flags="-ap"):
    """
    Extract tarball to given dir from a session.

    :param session: session to run the command on
    :type session: ShellSession
    :param str tarball: full path of tar file that should be extracted
    :param str target_dir: name of directory where tarball should be extracted
    :param str flags: extra flags passed to ``tar`` on the command line
    :raises: :py:class:`RuntimeError` if tar command returned non-null
    """
    cmd = f'tar -C {quote(target_dir)} {flags} -xf {quote(tarball)}'
    status, output = session.cmd_status_output(cmd)
    if output:
        output = output.strip()
    if status != 0:
        raise RuntimeError(f'Failed to extract {tarball} to {target_dir}: {output}')


###############################################################################
# system
###############################################################################


def start_services(session, services, timeout=60):
    """
    Try starting all services in given list.

    :param session: virtual machine session
    :type session: :py:class:`aexpect.ShellSession`
    :param services: list of services to modify
    :type services: [str]
    :param int timeout: timeout for each service to start
    :returns: statuses for each modified service
    :rtype: [int]
    """
    statuses = []
    for service in services:
        status = session.cmd_status(f'service {service} status')
        if status == 0:      # is running --> skip
            LOG.debug(f'Service {service} already started - skipping')
        elif status == 3:    # is stopped --> ok
            LOG.debug(f'Service {service} stopped - starting')
            status = session.cmd_status(f'service {service} start', timeout)
        else:                # not sure, try restarting
            LOG.debug(f'Querying status for service {service} resulted in '
                      f'unexpected return code {status}. Try starting it')
            status = session.cmd_status(f'service {service} start', timeout)
        LOG.debug(f'Starting service {service} resulted in status {status}')
        statuses += [status]
    return statuses


def stop_services(session, services, timeout=60):
    """
    Try stopping all services in given list.

    :param session: virtual machine session
    :type session: :py:class:`aexpect.ShellSession`
    :param services: list of services to modify
    :type services: [str]
    :param int timeout: timeout for each service to stop
    :returns: statuses for each modified service
    :rtype: [int]
    """
    statuses = []
    for service in services:
        status = session.cmd_status(f'service {service} status')
        if status == 0:      # is running --> stop
            status = session.cmd_status(f'service {service} stop', timeout)
        elif status == 3:    # is stopped --> ok
            LOG.debug(f'Service {service} stopped already')
        else:                # not sure, try stopping
            LOG.debug(f'Querying status for service {service} resulted in '
                      f'unexpected return code {status}. Try stopping it')
            status = session.cmd_status(f'service {service} stop', timeout)
        LOG.debug(f'Stopping service {service} resulted in status {status}')
        statuses += [status]
    return statuses


def restart_services(session, services, timeout=60):
    """
    Try restarting all services in given list.

    :param session: virtual machine session
    :type session: :py:class:`aexpect.ShellSession`
    :param services: list of services to modify
    :type services: [str]
    :param int timeout: timeout for each service to restart
    :returns: statuses for each modified service
    :rtype: [int]
    """
    statuses = []
    for service in services:
        status = session.cmd_status(f'service {service} status')
        if status == 0:      # is running --> restart
            status = session.cmd_status(f'service {service} restart', timeout)
        elif status == 3:    # is stopped --> ok
            LOG.debug(f'Service {service} stopped - starting')
            status = session.cmd_status(f'service {service} start', timeout)
        else:                # not sure, try restarting
            LOG.debug(f'Querying status for service {service} resulted in '
                      f'unexpected return code {status}. Try restarting it')
            status = session.cmd_status(f'service {service} restart', timeout)
        LOG.debug(f'Restarting service {service} resulted in status {status}')
        statuses += [status]
    return statuses
