# coding=utf-8

import os
import sys

from packaging import version
from six import StringIO

from conans.errors import ConanException

try:
    import astroid  # Conan 'pylint_plugin.py' uses astroid
    from pylint import lint, __version__ as pylint_version
    if version.parse(pylint_version) >= version.Version("2.4"):
        from pylint.reporters import JSONReporter
    else:
        from pylint.reporters.json import JSONReporter
except ImportError as e:
    sys.stderr.write("Install pylint to use 'recipe_linter' hook: 'pip install pylint astroid'")
    sys.exit(1)


CONAN_HOOK_PYLINT_RCFILE = "CONAN_PYLINTRC"
CONAN_HOOK_PYLINT_WERR = "CONAN_PYLINT_WERR"


def pre_export(output, conanfile_path, *args, **kwargs):
    output.info("Lint recipe '{}'".format(conanfile_path))

    lint_args = ['--verbose',
                 '--exit-zero',
                 '--py3k',
                 '--enable=all',
                 '--reports=no',
                 '--disable=no-absolute-import',
                 '--persistent=no',
                 '--load-plugins=conans.pylint_plugin',
                 '--disable=W0702',  # No exception type(s) specified (bare-except)
                 '--disable=W0703',  # Catching too general exception Exception (broad-except)
                 ]

    rc_file = os.getenv(CONAN_HOOK_PYLINT_RCFILE, None)
    if rc_file:
        lint_args += ['--rcfile', rc_file]

    lint_args += [conanfile_path]

    sys.path.insert(0, os.path.dirname(conanfile_path))
    try:
        buff = StringIO()
        reporter = JSONReporter(output=buff)
        if version.parse(pylint_version) >= version.Version("2.0"):
            lint.Run(lint_args, reporter=reporter, do_exit=False)
        else:
            lint.Run(lint_args, reporter=reporter, exit=False)
    except Exception as e:
        output.error("Unexpected error running linter: {}".format(e))
    else:
        for msg in reporter.messages:
            line = "{path}:{line}:{column}: {message-id}: {message} ({symbol})".format(**msg)
            output.info(line)

        if os.getenv(CONAN_HOOK_PYLINT_WERR) \
                and any(msg["type"] in ("error", "warning") for msg in reporter.messages):
            raise ConanException("Package recipe has linter errors. Please fix them.")
    finally:
        sys.path.pop()
