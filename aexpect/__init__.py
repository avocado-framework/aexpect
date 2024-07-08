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

"""
Aexpect module, see help('aexpect.client') to get info about the main
entry-points.
"""

from . import remote, rss_client
from .client import (
    Expect,
    ShellSession,
    Spawn,
    Tail,
    kill_tail_threads,
    run_bg,
    run_fg,
    run_tail,
)
from .exceptions import (
    ExpectError,
    ExpectProcessTerminatedError,
    ExpectTimeoutError,
    ShellCmdError,
    ShellError,
    ShellProcessTerminatedError,
    ShellStatusError,
    ShellTimeoutError,
)
