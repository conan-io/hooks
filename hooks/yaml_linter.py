# coding=utf-8

import os
import platform
import subprocess
import sys

from conans.errors import ConanException
from conans.tools import logger


try:
    import yamllint
except ImportError as e:
    sys.stderr.write("Install yamllint to use 'yaml_linter' hook: 'pip install yamllint'")
    sys.exit(1)


CONAN_HOOK_YAMLLINT_WERR = "CONAN_YAMLLINT_WERR"


def pre_export(output, conanfile_path, *args, **kwargs):
    output.info("Lint yaml '{}'".format(conanfile_path))
    conanfile_dirname = os.path.dirname(conanfile_path)
    
    rules = {
        "document-start": "disable",
        "line-length": "disable",
        "new-lines": "{level: warning}",
        "empty-lines": "{level: warning}",
        "indentation": "{level: warning}",
        "trailing-spaces": "{level: warning}",
    }

    lint_args = ['-f', 'parsable',
                 '-d', '"{extends: default, rules: {%s}}"' %
                 ", ".join("%s: %s" % (r, rules[r]) for r in rules)]

    try:
        command = ['yamllint'] + lint_args + ['"%s"' % conanfile_dirname.replace('\\', '/')]
        command = " ".join(command)
        shell = bool(platform.system() != "Windows")
        p = subprocess.Popen(command, shell=shell, bufsize=10,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        yamllint_stdout, yamllint_stderr = p.communicate()
        yamllint_stdout = yamllint_stdout.decode('utf-8')
    except Exception as exc:
        output.error("Unexpected error running linter: {}".format(exc))
        return
    errors = 0
    for line in yamllint_stdout.splitlines():
        output.info(line)
        i = line.find(":")
        line = line[i:]
        i = line.find(":")
        line = line[i:]
        parts = line.split(' ')
        errors += int(parts[1] == "[error]")

    output.info("YAML Linter detected '{}' errors".format(errors))
    if os.getenv(CONAN_HOOK_YAMLLINT_WERR) and errors:
        raise ConanException("Package recipe has YAML linter errors. Please fix them.")
