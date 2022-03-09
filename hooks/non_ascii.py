# -*- coding: utf-8 -*-

import os
import unicodedata


def load(conanfile, filename):
    try:
        from conans.tools import load
        v2 = False
    except ImportError:
        from conan.tools.files import load
        v2 = True
    if v2:
        return load(conanfile, filename)
    else:
        return load(filename)


def check_non_ascii(filename, content, output):
    for num, line in enumerate(content.splitlines(), 1):
        bad_chars = {num: char for num, char in enumerate(line, 1) if ord(char) >= 128}
        if bad_chars:
            output.error("The file '{}' contains a non-ascii character at line ({})."
                        " Only ASCII characters are allowed, please remove it.".format(filename, num))
            indexes = bad_chars.keys()
            draw = ['^' if i in indexes else ' ' for i in range(1, len(line))]
            draw = ''.join(draw)
            bad_chars = bad_chars.values()
            bad_chars = ["\\x%s (%s)" % (format(ord(c), 'x'), unicodedata.name(c)) for c in bad_chars]
            message = "bad characters: " + ' '.join(bad_chars)
            output.info(message)
            output.info(line)
            output.info(draw)


def pre_export(output, conanfile, conanfile_path, reference, **kwargs):
    conanfile_content = load(conanfile, conanfile_path)
    check_non_ascii("conanfile.py", conanfile_content, output)
    test_package_dir = os.path.join(os.path.dirname(conanfile_path), "test_package")
    test_package_path = os.path.join(test_package_dir, "conanfile.py")
    if os.path.exists(test_package_path):
        test_package_content = load(conanfile, test_package_path)
        check_non_ascii("test_package/conanfile.py", test_package_content)
