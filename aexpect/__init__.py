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

from .exceptions import ExpectError
from .exceptions import ExpectProcessTerminatedError
from .exceptions import ExpectTimeoutError
from .exceptions import ShellCmdError
from .exceptions import ShellError
from .exceptions import ShellProcessTerminatedError
from .exceptions import ShellStatusError
from .exceptions import ShellTimeoutError

from .client import Spawn
from .client import Tail
from .client import Expect
from .client import ShellSession
from .client import kill_tail_threads
from .client import run_tail
from .client import run_bg
from .client import run_fg

from . import remote
from . import rss_client
