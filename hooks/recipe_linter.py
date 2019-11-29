# coding=utf-8

import json
import os
import sys

from conans.errors import ConanException

try:
    import astroid  # Conan 'pylint_plugin.py' uses astroid
    from pylint import epylint as lint
except ImportError as e:
    sys.stderr.write("Install pylint to use 'recipe_linter' hook: 'pip install pylint astroid'")
    sys.exit(1)


CONAN_HOOK_PYLINT_RCFILE = "CONAN_PYLINTRC"
CONAN_HOOK_PYLINT_WERR = "CONAN_PYLINT_WERR"
CONAN_HOOK_PYLINT_RECIPE_PLUGINS = "CONAN_PYLINT_RECIPE_PLUGINS"


def pre_export(output, conanfile_path, *args, **kwargs):
    output.info("Lint recipe '{}'".format(conanfile_path))

    lint_args = ['"{}"'.format(conanfile_path),
                 '--output-format=json',
                 '--exit-zero',
                 '--py3k',
                 '--enable=all',
                 '--reports=no',
                 '--disable=no-absolute-import',
                 '--persistent=no',
                 '--disable=W0702',  # No exception type(s) specified (bare-except)
                 '--disable=W0703',  # Catching too general exception Exception (broad-except)
                 ]

    pylint_plugins = os.getenv(CONAN_HOOK_PYLINT_RECIPE_PLUGINS, 'conans.pylint_plugin')
    if pylint_plugins:
        lint_args += ['--load-plugins={}'.format(pylint_plugins)]

    rc_file = os.getenv(CONAN_HOOK_PYLINT_RCFILE)
    if rc_file:
        lint_args += ['--rcfile="{}"'.format(rc_file)]

    sys.path.insert(0, os.path.dirname(conanfile_path))
    try:
        command_line = " ".join(lint_args)
        (pylint_stdout, pylint_stderr) = lint.py_run(command_line, return_std=True)
        messages = json.loads(pylint_stdout.getvalue())
    except Exception as exc:
        output.error("Unexpected error running linter: {}".format(exc))
    else:
        for msg in messages:
            line = "{path}:{line}:{column}: {message-id}: {message} ({symbol})".format(**msg)
            output.info(line)

        if os.getenv(CONAN_HOOK_PYLINT_WERR) \
                and any(msg["type"] in ("error", "warning") for msg in messages):
            raise ConanException("Package recipe has linter errors. Please fix them.")
    finally:
        sys.path.pop()
