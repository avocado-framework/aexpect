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
# Authors : Plamen Dimitrov <plamen.dimitrov@intra2net.com>

"""

SUMMARY
------------------------------------------------------
Share code between remote locations.


CONTENTS
------------------------------------------------------

Utility for sharing code among multiple remote platforms, executing parts of a
program on different locations (distributed programming) or writing controls
executed on another host (metaprogramming).

We use the following three options to communicate code among remote hosts:

1) Static (template) controls are the classical way we use to do this,
   namely by metaprogramming and setting attributes on a remote control
   file and then running the control on the remote location.

2) Generated controls / remote utilities are fully programmatically made
   but simple (a few lines long) ways to perform a single call to a module
   or utility installed on another machine (virtual or remote physical).

3) Remote objects are python code objects provided over the network that
   allow data persistence throughout multiple calls but are limited to
   serialization support. Ultimately, one could share greater functionality
   persistently over the network by extending the usual classes with ones
   that are more serialization compatible (using pyro proxy instances).


INTERFACE
------------------------------------------------------

"""

# disable import issues from optional dependencies or remote extra imports using
# pylint: disable=E0401,C0415,W0212
# disable too-many-* as we need them pylint: disable=R0912,R0913,R0914,R0915,C0302
# ..todo:: we could reduce the disabled issues after more significant refactoring

import os
import re
import logging
import inspect
import threading
import tempfile
import time
# NOTE: enable this before importing the Pyro backend in order to debug issues
# related to connectivity and perform further development on the this utility.
# os.environ["PYRO_LOGLEVEL"] = "DEBUG"
import Pyro4

try:
    from aexpect import remote
except ImportError:
    pass


#############################################
#   REMOTE UTILITIES / GENERATED CONTROLS   #
#############################################

#: default location for template control files
SRC_CONTROL_DIR = "."
#: default location for dumped control files
DUMP_CONTROL_DIR = "."
#: python binary to use for remote door running
REMOTE_PYTHON_BINARY = "/usr/bin/python3.7"
#: default path for remote utility python path
REMOTE_PYTHON_PATH = "/tmp/utils"


def _string_call(function, *args, **kwargs):
    arguments = ""
    for arg in args:
        if isinstance(arg, str):
            arguments = "%s'%s'" % (arguments, arg)
        else:
            arguments = "%s%s" % (arguments, arg)
        if len(kwargs) > 0 or arg != args[-1]:
            arguments = "%s%s" % (arguments, ", ")
    ordered_kwargs = list(kwargs.keys())
    for key in ordered_kwargs:
        if isinstance(kwargs[key], str):
            arguments = "%s%s='%s'" % (arguments, key, kwargs[key])
        else:
            arguments = "%s%s=%s" % (arguments, key, kwargs[key])
        if key != ordered_kwargs[-1]:
            arguments = "%s%s" % (arguments, ", ")
    return "result = %s(%s)\n" % (function, arguments)


def _string_generated_control(control_str):
    dump_dir = os.path.abspath(DUMP_CONTROL_DIR)
    new_fd, new_path = tempfile.mkstemp(suffix=".control", dir=dump_dir)
    logging.debug("Using %s for generated control file", new_path)
    with os.fdopen(new_fd, "wt") as new_f:
        new_f.write(control_str)
    return new_path


def run_remote_util(session, utility, function, *args, verify=None, detach=False, **kwargs):
    """
    Access a remote utility by generating a small control file to run remotely.

    :param session: session to use for running the remote utility
    :type session: RemoteSession object
    :param str utility: name of the remote utility to run
    :param str function: function of the remote utility to call
    :param verify: expected return argument from the call to use for
                   verification of the call execution
    :type verify: object or None
    :param bool detach: whether to detach from session (e.g. if running a
                        daemon or similar long-term utility)

    If the remote utility call is detached from the session, it will not wait
    for the session command to complete. Its further output (stdout and stderr)
    is channeled through the session and thus to the loggers provided by the
    session creators. The session will be spent and used entirely for the
    communication from the remote utility in order to avoid polluting its
    output from various detached processes. This is not a problem as multiple
    sessions can be easily created.
    """
    wrapper_control = "import logging\n"
    wrapper_control += "logging.basicConfig(level=logging.DEBUG, format='%(module)-16.16s '\n"
    wrapper_control += "                    'L%(lineno)-.4d %(levelname)-5.5s| %(message)s')\n"
    wrapper_control += "import sys\n"
    wrapper_control += "sys.path.append('%s')\n" % REMOTE_PYTHON_PATH
    wrapper_control += "import %s\n" % utility
    wrapper_control += _string_call(utility + "." + function, *args, **kwargs)
    wrapper_control += "assert result is %s\n" % verify if verify else ""

    control_path = _string_generated_control(wrapper_control)
    logging.debug("Accessing %s remote utility using the wrapper control %s",
                  utility, control_path)
    run_subcontrol(session, control_path, detach=detach)


def running_remotely(function):
    """
    Decorator for local functions to be run remotely.

    :param function: function to run remotely
    :type function: function
    :returns: same function converted to remote one
    :rtype: function

    Each function should contain a `_session` as a first argument
    and is expected to follow PEP8 standards.
    """
    def wrapper(session, *args, **kwargs):
        wrapper_control = "import logging\n"
        wrapper_control += "logging.basicConfig(level=logging.DEBUG, format='%(module)-16.16s '\n"  # pylint: disable=C0301
        wrapper_control += "                    'L%(lineno)-.4d %(levelname)-5.5s| %(message)s')\n"  # pylint: disable=C0301
        wrapper_control += "import sys\n"
        wrapper_control += "sys.path.append('%s')\n" % REMOTE_PYTHON_PATH
        # drop first argument and first line with the decorator since function already runs remotely
        wrapper_control += "\n" + "\n".join(inspect.getsource(function).split("\n")[1:]).replace("_session, ", "")  # pylint: disable=C0301
        wrapper_control += "\n" + _string_call(function.__name__, *args, **kwargs)
        logging.debug("Running remotey a function using the wrapper control %s",
                      wrapper_control)

        control_path = _string_generated_control(wrapper_control)
        run_subcontrol(session, control_path)

    return wrapper


##################################
#   STATIC (TEMPLATE) CONTROLS   #
##################################


def run_subcontrol(session, control_path, timeout=600, detach=False):
    """
    Get appropriate overwrite string in order to run a remote control.

    :param session: session to use for running the control
    :type session: RemoteSession object
    :param str control_path: path to the control on the host
    :param int timeout: timeout for the control to complete
    :param bool detach: whether to detach from session (e.g. if running a
                        daemon or similar long-term utility)
    """
    remote_control_path = os.path.join("/tmp", os.path.basename(control_path))
    remote.scp_to_remote(session.host, session.port, session.username, session.password,
                         control_path, remote_control_path)
    cmd = REMOTE_PYTHON_BINARY + " " + remote_control_path
    if detach:
        session.set_output_func(logging.info)
        session.set_output_params(())
        session.sendline(cmd)
    else:
        session.cmd(cmd, timeout=timeout, print_func=logging.info)


def prep_subcontrol(src_file, src_dir=None):
    """
    Produce a temporary control file from a source one.

    :param str src_file: source file for the control
    :param src_dir: source directory for the file if custom
    :type src_dir: str or None
    :returns: path of the copied temporary control
    :rtype: str

    If the `src_file` is a relative path, it will be searched for
    in a previously defined `SRC_CONTROL_DIR`. If it will be used
    as is if it is an absolute path.
    """
    if src_dir is None:
        src_dir = SRC_CONTROL_DIR

    if os.path.isabs(src_file):
        src_path = src_file
    else:
        src_path = os.path.join(os.path.abspath(src_dir), src_file)
    logging.debug("Using %s for original control path %s", src_path, src_file)

    dump_dir = os.path.abspath(DUMP_CONTROL_DIR)
    new_fd, new_path = tempfile.mkstemp(suffix=".control", dir=dump_dir)
    logging.debug("Using %s for modified control path %s", new_path, src_file)

    with open(src_path, "rt") as src_f:
        with os.fdopen(new_fd, "wt") as new_f:
            new_f.write(src_f.read())

    return new_path


def set_subcontrol(function):
    """
    Decorator for subcontrol code modification.

    :param function: function to set subcontrol variable
    :type function: function
    :returns: same function with control file handling
    :rtype: function
    """
    def wrapper(*args, **kwargs):
        control_path = args[0]
        control = prep_subcontrol(control_path)
        with open(control, "rt") as handle:
            subcontrol = handle.read()
        modcontrol = function(subcontrol, *args[1:], **kwargs)
        with open(control, "wt") as handle:
            handle.write(modcontrol)
        return control
    return wrapper


@set_subcontrol
def set_subcontrol_parameter(subcontrol, parameter, value):
    """
    Replace a single variable at the beginning of a remote control file.

    :param str subcontrol: path to the original control
    :param str parameter: control variable name
    :param str value: control variable value
    :returns: path to the modified control
    :rtype: str

    .. warning:: The `subcontrol` parameter is control path externally but
        control content internally after decoration.
    """
    return re.sub("%s[ \t\v]*=[ \t\v]*.*" % parameter.upper(),
                  "%s = %s" % (parameter.upper(), repr(value)),
                  subcontrol, count=1)


@set_subcontrol
def set_subcontrol_parameter_list(subcontrol, list_name, value):
    """
    Replace a list at the beginning of a remote control file.

    :param str subcontrol: path to the original control
    :param str list_name: control list name
    :param value: control list value
    :type value: [any]
    :returns: path to the modified control
    :rtype: str

    .. warning:: The `subcontrol` parameter is control path externally but
        control content internally after decoration.
    """
    return re.sub(r"%s[ \t\v]*=[ \t\v]*\[.*\]" % list_name.upper(),
                  "%s = %s" % (list_name.upper(), repr(value)),
                  subcontrol, count=1)


@set_subcontrol
def set_subcontrol_parameter_dict(subcontrol, dict_name, value):
    """
    Replace a dictionary at the beginning of a remote control file.

    :param str subcontrol: path to the original control
    :param str dict_name: control dictionary name
    :param value: control dictionary value
    :type value: {any, any}
    :returns: path to the modified control
    :rtype: str

    .. warning:: The `subcontrol` parameter is control path externally but
        control content internally after decoration.
    """
    return re.sub(r"%s[ \t\v]*=[ \t\v]*\{.*\}" % dict_name.upper(),
                  "%s = %s" % (dict_name.upper(), repr(value)),
                  subcontrol, count=1)


@set_subcontrol
def set_subcontrol_parameter_object(subcontrol, value):
    """
    Prepare a URI to remote params for the remote control file.

    :param str subcontrol: path to the original control
    :param value: control parameters value
    :type value: Params object
    :returns: path to the modified control
    :rtype: str
    :raises: :py:class:`ValueError` if the host IP couldn't be obtained to share the parameters

    .. warning:: The `subcontrol` parameter is control path externally but
        control content internally after decoration.
    """
    params = value
    host_ip = None
    nics = params.objects("nics")
    for nic in nics:
        nic_params = params.object_params(nic)
        if nic_params.get("host") is not None:
            host_ip = nic_params.get("host")
            break
    if host_ip is None:
        raise ValueError("No IP of the host machine was found")

    logging.info("Sharing the test parameters over the network")
    Pyro4.config.AUTOPROXY = False
    Pyro4.config.REQUIRE_EXPOSE = False
    try:
        pyro_daemon = Pyro4.Daemon(host=host_ip, port=1437)
        logging.debug("Pyro4 daemon started successfully")
        uri = pyro_daemon.register(params)
        pyrod_running = False
    # address already in use OS error
    except OSError:
        pyro_daemon = Pyro4.Proxy("PYRO:" + Pyro4.constants.DAEMON_NAME +
                                  "@" + host_ip + ":1437")
        pyro_daemon.ping()
        registered = pyro_daemon.registered()
        logging.debug("Pyro4 daemon already started, available objects: %s",
                      registered)
        assert len(registered) == 2
        assert registered[0] == "Pyro.Daemon"
        uri = "PYRO:" + registered[1] + "@" + host_ip + ":1437"
        pyrod_running = True

    if not pyrod_running:
        logging.info("Starting the parameters provider for the remote host")
        loop = DaemonLoop(pyro_daemon)
        loop.start()

    logging.debug("Pouring the params object to the host via uri %s", uri)
    subcontrol = re.sub("URI[ \t\v]*=[ \t\v]*\".*\"", "URI = \"%s\"" % uri,
                        subcontrol, count=1)

    return subcontrol


######################
#   REMOTE OBJECTS   #
######################

class DaemonLoop(threading.Thread):
    """Loop thread for sharing remote objects."""

    def __init__(self, pyro_daemon):
        """
        Contruct the Pyro daemon thread.

        :param pyro_daemon: daemon for the remote python objects
        :type pyro_daemon: Pyro4.Daemon object
        """
        threading.Thread.__init__(self)
        self.pyro_daemon = pyro_daemon
        self.daemon = True     # make this a Daemon Thread

    def run(self):
        """Run the Pyro4 daemon thread."""
        self.pyro_daemon.requestLoop()


def get_remote_object(object_name, session=None, host="localhost", port=9090):
    """
    Get a data object (visual or other) executing remotely or
    share one if none is available, generating control files along
    the way.

    :param str object_name: name of the object to connect to
    :param session: connection session if the object will be shared from the
                    other side (devoted to communication with the object)
    :type session: RemoteSession or None
    :param str host: ip address of the local sharing server
    :param int port: port of the local name server
    :returns: proxy version of the remote object
    :rtype: Pyro4.Proxy

    To consider whitelisting of shareable functions/classes you have to share
    local objects separately with more manual configuration on the sharing
    process. This automatic two-way door opening considers simpler cases.

    This method does not rely on any static (template) controls in order to
    work because the remote door takes care to reach back the local one.
    """
    try:
        remote_object = Pyro4.Proxy("PYRONAME:" + object_name + "@" + host + ":" + str(port))
        remote_object._pyroBind()
    except Pyro4.errors.PyroError:
        if not session:
            raise

        # if there is no door on the other side, open one
        remote.scp_to_remote(session.host, session.port, session.username, session.password,
                             os.path.abspath(__file__), REMOTE_PYTHON_PATH)
        run_remote_util(session, "remote_door", "share_local_object",
                        object_name, host=host, port=port, detach=True)
        output, attempts = "", 10
        for _ in range(attempts):
            output = session.get_output()
            if "ready" in output:
                break
            time.sleep(1)
        else:
            raise OSError("Local object sharing failed:\n%s" % output)
        logging.debug("Local object sharing output:\n%s", output)
        logging.getLogger("Pyro4").setLevel(10)

        remote_object = Pyro4.Proxy("PYRONAME:" + object_name + "@" + host + ":" + str(port))
        remote_object._pyroBind()
    return remote_object


def get_remote_objects(session=None, host="localhost", port=0):
    """
    Get all data objects (full python access) executing remotely or share
    them if they are not available, generating control files along the way.

    :param session: connection session if the object will be shared
    :type session: RemoteSession or None
    :param str host: ip address of the local sharing server
    :param int port: port of the local sharing server
    :returns: proxy version of the remote objects
    :rtype: Pyro4.Proxy

    This method does not rely on any static (template) controls in order to
    work because the remote door takes care to reach back the local one.
    """
    Pyro4.config.SERIALIZER = "pickle"
    Pyro4.config.PICKLE_PROTOCOL_VERSION = 3
    from Pyro4.utils import flame

    try:
        remote_objects = flame.connect(host + ":" + str(port))
        remote_objects._pyroBind()
    except Pyro4.errors.PyroError:
        if not session:
            raise

        # if there is no door on the other side, open one
        remote.scp_to_remote(session.host, session.port, session.username, session.password,
                             os.path.abspath(__file__), REMOTE_PYTHON_PATH)
        run_remote_util(session, "remote_door", "share_local_objects",
                        wait=True, host=host, port=port, detach=True)
        for _ in range(10):
            if "ready" in session.cmd("cat /tmp/control.log"):
                break
            time.sleep(1)
        else:
            raise OSError("Local objects sharing failed:\n%s" % session.cmd("cat /tmp/control.log"))
        logging.debug("Local objects sharing output:\n%s", session.cmd("cat /tmp/control.log"))

        remote_objects = flame.connect(host + ":" + str(port))
        remote_objects._pyroBind()
    return remote_objects


def share_local_object(object_name, whitelist=None, host="localhost", port=9090):
    """
    Share a local object of the given name over the network.

    :param str object_name: name of the local object
    :param whitelist: shared functions/classes of the local object as tuple
                      pairs (module, function) or (module, class); whitelist
                      all (do not filter) if None or empty
    :type whitelist: [(str,str)] or None
    :param str host: ip address of the local name server
    :param port: port of the local sharing server
    :type port: int or str

    This function shares a custom object with whitelisted attributes through a
    custom implementation. It is more secure but more limited as functionality
    since it requires serialization extensions.
    """
    Pyro4.config.AUTOPROXY = True
    Pyro4.config.REQUIRE_EXPOSE = False
    port = int(port) if isinstance(port, str) else port

    # pyro daemon
    try:
        pyro_daemon = Pyro4.Daemon(host=host)
        logging.debug("Pyro4 daemon started successfully")
        pyrod_running = False
    # address already in use OS error
    except OSError:
        pyro_daemon = Pyro4.Proxy("PYRO:" + Pyro4.constants.DAEMON_NAME + "@" + host)
        pyro_daemon.ping()
        logging.debug("Pyro4 daemon already started, available objects: %s",
                      pyro_daemon.registered())
        pyrod_running = True

    # name server
    try:
        ns_server = Pyro4.locateNS(host=host, port=port)
        logging.debug("Pyro4 name server already started")
        nsd_running = True
    # network unreachable and failed to locate the nameserver error
    except (OSError, Pyro4.errors.NamingError):
        from Pyro4 import naming
        ns_uri, ns_daemon, _bc_server = naming.startNS(host=host, port=port)
        ns_server = Pyro4.Proxy(ns_uri)
        logging.debug("Pyro4 name server started successfully with URI %s", ns_uri)
        nsd_running = False

    # main retrieval of the local object
    import importlib
    module = importlib.import_module(object_name)
    def proxymethod(fun):
        """Decorator to autoproxy all callables."""
        def wrapper(*args, **kwargs):
            rarg = fun(*args, **kwargs)
            def proxify_type(rarg):
                if rarg is None or type(rarg) in (bool, int, float, str):  # pylint: disable=C0123
                    return rarg
                if isinstance(rarg, tuple):
                    return tuple(proxify_type(e) for e in rarg)
                if isinstance(rarg, list):
                    return [proxify_type(e) for e in rarg]
                if isinstance(rarg, dict):
                    return {proxify_type(k): proxify_type(v) for (k, v) in rarg.items()}
                pyro_daemon.register(rarg)
                return rarg
            import types
            if isinstance(rarg, types.GeneratorType):
                def generator_wrapper():
                    for nxt in rarg:
                        yield proxify_type(nxt)
                return generator_wrapper()
            return proxify_type(rarg)
        return wrapper
    class ModuleObject:  # pylint: disable=R0903
        """Module wrapped for transferability."""
    for fname, fobj in inspect.getmembers(module, inspect.isfunction):
        if not whitelist or (object_name, fname) in whitelist:
            setattr(ModuleObject, fname, staticmethod(proxymethod(fobj)))
    for cname, cobj in inspect.getmembers(module, inspect.isclass):
        if not whitelist or (object_name, cname) in whitelist:
            setattr(ModuleObject, cname, staticmethod(proxymethod(cobj)))
    local_object = ModuleObject()

    # we should register to the pyro daemon before entering its loop
    uri = pyro_daemon.register(local_object)
    if not pyrod_running:
        loop = DaemonLoop(pyro_daemon)
        loop.start()
    if not nsd_running:
        loop = DaemonLoop(ns_daemon)
        loop.start()
    # we should register to the name server after entering its loop
    ns_server.register(object_name, uri)

    logging.info("Local object '%s' sharing - ready", object_name)
    loop.join()


def share_local_objects(wait=False, host="localhost", port=0):
    """
    Share all local objects of the given name over the network.

    :param bool wait: whether to wait for a loop exit (e.g. if not running
                      this function's code locally)
    :param str host: ip address of the local sharing server
    :param int port: port of the local sharing server

    This function shares all possible python code (dangerous) and not
    just a custom object with whitelisted attributes (secure).
    """
    Pyro4.config.FLAME_ENABLED = True
    Pyro4.config.SERIALIZER = "pickle"
    Pyro4.config.SERIALIZERS_ACCEPTED = {"pickle"}

    # pyro daemon
    pyro_daemon = Pyro4.Daemon(host=host, port=port)
    logging.debug("Pyro4 daemon started successfully")

    # main retrieval of the local objects
    from Pyro4.utils import flame
    _uri = flame.start(pyro_daemon)  # lgtm [py/unused-local-variable]

    # request loop
    loop = DaemonLoop(pyro_daemon)
    loop.start()
    if wait:
        loop.join()


def share_remote_objects(session, control_path, host="localhost", port=9090,
                         os_type="windows", extra_params=None):
    """
    Create and share remote objects from a remote location over the network.

    :param session: remote session to the platform
    :type session: RemoteSession
    :param str control_path: path to the control on the host
    :param str host: ip address of the remote sharing server
    :param int port: port of the remote sharing server
    :param str os_type: OS type of the session, either "linux" or "windows"
    :param extra_params: extra parameters to pass to the remote object sharing
                         control file (similarly to subcontrol setting above),
                         with keys usually prepended with "ro_" prefix
    :type extra_params: {str, str}
    :raises: :py:class:`RuntimeError` if the object server failed to start

    In comparison to :py:func:`share_local_object`, this function fires up a
    name server from a second spawned session (not remote util call) and uses
    static (template) control as a remote object server which has to be
    preprogrammed but thus also customized (e.g. sharing multiple objects).

    In comparison to :py:func:`share_local_objects`, this function is not
    an internal implementation sharing everything on the other side but only
    what is dicated by the remote object server module and thus its creator.

    .. note:: Created and works specifically for Windows and Linux.
    """
    logging.info("Sharing the remote objects over the network")

    # setup remote objects server
    logging.info("Starting nameserver for the remote objects")
    cmd = "python -m Pyro4.naming -n %s -p %s" % (host, port)
    session.cmd("START " + cmd if os_type == "windows" else cmd + " &")

    logging.info("Starting the server daemon for the remote objects")
    # ..todo:: later on we can dynamize this further depending on usage of this alternative function
    transfer_client = "rss" if os_type == "windows" else "scp"
    transfer_port = 10023 if os_type == "windows" else 22
    local_path = set_subcontrol_parameter(control_path, "ro_server_ip", host)
    # optional parameters (set only if present and/or available)
    for key in extra_params.keys():
        local_path = set_subcontrol_parameter(local_path, key, extra_params[key])
    # NOTE: since we are creating the path in Linux but use it in Windows,
    # we replace some of the backslashes
    if os_type == "windows":
        remote_path = os.path.join(REMOTE_PYTHON_PATH,
                                   os.path.basename(control_path)).replace("/", "\\")
    remote.copy_files_to(session.host, transfer_client,
                         session.username, session.password, transfer_port,
                         local_path, remote_path, timeout=10)
    middleware_session = remote.wait_for_login(session.client, session.host, session.port,
                                               session.username, session.password,
                                               session.prompt, session.linesep)
    middleware_session.set_status_test_command(session.status_test_command)
    middleware_session.set_output_func(logging.info)
    middleware_session.set_output_params(())
    middleware_session.sendline("python %s" % remote_path)

    # HACK: not the best way to do this but the stderr and stdout are mixed and we
    # cannot get the exit status so we rely on the mixed stdout/stderr output
    output, attempts = "", 30
    while "Remote objects shared over the network" not in output:
        output = middleware_session.get_output()
        logging.debug(output)
        if attempts <= 0 or "Traceback (most recent call last):" in output:
            raise RuntimeError("The remote objects server failed to start")
        attempts -= 1
        time.sleep(1)

    Pyro4.config.NS_HOST = host
    logging.getLogger("Pyro4").setLevel(10)


def import_remote_exceptions(exceptions):
    """
    Make serializable all remote custom exceptions.

    :param exceptions: module dot accessible exception names
    :type exceptions: [str]

    .. note:: This wouldn't be needed if we were using the Pickle serializer but its
        security problems at the moment made us prefer the serpent serializer paying
        for it with some extra setup steps and this method.
    """
    # ..todo:: need a more dynamic way of determining the exceptions like examining
    # the errors modules and even extracting the exception classes from there
    class RemoteCustomException(Exception):
        """Standard class to instantiate during remote expection deserialization."""
    def recreate_exception(class_name, class_dict):
        logging.debug("Remote exception %s data: %s", class_name, class_dict)
        exceptiontype = RemoteCustomException
        exception = exceptiontype(*class_dict["args"])
        # in the case of non-custom exceptions the class is properly restored
        exception.__customclass__ = class_dict.get("__class__", "")

        if "attributes" in class_dict.keys():
            # restore custom attributes on the exception object
            for attr, value in class_dict["attributes"].items():
                setattr(exception, attr, value)
        return exception

    for exception in exceptions:
        Pyro4.util.SerializerBase.register_dict_to_class(exception, recreate_exception)
