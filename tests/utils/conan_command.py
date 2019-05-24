# coding=utf-8

from contextlib import contextmanager

from conans import __version__ as conan_version
from conans.client.command import Conan, CommandOutputer, Command
from conans.model.version import Version


@contextmanager
def conan_command(output_stream):
    # This snippet reproduces code from conans.client.command.main, we cannot directly
    # use it because in case of error it is exiting the python interpreter :/
    conan_api, cache, user_io = Conan.factory()
    user_io.out._stream = output_stream
    outputer = CommandOutputer(user_io, cache)
    if Version(conan_version) >= "1.16":
        cmd = Command(conan_api)
    else:
        cmd = Command(conan_api, cache, user_io, outputer)
    try:
        yield cmd
    finally:
        if Version(conan_version) < "1.13":
            conan_api._remote_manager._auth_manager._localdb.connection.close()  # Close sqlite3
