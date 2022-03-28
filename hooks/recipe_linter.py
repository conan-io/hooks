# coding=utf-8

import json
import os
import platform
import subprocess
import re

from conans.errors import ConanException
from conans.tools import logger


CONAN_HOOK_PYLINT_RCFILE = "CONAN_PYLINTRC"
CONAN_HOOK_PYLINT_WERR = "CONAN_PYLINT_WERR"
CONAN_HOOK_PYLINT_RECIPE_PLUGINS = "CONAN_PYLINT_RECIPE_PLUGINS"


def pre_export(output, conanfile_path, *args, **kwargs):
    try:
        import astroid  # Conan 'pylint_plugin.py' uses astroid
        from pylint import epylint as lint
    except ImportError as e:
        output.error("Install pylint to use 'recipe_linter' hook: 'pip install pylint astroid'")
        return
    output.info("Lint recipe '{}'".format(conanfile_path))
    conanfile_dirname = os.path.dirname(conanfile_path)

    lint_args = ['--output-format=json',  # JSON output fails in Windows (parsing)
                 '--py3k',
                 '--enable=all',
                 '--reports=no',
                 '--disable=no-absolute-import',
                 '--persistent=no',
                 # These were disabled in linter that was inside Conan
                 # '--disable=W0702',  # No exception type(s) specified (bare-except)
                 # '--disable=W0703',  # Catching too general exception Exception (broad-except)
                 '--init-hook="import sys;sys.path.extend([\'{}\',])"'.format(conanfile_dirname.replace('\\', '/'))
                 ]

    pylint_plugins = os.getenv(CONAN_HOOK_PYLINT_RECIPE_PLUGINS, 'conans.pylint_plugin')
    if pylint_plugins:
        lint_args += ['--load-plugins={}'.format(pylint_plugins)]

    rc_file = os.getenv(CONAN_HOOK_PYLINT_RCFILE)
    if rc_file:
        lint_args += ['--rcfile', rc_file.replace('\\', '/')]

    try:
        command = ['pylint'] + lint_args + ['"{}"'.format(conanfile_path).replace('\\', '/')]
        command = " ".join(command)
        shell = bool(platform.system() != "Windows")
        p = subprocess.Popen(command, shell=shell, bufsize=10,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        pylint_stdout, pylint_stderr = p.communicate()

        # Remove ANSI escape sequences from Pylint output (fails in Windows)
        ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
        pylint_stdout = ansi_escape.sub('', pylint_stdout.decode('utf-8'))
    except Exception as exc:
        output.error("Unexpected error running linter: {}".format(exc))
    else:
        try:
            messages = json.loads(pylint_stdout)
        except Exception as exc:
            output.error("Error parsing JSON output: {}".format(exc))
            logger.error(
                "Error parsing linter output for recipe '{}': {}".format(conanfile_path, exc))
            logger.error(" - linter arguments: {}".format(lint_args))
            logger.error(" - output: {}".format(pylint_stdout))
            logger.error(" - stderr: {}".format(pylint_stderr))
        else:
            errors = 0
            for msg in messages:
                line = "{path}:{line}:{column}: {message-id}: {message} ({symbol})".format(**msg)
                output.info(line)
                errors += int(msg["type"] == "error")

            output.info("Linter detected '{}' errors".format(errors))
            if os.getenv(CONAN_HOOK_PYLINT_WERR) and errors:
                raise ConanException("Package recipe has linter errors. Please fix them.")
