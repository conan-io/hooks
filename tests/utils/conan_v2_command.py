# coding=utf-8

from contextlib import contextmanager

import sys

from conan.api.conan_api import ConanAPI
from conan.cli.cli import Cli



@contextmanager
def conan_v2_command(output_stream):
    # This snippet reproduces code from conans.client.command.main, we cannot directly
    # use it because in case of error it is exiting the python interpreter :/
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = output_stream, output_stream

    conan_api = ConanAPI()
    cmd = Cli(conan_api)
    try:
        yield cmd
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
