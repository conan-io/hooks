# coding=utf-8

from contextlib import contextmanager

import sys
from conans import __version__ as conan_version
try:
    from conans.client.command import Conan, CommandOutputer, Command
except ImportError:
    from conans.cli.api.conan_api import ConanAPIV2
    from conans.cli.cli import Cli
    v2 = True

from conans.model.version import Version


@contextmanager
def conan_command(output_stream):
    if v2:
        conan_api = ConanAPIV2()
        cli = Cli(conan_api)
        yield cli
        return

    # This snippet reproduces code from conans.client.command.main, we cannot directly
    # use it because in case of error it is exiting the python interpreter :/
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = output_stream, output_stream
    conan_api, cache, user_io = Conan.factory()
    if Version(conan_version) >= "1.16":
        cmd = Command(conan_api)
    else:
        user_io.out._stream = output_stream
        outputer = CommandOutputer(user_io, cache)
        cmd = Command(conan_api, cache, user_io, outputer)
    try:
        yield cmd
    finally:
        if Version(conan_version) < "1.13":
            conan_api._remote_manager._auth_manager._localdb.connection.close()  # Close sqlite3
        sys.stdout, sys.stderr = old_stdout, old_stderr
