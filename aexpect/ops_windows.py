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
# Authors : Samir Aguiar <samir.aguiar@intra2net.com>

"""
A list of frequent operations performed through remote sessions to windows platforms.

PowerShell:
A section for PowerShell-based commands and scripts.

registry ops:
Registry key manipulation.

filesystem ops:
Operations concerning files on Windows e.g. file paths and directories.

process ops:
Operations concerning process management e.g. start, kill, and run as.

network ops:
Network configuration and downloads.
"""

import re
import uuid
import logging
from textwrap import dedent
from base64 import b64encode
from enum import Enum, auto

# avocado imports
from aexpect.exceptions import ShellError, ShellProcessTerminatedError

LOG = logging.getLogger(__name__)


###############################################################################
# PowerShell
###############################################################################


def ps_cmd(session, script, timeout=60):
    """
    Run one or multiple PowerShell commands.

    :param session: session of the Windows guest
    :type session: :py:class:`aexpect.client.RemoteSession`
    :param str script: one or multiple PowerShell commands
    :param int timeout: seconds to wait for the command to complete
    :returns: the output of the command
    :rtype: str

    The string with commands is encoded in base64, which means that
    a whole multiline script can be passed without problems.

    This function was slightly based on a similar function from `pywinrm`.
    """
    def nicely_log_str(header, string):
        LOG.info(header)
        LOG.info("-" * len(header))
        for line in string.splitlines():
            LOG.info(line)
        LOG.info("\n")

    nicely_log_str("Running PowerShell script", dedent(script))
    # must use utf16 little endian on Windows
    encoded_cmd = b64encode(script.encode("utf_16_le")).decode("ascii")
    try:
        output = session.cmd(f"powershell -NoLogo -NonInteractive -OutputFormat text "
                             f"-ExecutionPolicy Bypass -EncodedCommand {encoded_cmd}",
                             timeout=timeout)

        # there was an error but the exit code was still zero
        if output.startswith("#< CLIXML") and "<S S=\"Error\">" in output:
            raise ShellError(script, output)

        # TODO: PowerShell sometimes ignores the -OutputFormat and outputs
        # as XML. This has been fixed on newer versions but we have yet to update:
        # https://github.com/PowerShell/PowerShell/pull/8115
        if output.startswith("#< CLIXML") and "<Objs Version" in output:
            output = "\n".join(output.splitlines()[1:-1])

        nicely_log_str("PowerShell script output", output)
        return output.strip()
    except ShellError as error:
        # `cmd` is encoded here, replace before raising
        error.cmd = script
        error.output = _clean_error_message(error.output)
        nicely_log_str("An error occurred while running the script", error.output)
        raise


def ps_file(session, filename, timeout=60):
    """
    Execute a PowerShell script from a file.

    :param session: session of the Windows guest
    :type session: :py:class:`aexpect.client.RemoteSession`
    :param str filename: path to the file in the guest VM
    :param int timeout: seconds to wait for the script to run
    :returns: the output of the command
    :rtype: str
    """
    cmd = f"powershell -ExecutionPolicy RemoteSigned -File \"{filename}\""
    LOG.info("Executing PowerShell file with `%s`", cmd)
    return session.cmd(cmd, timeout=timeout)


def _clean_error_message(message):
    """
    Convert a Powershell CLIXML message to a human readable string.

    :param str message: XML message
    :returns: human readable string
    :rtype: str
    """
    # make sure we have a CLIXML message
    if not message.startswith("#< CLIXML\n"):
        return message

    output = []
    # the strings are between <S S="Error">...</S> tags
    for msgstr in message.split("<S S=\"Error\">"):
        if not msgstr.endswith("</S>"):
            continue
        msgstr = re.sub(r"</S>$", "", msgstr).replace("_x000D__x000A_", "")
        output.append(msgstr)
    # return the original message if anything failed
    return "\n".join(output) if output else message


###############################################################################
# registry ops
###############################################################################


class RegistryKeyType(Enum):
    """Enum representing possible values of registry keys."""

    # Binary data in any form.
    BINARY = auto()
    # A 32-bit number.
    DWORD = auto()
    # A 32-bit number in little-endian format. Windows is designed to run on
    # little-endian computer architectures. Therefore, this value is defined
    # as REG_DWORD in the Windows header files.
    DWORD_LITTLE_ENDIAN = auto()
    # A 32-bit number in big-endian format.
    DWORD_BIG_ENDIAN = auto()
    # A null-terminated string that contains unexpanded references to
    # environment variables (for example, "%PATH%"). It will be a Unicode or
    # ANSI string depending on whether you use the Unicode or ANSI functions.
    EXPAND_SZ = auto()
    # A null-terminated Unicode string that contains the target path of a
    # symbolic link that was created by calling the RegCreateKeyEx function
    # with REG_OPTION_CREATE_LINK.
    LINK = auto()
    # A sequence of null-terminated strings, terminated by an empty string (\0).
    # The following is an example: String1\0String2\0String3\0LastString\0\0
    # The first \0 terminates the first string, the second to the last \0
    # terminates the last string, and the final \0 terminates the sequence.
    # Note that the final terminator must be factored into the length of the string.
    MULTI_SZ = auto()
    # No defined value type.
    NONE = auto()
    # A 64-bit number.
    QWORD = auto()
    # A 64-bit number in little-endian format. Windows is designed to run on
    # little-endian computer architectures. Therefore, this value is defined
    # as REG_QWORD in the Windows header files.
    QWORD_LITTLE_ENDIAN = auto()
    # A null-terminated string. This will be either a Unicode or an ANSI string,
    # depending on whether you use the Unicode or ANSI functions.
    SZ = auto()

    def __init__(self, *_):
        """Initialize this instance with correct values."""
        super().__init__()
        # replace values assigned by "auto" with the correct types
        self._value_ = f"REG_{self.name}"


def query_registry(session, key_name, value_name):
    """
    Query registry keys.

    :param session: session of the Windows guest
    :type session: :py:class:`aexpect.client.RemoteSession`
    :param str key_name: full path of the subkey
    :param str value_name: registry value name that is to be queried
    :returns: value of the corresponding sub key and value name or None if not found
    :rtype: str or None
    """
    key_types = ["REG_SZ", "REG_MULTI_SZ", "REG_EXPAND_SZ",
                 "REG_DWORD", "REG_BINARY", "REG_NONE"]

    out = session.cmd_output(f"reg query \"{key_name}\" /v {value_name}").strip()
    LOG.info("Reg query for key %s and value %s: %s", key_name, value_name, out)
    for k in key_types:
        parts = out.split(k)
        if len(parts) > 1:
            return parts[-1].strip()

    return None


def add_reg_key(session, path, name, value, key_type, force=True):   # pylint: disable=R0913
    """
    Wrapper around the reg add command.

    :param str path: path where the new registry key will be created
    :param str name: name of the key to create
    :param str value: value of the key
    :param key_type: type of the key to create
    :type key_type: :py:class:`RegistryKeyType`
    :returns: the output of the reg add command
    :rtype: str
    """
    if not isinstance(key_type, RegistryKeyType):
        raise TypeError(f"{key_type} must be instance of RegistryKeyType")

    cmd = f"reg add \"{path}\" /v {name} /d {value} /t {key_type.value}"
    if force:
        cmd += " /f"

    return session.cmd(cmd)


def refresh_path_variable(session):
    """
    Refresh the PATH variable in the current session.

    :param session: session of the Windows guest
    :type session: :py:class:`aexpect.client.RemoteSession`
    """
    env_key = r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
    # system path
    syspath = query_registry(session, env_key, "Path")
    # user path
    userpath = query_registry(session, r"HKCU\Environment", "Path")
    LOG.info("Setting the PATH in the Windows session to %s;%s", syspath, userpath)
    session.cmd(f"set PATH={syspath};{userpath}")


###############################################################################
# filesystem ops
###############################################################################


def path_exists(session, path):
    """
    Check whether a file or a folder exists.

    :param session: session of the Windows guest
    :type session: :py:class:`aexpect.client.RemoteSession`
    :param str path: path to the file or folder
    :returns: whether the given path exists
    :rtype: str
    """
    output = session.cmd_output(f"if exist \"{path}\" echo yes")
    return output.strip() == "yes"


def hash_file(session, filename):
    """
    Calculate the md5 hash value of given file.

    :param session: session of the Windows guest
    :type session: :py:class:`aexpect.client.RemoteSession`
    :param str filename: full path of file that should be hashed
    :returns: hash value
    :rtype: str
    """
    output = session.cmd(f"certutil -hashfile \"{filename}\" MD5")
    LOG.debug("certutil output for %s is %s", filename, output)
    hash_value = output.splitlines()[1]
    LOG.debug("Hash value is %s", hash_value)
    return hash_value


def mkdir(session, path, exist_ok=True):
    """
    Create a folder.

    :param session: session of the Windows guest
    :type session: :py:class:`aexpect.client.RemoteSession`
    :param str path: path to the folder create
    :param bool exist_ok: whether to ignore if the destination exists
    :raises: :py:class:`aexpect.exceptions.ShellCmdError` when the folder
             exists and exist_ok is False
    """
    if exist_ok:
        cmd = f"if not exist \"{path}\" mkdir \"{path}\""
    else:
        cmd = f"mkdir \"{path}\""
    session.cmd(cmd)


def touch(session, path):
    """
    Create a file with no content.

    :param session: session of the Windows guest
    :type session: :py:class:`aexpect.client.RemoteSession`
    :param str path: path to the file create
    :returns: path of the file created
    :rtype: str
    """
    session.cmd(f"type nul > \"{path}\"")
    return path


def cat(session, filename):
    """
    Read a file.

    :param session: session of the Windows guest
    :type session: :py:class:`aexpect.client.RemoteSession`
    :param str filename: full path of file to read
    :returns: contents of the file
    :rtype: str
    """
    return session.cmd_output(f"type {filename}")


def remove(session, path, recurse=False):
    """
    Remove a file or a directory.

    :param session: session of the Windows guest
    :type session: :py:class:`aexpect.client.RemoteSession`
    :param str filename: path of the directory or file to remove
    :param bool recurse: whether to remove all files under the directory
    """
    if recurse:
        session.cmd(f"rmdir /s /q {path}")
    else:
        session.cmd(f"del /f /q {path}")


def tempfile(session, local=True):
    """
    Create a temporary file in a safe way through a session.

    :param session: session to run the command on
    :type session: ShellSession
    :param bool local: whether the temporary file should be created in the
                       user's TEMP folder or in a folder accessible by
                       other users in the system
    :returns: name of temporary file
    :rtype: str
    :raises: :py:class:`RuntimeError` if the operation fails
    """
    if local:
        return ps_cmd(session, "(New-TemporaryFile).FullName")

    # make sure it exists (it not always does on Windows 10)
    mkdir(session, "C:\\Temp")

    # Although the generated UUID can exist in the destination,
    # this should be rare and work for 99% of the cases.
    tmp_file = f"C:\\Temp\\{uuid.uuid4()}.tmp"
    touch(session, tmp_file)
    return tmp_file


###############################################################################
# process ops
###############################################################################


def run_as(session, user, password, command, timeout=60, background=False):   # pylint: disable=R0913
    """
    Run a command as different user.

    :param session: session of the Windows guest
    :type session: :py:class:`aexpect.client.RemoteSession`
    :param str user: name of the user under which to run the command
    :param str password: password of the user
    :param str command: command to run
    :param int timeout: amount of time to wait for the command to finish
    :param bool background: whether this is a background command that should
                            not be awaited for completion
    :returns: the output of the command or None if background is True
    :rtype: str or None
    """
    LOG.info("Running `%s` as user `%s`", command, user)

    def _run_as(cmd_to_run):
        LOG.debug("Running command `%s`", cmd_to_run)
        session.sendline(cmd_to_run)
        LOG.debug("Entering password `%s`", password)
        session.read_until_output_matches(["Geben Sie das Kennwort"])
        session.sendline(password)

    if background is True:
        _run_as(f"runas /user:{user} \"{command}\"")
        return None

    outfile = tempfile(session, local=False)
    # runas produces no output, so we add a redirection to the inner command
    cmd = f"runas /user:{user} \"cmd.exe /c {command} > {outfile}\""
    _run_as(cmd)
    LOG.debug("Waiting %s seconds for the command to finish", timeout)
    # no need to capture anything, we redirected the output
    session.read_up_to_prompt(timeout=timeout)

    # after reading the output from the file we can remove it
    output = cat(session, outfile).strip()
    remove(session, outfile)
    return output


def kill_program(session, program, kill_children=True):
    """
    Forcefully kill a program.

    :param session: session of the Windows guest
    :type session: :py:class:`aexpect.client.RemoteSession`
    :param str program: name of the program to kill
    :param bool kill_children: whether to kill child processes
    """
    cmd = f"taskkill /f /im \"{program}\""
    if kill_children:
        cmd += " /t"
    session.cmd(cmd)


def wait_process_end(session, process, timeout=30):
    """
    Wait until a process has fully ended using PowerShell.

    :param session: session of the Windows guest
    :type session: :py:class:`aexpect.client.RemoteSession`
    :param str process: name of the process to track
    :param int timeout: timeout to wait before giving up
    :raises: :py:class:`TimeoutError` if an error occurred
    :raises: :py:class:`RuntimeError` if an error occurred
    """
    LOG.info("Waiting for process %s to end using PowerShell", process)

    # give some extra timeout to wait for PowerShell to return
    ps_cmd(session, f"Wait-Process -Name {process} -Timeout {timeout}",
           timeout=timeout+5)


def kill_session(session):
    """
    Kill the rss process responsible for a session.

    :param session: session of the Windows guest
    :type session: :py:class:`aexpect.client.RemoteSession`
    """
    LOG.info("Killing session for the user %s", session.username)
    cmd = "(Get-WmiObject Win32_Process -Filter ProcessId=$PID).ParentProcessId"
    cmd_pid = ps_cmd(session, cmd)
    LOG.debug("Got cmd.exe with PID %s", cmd_pid)

    rss = f"(Get-WmiObject Win32_Process -Filter ProcessId={cmd_pid}).ParentProcessId"
    rss_pid = ps_cmd(session, rss)
    LOG.debug("Got rss.exe with PID %s", rss_pid)

    session.sendline(f"taskkill /F /PID {rss_pid}")
    # read everything left to read
    session.read_nonblocking(internal_timeout=0, timeout=3)
    # make sure we got the right session (session.is_responsive() does not always work here)
    try:
        session.cmd("whoami", timeout=5)
    except ShellProcessTerminatedError:
        # session ended correctly
        pass
    else:
        raise ProcessLookupError(f"Could not kill rss.exe for user {session.username}")

    session.close()
    LOG.info("Session successfully killed")


###############################################################################
# network ops
###############################################################################


def find_unused_port(session, start_port=10024):
    """
    Find an unused port in the Windows VM.

    :param session: session of the Windows guest
    :type session: :py:class:`aexpect.client.RemoteSession`
    :param int start_port: start looking from this port onwards
    :returns: unused port that was found
    :rtype: int
    """
    output = ps_cmd(session, f"""
        $port = {start_port}
        while($true) {{
            try {{
                $listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Any, $port)
                $listener.Start()
                Write-Host "Found unused port $port."
                $listener.Stop()
                break;
            }}
            catch [System.Net.Sockets.SocketException] {{
                Write-Host "Unable to open socket on port $port."
                $port = $port + 1
            }}
        }}

        Write-Host "::unused=$port"
    """)
    port = re.search(r"::unused=(\d+)", output).group(1)
    return int(port)


def curl(session, url, proxy_address=None, proxy_port=None, insecure=False):
    """
    Simple curl-like function that uses PowerShell.

    :param session: session of the Windows guest
    :type session: :py:class:`aexpect.client.RemoteSession`
    :param str proxy_address: optional address of a proxy to use
    :param str proxy_port: port in the proxy server
    :param bool insecure: allow insecure server connections when using SSL
    :returns: status and output of the web request
    :rtype: (int, str)
    """
    # extra indentation is not allowed within PS heredocs
    skip_ssl_template = dedent("""\
        Add-Type -Language CSharp @"
        namespace System.Net
        {
            public static class Util
            {
                public static void Init()
                {
                    ServicePointManager.ServerCertificateValidationCallback = null;
                    ServicePointManager.ServerCertificateValidationCallback += (sender, cert, chain, errs) => true;
                    ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls | SecurityProtocolType.Tls11 | SecurityProtocolType.Tls12;
                }
            }
        }
        "@;
        [System.Net.Util]::Init()""")

    # TODO: WebRequest (wrapper on top of System.Net.WebClient) is painfully slow
    # for some reason compared to the 3rd-party curl.exe tool, but let's use it for now.
    webrequest_cmd = f"Invoke-WebRequest -Uri \"{url}\""
    if proxy_address is not None:
        # the session user must have access to the proxy (otherwise use -ProxyCredential)
        webrequest_cmd += f" -Proxy http://{proxy_address}:{proxy_port} -ProxyUseDefaultCredentials"

    output = ps_cmd(session, f"""
        {skip_ssl_template if insecure else ''}
        $ProgressPreference = 'SilentlyContinue'
        $result = {webrequest_cmd}
        Write-Output $result.StatusCode
        Write-Output $result.Content
    """)

    LOG.debug("Powershell request produced output:\n'%s'", output)
    try:
        status, content = output.split("\n", 1)
    except ValueError as error:
        raise RuntimeError("The request failed -- invalid output structure") from error
    return int(status), content
