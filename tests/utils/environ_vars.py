# coding=utf-8

import contextlib
import os
import re


@contextlib.contextmanager
def _context_restore():
    old_environ = dict(os.environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old_environ)


@contextlib.contextmanager
def clean_context_env(pattern):
    expr = re.compile(pattern)
    with _context_restore():
        for key, val in dict(os.environ).items():
            if expr.match(key):
                del os.environ[key]
        yield


@contextlib.contextmanager
def context_env(**environ):
    with _context_restore():
        os.environ.update(environ)
        yield

