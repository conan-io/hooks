# coding=utf-8

import os
import platform
import subprocess

from conans.errors import ConanException
from conans.tools import logger


CONAN_HOOK_YAMLLINT_WERR = "CONAN_YAMLLINT_WERR"


def pre_export(output, conanfile_path, *args, **kwargs):
    output.info("Lint yaml '{}'".format(conanfile_path))
    conanfile_dirname = os.path.dirname(conanfile_path)
    conandata_file = os.path.join(conanfile_dirname, 'conadata.yaml')

    lint_args = ['-f', 'parsable',
                 '-d', '"{extends: default, rules: {document-start: disable}}"']

    try:
        command = ['yamllint'] + lint_args + [conandata_file.replace('\\', '/')]
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
    for line in messages.splitlines():
        output.info(line)
        parts = line.split(' ')
        errors += int(parts[1] == "[error]")

    output.info("YAML Linter detected '{}' errors".format(errors))
    if os.getenv(CONAN_HOOK_YAMLLINT_WERR) and errors:
        raise ConanException("Package recipe has YAML linter errors. Please fix them.")