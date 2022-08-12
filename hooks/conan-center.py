import ast
import collections

import fnmatch
import inspect
import os
import re
import sys
import subprocess

from logging import WARNING, ERROR, INFO, DEBUG, NOTSET

import yaml
from conans import tools
from conans.client.graph.python_requires import ConanPythonRequire
from conans.client.loader import parse_conanfile
try:
    from conans import Settings
except ImportError:
    from conans.model.settings import Settings

kb_errors = {"KB-H001": "DEPRECATED GLOBAL CPPSTD",
             "KB-H002": "REFERENCE LOWERCASE",
             "KB-H003": "RECIPE METADATA",
             "KB-H005": "HEADER_ONLY, NO COPY SOURCE",
             "KB-H006": "FPIC OPTION",
             "KB-H007": "FPIC MANAGEMENT",
             "KB-H008": "VERSION RANGES",
             "KB-H009": "RECIPE FOLDER SIZE",
             "KB-H010": "IMMUTABLE SOURCES",
             "KB-H011": "LIBCXX MANAGEMENT",
             "KB-H012": "PACKAGE LICENSE",
             "KB-H013": "DEFAULT PACKAGE LAYOUT",
             "KB-H014": "MATCHING CONFIGURATION",
             "KB-H015": "SHARED ARTIFACTS",
             "KB-H016": "CMAKE-MODULES-CONFIG-FILES",
             "KB-H017": "PDB FILES NOT ALLOWED",
             "KB-H018": "LIBTOOL FILES PRESENCE",
             "KB-H019": "CMAKE FILE NOT IN BUILD FOLDERS",
             "KB-H020": "PC-FILES",
             "KB-H021": "MS RUNTIME FILES",
             "KB-H022": "CPPSTD MANAGEMENT",
             "KB-H023": "EXPORT LICENSE",
             "KB-H024": "TEST PACKAGE FOLDER",
             "KB-H025": "META LINES",
             "KB-H026": "LINTER WARNINGS",
             "KB-H027": "CONAN CENTER INDEX URL",
             "KB-H028": "CMAKE MINIMUM VERSION",
             "KB-H029": "TEST PACKAGE - RUN ENVIRONMENT",
             "KB-H030": "CONANDATA.YML FORMAT",
             "KB-H031": "CONANDATA.YML REDUCE",
             "KB-H032": "SYSTEM REQUIREMENTS",
             "KB-H034": "TEST PACKAGE - NO IMPORTS()",
             "KB-H037": "NO AUTHOR",
             "KB-H039": "NOT ALLOWED ATTRIBUTES",
             "KB-H040": "NO TARGET NAME",
             "KB-H041": "NO FINAL ENDLINE",
             "KB-H043": "MISSING SYSTEM LIBS",
             "KB-H044": "NO REQUIRES.ADD()",
             "KB-H045": "DELETE OPTIONS",
             "KB-H046": "CMAKE VERBOSE MAKEFILE",
             "KB-H048": "CMAKE VERSION REQUIRED",
             "KB-H049": "CMAKE WINDOWS EXPORT ALL SYMBOLS",
             "KB-H050": "DEFAULT SHARED OPTION VALUE",
             "KB-H051": "DEFAULT OPTIONS AS DICTIONARY",
             "KB-H052": "CONFIG.YML HAS NEW VERSION",
             "KB-H053": "PRIVATE IMPORTS",
             "KB-H054": "LIBRARY DOES NOT EXIST",
             "KB-H055": "SINGLE REQUIRES",
             "KB-H056": "LICENSE PUBLIC DOMAIN",
             "KB-H057": "TOOLS RENAME",
             "KB-H058": "ILLEGAL CHARACTERS",
             "KB-H059": "CLASS NAME",
             "KB-H060": "NO CRLF",
             "KB-H061": "NO BUILD SYSTEM FUNCTIONS",
             "KB-H062": "TOOLS CROSS BUILDING",
             "KB-H064": "INVALID TOPICS",
             "KB-H065": "NO REQUIRED_CONAN_VERSION",
             "KB-H066": "SHORT_PATHS USAGE",
             "KB-H068": "TEST_TYPE MANAGEMENT",
             "KB-H069": "TEST PACKAGE - NO DEFAULT OPTIONS",
             "KB-H070": "MANDATORY SETTINGS",
             "KB-H071": "INCLUDE PATH DOES NOT EXIST",
             }


this = sys.modules[__name__]


class _HooksOutputErrorCollector(object):

    def __init__(self, output, kb_id=None):
        self._output = output
        self._error = False
        self._test_name = kb_errors[kb_id] if kb_id else ""
        self.kb_id = kb_id
        if self.kb_id:
            self.kb_url = kb_url(self.kb_id)
        self._error_level = int(os.getenv("CONAN_HOOK_ERROR_LEVEL", str(NOTSET)))

    def _get_message(self, message):
        if self._test_name:
            name = "{} ({})".format(self._test_name, self.kb_id) if self.kb_id else self._test_name
            return "[{}] {}".format(name, message)
        else:
            return message

    def success(self, message):
        self._output.success(self._get_message(message))

    def debug(self, message):
        if self._error_level and self._error_level <= DEBUG:
            self._error = True
        self._output.debug(self._get_message(message))

    def info(self, message):
        if self._error_level and self._error_level <= INFO:
            self._error = True
        self._output.info(self._get_message(message))

    def warn(self, message):
        if self._error_level and self._error_level <= WARNING:
            self._error = True
        if hasattr(self._output, "warn"):
            self._output.warn(self._get_message(message))
        else:
            self._output.warning(self._get_message(message))

    def error(self, message):
        self._error = True
        url_str = '({})'.format(self.kb_url) if self.kb_id else ""
        self._output.error(self._get_message(message) + " " + url_str)

    def __str__(self):
        return self._output._stream.getvalue()

    @property
    def failed(self):
        return self._error

    def raise_if_error(self):
        if self._error and self._error_level and self._error_level <= ERROR:
            raise Exception("Some checks failed running the hook, check the output")


def raise_if_error_output(func):
    def wrapper(output, *args, **kwargs):
        output = _HooksOutputErrorCollector(output)
        ret = func(output, *args, **kwargs)
        output.raise_if_error()
        return ret

    return wrapper


def kb_url(kb_id):
    return "https://github.com/conan-io/conan-center-index/blob/master/docs/error_knowledge_base.md#{}".format(kb_id)


def run_test(kb_id, output):
    def tmp(func):
        out = _HooksOutputErrorCollector(output, kb_id)
        try:
            ret = func(out)
            if not out.failed:
                out.success("OK")
            return ret
        except Exception as e:
            out.error("Exception raised from hook: {} (type={})".format(e, type(e).__name__))
            raise

    return tmp


def load_yml(path):
    if os.path.isfile(path):
        return yaml.safe_load(tools.load(path))
    return None


@raise_if_error_output
def pre_export(output, conanfile, conanfile_path, reference, **kwargs):
    this.reference = str(reference)
    conanfile_content = tools.load(conanfile_path)
    export_folder_path = os.path.dirname(conanfile_path)
    settings = _get_settings(conanfile)
    header_only = _is_recipe_header_only(conanfile)
    installer = settings is not None and "os_build" in settings and "arch_build" in settings

    @run_test("KB-H001", output)
    def test(out):
        if settings and "cppstd" in settings:
            out.error("The 'cppstd' setting is deprecated. Use the 'compiler.cppstd' "
                      "subsetting instead")

    @run_test("KB-H002", output)
    def test(out):
        if reference.name != reference.name.lower():
            out.error("The library name has to be lowercase")
        if reference.version != str(reference.version).lower():
            out.error("The library version has to be lowercase")

    @run_test("KB-H003", output)
    def test(out):
        def _message_attr(attributes, out_method):
            for field in attributes:
                field_value = getattr(conanfile, field, None)
                if not field_value:
                    out_method("Conanfile doesn't have '%s' attribute. " % field)

        if not re.search(r"(\s{4}|\t)name\s*=", conanfile_content):
            out.error("Conanfile doesn't have 'name' attribute.")
        _message_attr(["url", "license", "description", "homepage", "topics"], out.error)

    @run_test("KB-H005", output)
    def test(out):
        no_copy_source = getattr(conanfile, "no_copy_source", None)
        if not settings and header_only and not no_copy_source:
            out.warn("This recipe is a header only library as it does not declare "
                     "'settings'. Please include 'no_copy_source' to avoid unnecessary copy steps")

    @run_test("KB-H006", output)
    def test(out):
        options = getattr(conanfile, "options", None)
        if settings and options and not header_only and "fPIC" not in options and not installer:
            out.warn("This recipe does not include an 'fPIC' option. Make sure you are using the "
                     "right casing")

    @run_test("KB-H008", output)
    def test(out):
        # This regex takes advantage that a conan reference is always a string
        vrange_match = re.compile(r'.*[\'"][a-zA-Z0-9_+.-]+/\[.+\]@[a-zA-Z0-9_+./-]+[\'"].*')
        for num, line in enumerate(conanfile_content.splitlines(), 1):
            if vrange_match.match(line):
                out.error("Possible use of version ranges, line %s:\n %s" % (num, line))

    @run_test("KB-H009", output)
    def test(out):
        max_folder_size = int(os.getenv("CONAN_MAX_RECIPE_FOLDER_SIZE_KB", 256))
        dir_path = os.path.dirname(conanfile_path)
        total_size = 0
        for path, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in dirs if
                       d not in [".conan"]]  # Discard the generated .conan directory
            if _skip_test_package(path, dir_path):
                # Discard any file in temp builds
                continue
            for files_it in files:
                file_path = os.path.join(path, files_it)
                if not os.path.islink(file_path):
                    total_size += os.path.getsize(file_path)

        total_size_kb = total_size / 1024
        out.success("Total recipe size: %s KB" % total_size_kb)
        if total_size_kb > max_folder_size:
            out.error("The size of your recipe folder ({} KB) is larger than the maximum allowed"
                      " size ({}KB).".format(total_size_kb, max_folder_size))

    @run_test("KB-H023", output)
    def test(out):
        for attr_it in ["exports", "exports_sources"]:
            exports = getattr(conanfile, attr_it, None)
            out.info("exports: {}".format(exports))
            if exports is None:
                continue
            exports = [exports] if isinstance(exports, str) else exports
            for exports_it in exports:
                for license_it in ["copying", "license", "copyright"]:
                    if license_it in exports_it.lower():
                        out.error("This recipe is exporting a license file. "
                                  "Remove %s from `%s`" % (exports_it, attr_it))

    @run_test("KB-H024", output)
    def test(out):
        dir_path = os.path.dirname(conanfile_path)
        test_package_path = os.path.join(dir_path, "test_package")
        if not os.path.exists(test_package_path):
            out.error("There is no 'test_package' for this recipe")
        elif not os.path.exists(os.path.join(test_package_path, "conanfile.py")):
            out.error("There is no 'conanfile.py' in 'test_package' folder")

    @run_test("KB-H025", output)
    def test(out):
        def _search_for_metaline(from_line, to_line, lines):
            for index in range(from_line, to_line):
                line_number = index + 1
                if "# -*- coding:" in lines[index] or \
                   "# coding=" in lines[index]:
                    out.error("PEP 263 (encoding) is not allowed in the conanfile. "
                              "Remove the line {}".format(line_number))
                if "#!" in lines[index]:
                    out.error("Shebang (#!) detected in your recipe. "
                              "Remove the line {}".format(line_number))
                if "# vim:" in lines[index]:
                    out.error("vim editor configuration detected in your recipe. "
                              "Remove the line {}".format(line_number))

        conanfile_lines = conanfile_content.splitlines()
        first_lines_range = 5 if len(conanfile_lines) > 5 else len(conanfile_lines)
        _search_for_metaline(0, first_lines_range, conanfile_lines)

        last_lines_range = len(conanfile_lines) - 3 if len(conanfile_lines) > 8 else len(conanfile_lines)
        _search_for_metaline(last_lines_range, len(conanfile_lines), conanfile_lines)

    @run_test("KB-H027", output)
    def test(out):
        url = getattr(conanfile, "url", None)
        if url and not url.startswith("https://github.com/conan-io/conan-center-index"):
            out.error("The attribute 'url' should point to: "
                      "https://github.com/conan-io/conan-center-index")

    @run_test("KB-H028", output)
    def test(out):
        def _find_cmake_minimum(folder):
            for (root, _, filenames) in os.walk(folder):
                for filename in filenames:
                    if filename.lower().startswith("cmake") and \
                       (filename.endswith(".txt") or filename.endswith(".cmake")) and \
                       not _skip_test_package(root, folder):
                        cmake_path = os.path.join(root, filename)
                        cmake_content = tools.load(cmake_path).lower()
                        for line in cmake_content.splitlines():
                            if line.startswith("#") or re.search(r"^\s+#", line) or len(line.strip()) == 0:
                                continue
                            elif "cmake_minimum_required(version" in line or \
                                 "cmake_minimum_required (version" in line:
                                break
                            else:
                                file_path = os.path.join(os.path.relpath(root), filename)
                                out.error("The CMake file '%s' must contain a minimum version "
                                          "declared at the beginning (e.g. cmake_minimum_required(VERSION 3.1.2))" %
                                          file_path)

        dir_path = os.path.dirname(conanfile_path)
        _find_cmake_minimum(dir_path)

    @run_test("KB-H029", output)
    def test(out):
        test_package_path = os.path.join(export_folder_path, "test_package")
        if not os.path.exists(os.path.join(test_package_path, "conanfile.py")):
            return

        test_package_conanfile = tools.load(os.path.join(test_package_path, "conanfile.py"))
        if "RunEnvironment" in test_package_conanfile and \
           not re.search(r"self\.run\(.*, run_environment=True\)", test_package_conanfile):
            out.error("The 'RunEnvironment()' build helper is no longer needed. "
                      "It has been integrated into the self.run(..., run_environment=True)")

    @run_test("KB-H032", output)
    def test(out):
        if conanfile.version == "system":
            out.info("'system' versions are allowed to install system requirements.")
            return
        if "def system_requirements" in conanfile_content and \
           "SystemPackageTool" in conanfile_content:
            import re
            match = re.search(r'(\S+)\s?=\s?(tools.)?SystemPackageTool', conanfile_content)
            if ("SystemPackageTool().install" in conanfile_content) or \
               (match and "{}.install".format(match.group(1)) in conanfile_content):
                out.error("The method 'SystemPackageTool.install' is not allowed in the recipe.")

    @run_test("KB-H030", output)
    def test(out):
        conandata_path = os.path.join(export_folder_path, "conandata.yml")
        version = conanfile.version
        allowed_first_level = ["sources", "patches"]
        allowed_sources = ["md5", "sha1", "sha256", "url"]
        allowed_patches = ["patch_file", "base_path", "url", "sha256", "sha1", "md5", "patch_type", "patch_source", "patch_description"]
        weak_checksums = ["md5", "sha1"]
        checksums = ["md5", "sha1", "sha256"]
        found_checksums = []
        has_sources = False
        is_google_source = False

        def _not_allowed_entries(info, allowed_entries):
            not_allowed = []
            fields = info if isinstance(info, list) else [info]
            for field in fields:
                if isinstance(field, dict):
                    return _not_allowed_entries(list(field.keys()), allowed_entries)
                else:
                    if field not in allowed_entries:
                        not_allowed.append(field)
            return not_allowed

        conandata_yml = load_yml(conandata_path)
        if not conandata_yml:
            return
        entries = _not_allowed_entries(list(conandata_yml.keys()), allowed_first_level)
        if entries:
            out.error("First level entries %s not allowed. Use only first level entries %s in "
                      "conandata.yml" % (entries, allowed_first_level))

        google_source_regex = re.compile(r"https://\w+.googlesource.com/")

        for entry in conandata_yml:
            if entry in ['sources', 'patches']:
                if not isinstance(conandata_yml[entry], dict):
                    out.error("Expecting a dictionary with versions as keys under '{}' element".format(entry))
                else:
                    versions = conandata_yml[entry].keys()
                    if any([not isinstance(it, str) for it in versions]):
                        out.error("Versions in conandata.yml should be strings. Add quotes around the numbers")

            def validate_one(e, name, allowed):
                not_allowed = _not_allowed_entries(e, allowed)
                if not_allowed:
                    out.error("Additional entries %s not allowed in '%s':'%s' of "
                              "conandata.yml" % (not_allowed, name, version))
                    return False
                return True

            def validate_recursive(e, data, name, allowed):
                if isinstance(e, str) and e not in allowed_sources and not isinstance(data[e], str):
                    for child in data[e]:
                        if not validate_recursive(child, data[e], name, allowed):
                            return False
                    return True
                else:
                    return validate_one(e, name, allowed)

            def validate_checksum_recursive(e, data):
                def check_is_google_source(v):
                    nonlocal is_google_source
                    urls = v if isinstance(v, list) else [v]
                    if any(re.search(google_source_regex, url) for url in urls):
                        is_google_source = True

                if isinstance(e, str) and e not in allowed_sources and not isinstance(data[e], str):
                    for child in data[e]:
                        validate_checksum_recursive(child, data[e])
                else:
                    if isinstance(e, dict):
                        for k, v in e.items():
                            if k in checksums:
                                found_checksums.append(k)
                                if not v:
                                    out.error(f"The entry '{k}' cannot be empty in conandata.yml.")
                            if k == "url":
                                check_is_google_source(v)
                    else:
                        fields = e if isinstance(e, list) else [e]
                        for field in fields:
                            if field in checksums:
                                found_checksums.append(field)
                                if not data[field]:
                                    out.error(f"The entry '{field}' cannot be empty in conandata.yml.")
                        if "url" in data:
                            check_is_google_source(data["url"])

            if version not in conandata_yml[entry]:
                continue
            for element in conandata_yml[entry][version]:
                if entry == "patches":
                    if not validate_recursive(element, conandata_yml[entry][version], "patches",
                                              allowed_patches):
                        return
                if entry == "sources":
                    if not validate_recursive(element, conandata_yml[entry][version], "sources",
                                              allowed_sources):
                        return
            for element in conandata_yml[entry][version]:
                if entry == "sources":
                    has_sources = True
                    validate_checksum_recursive(element, conandata_yml[entry][version])
            if not found_checksums and has_sources and not is_google_source:
                out.error("The checksum key 'sha256' must be declared and can not be empty.")
            elif found_checksums and 'sha256' not in found_checksums:
                out.warn(f"Consider 'sha256' instead of {weak_checksums}. It's considerably more secure than others.")


    @run_test("KB-H034", output)
    def test(out):
        test_package_path = os.path.join(export_folder_path, "test_package")
        if not os.path.exists(os.path.join(test_package_path, "conanfile.py")):
            return

        test_package_conanfile = tools.load(os.path.join(test_package_path, "conanfile.py"))
        if "def imports" in test_package_conanfile:
            out.error("The method `imports` is not allowed in test_package/conanfile.py")

    @run_test("KB-H037", output)
    def test(out):
        author = getattr(conanfile, "author", None)
        if author:
            if isinstance(author, str):
                author = '"%s"' % author
            out.error("Conanfile should not contain author. Remove 'author = {}'".format(author))

    @run_test("KB-H039", output)
    def test(out):
        search_attrs = ["scm", "build_policy"]
        forbidden_attrs = []
        for attr in search_attrs:
            if getattr(conanfile, attr, None):
                forbidden_attrs.append(attr)
        if re.search(r"revision_mode\s=", conanfile_content):
            forbidden_attrs.append("revision_mode")

        if forbidden_attrs:
            out.error("Conanfile should not contain attributes: '{}'"
                      .format(", ".join(forbidden_attrs)))

    @run_test("KB-H040", output)
    def test(out):
        match = re.search(r"self\.cpp_info\.(name|filename)\s?=", conanfile_content)
        if match:
            out.error("CCI uses the name of the package for cmake generator and filename by default."
                      " Replace 'cpp_info.{0}' by 'cpp_info.{0}s[<generator>]'.".format(match.group(1)))

        match = re.search(r"self\.cpp_info\.(names|filenames)\[\s?['\"](cmake|cmake_multi)['\"]\s?\]", conanfile_content)
        if match:
            out.error("CCI uses the name of the package for {0} generator. "
                      "Conanfile should not contain 'self.cpp_info.{1}['{0}']'. "
                      "Use 'cmake_find_package' and 'cmake_find_package_multi' instead.".format(match.group(2),
                                                                                                 match.group(1)))

    @run_test("KB-H041", output)
    def test(out):
        checked_fileexts = ".c", ".cc", ".cpp", ".cxx", ".h", ".hxx", ".hpp", \
                           ".py", ".txt", ".yml", ".cmake", ".xml", ".patch", ".md"

        files_noext = "Makefile", "GNUMakefile"

        def _check_final_newline(path):
            try:
                last_char = tools.load(path)[-1]
            except (OSError, IndexError):
                return  # File is empty ==> ignore
            if last_char not in ("\n", "\r"):
                out.error("File '{}' does not end with an endline".format(path))

        for root, _, filenames in os.walk(export_folder_path):
            if _skip_test_package(root, export_folder_path):
                # Discard any file in temp builds
                continue
            for filename in filenames:
                _, fileext = os.path.splitext(filename)
                if filename in files_noext or fileext.lower() in checked_fileexts:
                    _check_final_newline(os.path.join(root, filename))

        config_yml = os.path.join(export_folder_path, os.path.pardir, "config.yml")
        if os.path.isfile(config_yml):
            _check_final_newline(config_yml)

    @run_test("KB-H044", output)
    def test(out):
        for forbidden in ["self.requires.add", "self.build_requires.add"]:
            if forbidden in conanfile_content:
                out.error("The method '{}()' is not allowed. Use '{}()' instead."
                          .format(forbidden, forbidden.replace(".add", "")))

    @run_test("KB-H045", output)
    def test(out):
        if "self.options.remove" in conanfile_content:
            out.error("Found 'self.options.remove'. Replace it by 'del self.options.<opt>'.")

    @run_test("KB-H046", output)
    def test(out):

        def check_for_verbose_flag(cmakelists_path):
            cmake_content = tools.load(cmakelists_path)
            if "cmake_verbose_makefile" in cmake_content.lower():
                out.error("The CMake definition 'set(CMAKE_VERBOSE_MAKEFILE ON)' is not allowed. "
                          "Remove it from {}.".format(os.path.relpath(cmakelists_path)))

        dir_path = os.path.dirname(conanfile_path)
        test_package_path = os.path.join(dir_path, "test_package")
        for cmake_path in [os.path.join(dir_path, "CMakeLists.txt"),
                           os.path.join(test_package_path, "CMakeLists.txt")]:
            if os.path.exists(cmake_path):
                check_for_verbose_flag(cmake_path)

    @run_test("KB-H048", output)
    def test(out):
        dir_path = os.path.dirname(conanfile_path)
        cmake_test_pkg = os.path.join(dir_path, "test_package", "CMakeLists.txt")
        if os.path.isfile(cmake_test_pkg):
            cmake_content = tools.load(cmake_test_pkg)
            if re.search(r"cmake_minimum_required\(version [\"']?2", cmake_content.lower()):
                out.error("The test_package/CMakeLists.txt requires CMake 3.1 at least."
                          " Update to 'cmake_minimum_required(VERSION 3.1)'.")

        cmake_path = os.path.join(dir_path, "CMakeLists.txt")
        if os.path.isfile(cmake_path):
            cmake_content = tools.load(cmake_path)
            if re.search(r"cmake_minimum_required\(version [\"']?2", cmake_content.lower()) and \
               "cxx_standard" in cmake_content.lower():
                out.error("The CMake definition CXX_STANDARD requires CMake 3.1 at least."
                          " Update to 'cmake_minimum_required(VERSION 3.1)'.")

    @run_test("KB-H049", output)
    def test(out):
        dir_path = os.path.dirname(conanfile_path)
        cmake_path = os.path.join(dir_path, "CMakeLists.txt")
        if os.path.isfile(cmake_path):
            cmake_content = tools.load(cmake_path)
            match = re.search(r"cmake_minimum_required\s?\(VERSION (\d?\.?\d?\.?\d+)\)",
                              cmake_content, re.I)
            if match and tools.Version(match.group(1)) < "3.4":
                for cmake_def in ["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS", "WINDOWS_EXPORT_ALL_SYMBOLS"]:
                    if cmake_def in cmake_content:
                        out.error("The CMake definition {} requires CMake 3.4 at least. Update "
                                "CMakeLists.txt to 'cmake_minimum_required(VERSION 3.4)'."
                                .format(cmake_def))
                        break

    @run_test("KB-H051", output)
    def test(out):
        default_options = getattr(conanfile, "default_options")
        if default_options and not isinstance(default_options, dict):
            out.error("Use a dictionary to declare 'default_options'")

    @run_test("KB-H052", output)
    def test(out):
        config_path = os.path.abspath(os.path.join(export_folder_path, os.path.pardir, "config.yml"))
        config_yml = load_yml(config_path)

        conandata_path = os.path.join(export_folder_path, "conandata.yml")
        conandata_yml = load_yml(conandata_path)

        if not config_yml or not conandata_yml:
            return

        if 'versions' not in config_yml:
            return

        if 'sources' not in conandata_yml:
            return

        versions_conandata = conandata_yml['sources'].keys()
        versions_config = config_yml['versions'].keys()
        conandata_path = os.path.relpath(conandata_path, export_folder_path)
        config_path = os.path.relpath(config_path, export_folder_path)

        for version in versions_conandata:
            if version not in versions_config:
                out.error('The version "{}" exists in "{}" but not in "{}", so it will not be built.'
                          ' Please update "{}" to include newly added '
                          'version "{}".'.format(version, conandata_path, config_path, config_path,
                                                 version))

    @run_test("KB-H053", output)
    def test(out):
        def _is_private_import(line):
            if line in ["from conans.model import Generator"]:
                return False
            allowed_list = ["tools", "errors"]
            for pattern in ["from conans.", "import conans."]:
                if line.startswith(pattern):
                    for allowed in allowed_list:
                        if line.startswith(pattern + allowed):
                            return False
                    return True
            return False

        def _check_private_imports(filename, content):
            for num, line in enumerate(content.splitlines(), 1):
                if _is_private_import(line):
                    out.error("The file {} imports private conan API on line {}, "
                              "this is strongly discouraged.".format(filename, num))
                    out.error(line)

        _check_private_imports("conanfile.py", conanfile_content)
        test_package_dir = os.path.join(os.path.dirname(conanfile_path), "test_package")
        test_package_path = os.path.join(test_package_dir, "conanfile.py")
        if os.path.exists(test_package_path):
            test_package_content = tools.load(test_package_path)
            _check_private_imports("test_package/conanfile.py", test_package_content)

    @run_test("KB-H055", output)
    def test(out):
        for prefix in ["", "build_"]:
            if hasattr(conanfile, "{}requires".format(prefix)) and \
               callable(getattr(conanfile, "{}requirements".format(prefix), None)):
                out.error("Both '{0}requires' attribute and '{0}requirements()' method should not "
                          "be declared at same recipe.".format(prefix))

    @run_test("KB-H057", output)
    def test(out):
        def _check_content(content, path):
            if "os.rename" in content:
                out.warn("The 'os.rename' in {} may cause permission error on Windows."
                         " Use 'conan.tools.files.rename(self, src, dst)' instead.".format(path))
            elif "tools.rename(" in content and not "tools.rename(self," in content:
                out.warn("The 'tools.rename' in {} is outdated and may cause permission error on Windows."
                         " Use 'conan.tools.files.rename(self, src, dst)' instead.".format(path))
        _check_content(conanfile_content, "conanfile.py")
        test_package_path = os.path.join(os.path.dirname(conanfile_path), "test_package", "conanfile.py")
        if os.path.exists(test_package_path):
            test_package_content = tools.load(test_package_path)
            _check_content(test_package_content, "test_package/conanfile.py")

    @run_test("KB-H058", output)
    def test(out):
        disallowed_chars = '<>:"/\\|?*%,; '
        recipe_folder = os.path.dirname(conanfile_path)
        for root, _, files in os.walk(recipe_folder):
            for file in files:
                if any(it in disallowed_chars for it in file):
                    out.error("The file '{}' uses illegal charecters ({}) for its name."
                              " Please, rename that file.".format(file, disallowed_chars))
                if file.endswith("."):
                    out.error("The file '{}' ends with a dot. Please, remove the dot from the end."
                              .format(file, disallowed_chars))

    @run_test("KB-H059", output)
    def test(out):
        class_name = type(conanfile).__name__
        if class_name in ("LibnameConan", "ConanFileDefault"):
            camel_name = "".join(s.title() for s in re.split("[^a-zA-Z0-9]", conanfile.name))
            out.warn("Class name '{}' is not allowed. For example, use '{}Conan' instead.".format(class_name, camel_name))

    @run_test("KB-H060", output)
    def test(out):
        ext_to_be_checked = [".cmake", ".conf", ".cfg", ".diff", ".md", ".patch", ".py", ".txt",
                             ".yml", ".am", ".xml", ".json", ".in", ".ac", ".tsx", ".tmx",
                             ".proto", ".capnp", ".c", ".cc", ".c++", ".cpp", ".cxx", ".c++m",
                             ".cppm", ".cxxm", ".h++", ".hh", ".hxx", ".hpp", ".qrc", ".pro",
                             ".build", ".s", ".asm"]
        recipe_folder = os.path.dirname(conanfile_path)
        for root, _, files in os.walk(recipe_folder):
            if _skip_test_package(root, recipe_folder):
                continue
            for filename in files:
                if not any(filename.lower().endswith(ext) for ext in ext_to_be_checked):
                    continue
                lines = open(os.path.join(root, filename), 'rb').readlines()
                if any(line.endswith(b'\r\n') for line in lines):
                    out.error("The file '{}' uses CRLF. Please, replace by LF."
                              .format(filename))

    @run_test("KB-H061", output)
    def test(out):
        Location = collections.namedtuple("Location", ("line", "column", "line_end", "column_end"))
        BuildInfo = collections.namedtuple("BuildInfo", ("loc", "what", "func"))
        class BuildInfoVisitor(ast.NodeVisitor):
            METHODS_NO_BUILDINFO = (
                "build_requirements",
                "config_options",
                "configure",
                "package_id",
                "package_info",
                "requirements",
                "source",
                "validate",
            )

            def __init__(self):
                self.invalids = []
                self.function_def_stack = []
                ast.NodeVisitor.__init__(self)

            def visit_FunctionDef(self, node):
                self.function_def_stack.append(node.name)
                self.generic_visit(node)
                self.function_def_stack.pop()

            def visit_Attribute(self, node):
                methods_stack_no_build_info_allowed = [fdef for fdef in self.function_def_stack if fdef in self.METHODS_NO_BUILDINFO]
                if methods_stack_no_build_info_allowed:
                    # FIXME: Not all python 2.7 interpretors have node.end_lineno or node.end_col_offset
                    if (node.attr == "os_info" and isinstance(node.value, ast.Name) and node.value.id == "tools") or \
                       (node.attr.startswith("is_") and isinstance(node.value, ast.Name) and node.value.id == "os_info"):
                        self.invalids.append(BuildInfo(Location(node.lineno, node.col_offset, getattr(node, "end_lineno", node.lineno), getattr(node, "end_col_offset", node.col_offset)), "tools.os_info", methods_stack_no_build_info_allowed[0]))
                    elif isinstance(node.value, ast.Name) and node.value.id == "platform":
                        self.invalids.append(BuildInfo(Location(node.lineno, node.col_offset, getattr(node, "end_lineno", node.lineno), getattr(node, "end_col_offset", node.col_offset)), "platform", methods_stack_no_build_info_allowed[0]))
                self.generic_visit(node)

        to_test = [(conanfile_path, conanfile_content),]
        test_conanfile_path = os.path.join(export_folder_path, "test_package", "conanfile.py")
        if os.path.isfile(test_conanfile_path):
            to_test.append((test_conanfile_path, tools.load(test_conanfile_path)))

        for dut_conanfile_path, dut_conanfile_contents in to_test:
            try:
                node = ast.parse(dut_conanfile_contents)
            except SyntaxError:
                out.error("A SyntaxError was thrown while parsing '{}'".format(dut_conanfile_path))
                continue
            visitor = BuildInfoVisitor()
            visitor.visit(node)
            for build_info in visitor.invalids:
                out.error("{}:{} Build system dependent functions detected. (Use of {} is forbidden in {})".format(
                    dut_conanfile_path, build_info.loc.line, build_info.what, build_info.func))


    @run_test("KB-H062", output)
    def test(out):
        def _check_content(content, path):
            if "tools.cross_building(self.settings)" in content:
                out.warn("The 'tools.cross_building(self.settings)' syntax in {} may not work correctly "
                         "in some scenarios. Consider using tools.cross_building(self).".format(path))

        _check_content(conanfile_content, "conanfile.py")
        test_package_path = os.path.join(os.path.dirname(conanfile_path), "test_package",
                                         "conanfile.py")
        if os.path.exists(test_package_path):
            test_package_content = tools.load(test_package_path)
            _check_content(test_package_content, test_package_path)

    @run_test("KB-H064", output)
    def test(out):
        topics = getattr(conanfile, "topics")
        if topics and isinstance(topics, (list, tuple)):
            invalid_topics = ["conan"]
            for topic in topics:
                if topic in invalid_topics:
                    out.warn("The topic '{}' is invalid and should be removed from topics "
                             "attribute.".format(topic))
                if topic != topic.lower():
                    out.warn("The topic '{}' is invalid; even names and acronyms should be formatted "
                             "entirely in lowercase.".format(topic))

    @run_test("KB-H065", output)
    def test(out):
        def _find_required_conan_version(conanfile_content):
            match = re.search(r"^\s*required_conan_version\s*=\s*[\"']>=\s*([\d\.]+)[\"']",
                              conanfile_content, re.MULTILINE)
            if match:
                return tools.Version(match.group(1))
            return None

        conanfile_content = tools.load(conanfile_path)

        found_strip_root = False
        lines = conanfile_content.splitlines()
        for idx, line in enumerate(lines):
            # check current and next line
            if 'tools.get' in line and any('strip_root=True' in l for l in lines[idx:idx+2]):
                found_strip_root = True

        version = _find_required_conan_version(conanfile_content)
        required_version = tools.Version('1.33.0')
        if found_strip_root and (not version or version < required_version):
            out.warn("tools.get with strip_root=True is available since Conan {0}. "
                     "Please add `required_conan_version >= \"{0}\"`"
                     "".format(str(required_version)))

    @run_test("KB-H068", output)
    def test(out):
        test_package_path = os.path.join(os.path.dirname(conanfile_path), "test_package", "conanfile.py")
        if os.path.isfile(test_package_path):
            try:
                test_conanfile = _load_conanfile(test_package_path)
                test_type = getattr(test_conanfile, "test_type", None)
                if test_type and test_type != "explicit":
                    out.error(f"The attribute 'test_type' only should be used with 'explicit' value.: {test_type}")
            except Exception as e:
                out.warn("Invalid conanfile: {}".format(e))

    @run_test("KB-H069", output)
    def test(out):
        test_package_path = os.path.join(os.path.dirname(conanfile_path), "test_package", "conanfile.py")
        if os.path.isfile(test_package_path):
            try:
                test_conanfile = _load_conanfile(test_package_path)
                default_options = getattr(test_conanfile, "default_options", None)
                if default_options:
                    out.error(f"The attribute 'default_options' is not allowed on test_package/conanfile.py, remove it.")
            except Exception as e:
                out.warn("Invalid conanfile: {}".format(e))


    @run_test("KB-H070", output)
    def test(out):
        settings = getattr(conanfile, "settings", None)
        if settings:
            settings = settings if isinstance(settings, (list, tuple)) else [settings]
            missing = [x for x in ["os", "arch", "compiler", "build_type"] if x not in settings]
            if missing:
                out.warn("The values '{}' are missing on 'settings' attribute. Update settings with the missing "
                         "values and use 'package_id(self)' method to manage the package ID.".format("', '".join(missing)))
        else:
            out.warn("No 'settings' detected in your conanfile.py. Add 'settings' attribute and use 'package_id(self)' method to manage the package ID.")


@raise_if_error_output
def post_export(output, conanfile, conanfile_path, reference, **kwargs):
    export_folder_path = os.path.dirname(conanfile_path)

    @run_test("KB-H031", output)
    def test(out):
        conandata_path = os.path.join(export_folder_path, "conandata.yml")
        version = str(conanfile.version)

        conandata_yml = load_yml(conandata_path)
        if not conandata_yml:
            return
        info = {}
        for entry in conandata_yml:
            if version not in conandata_yml[entry]:
                continue
            info[entry] = {}
            info[entry][version] = conandata_yml[entry][version]
        out.info("Saving conandata.yml: {}".format(info))
        new_conandata_yml = yaml.safe_dump(info, default_flow_style=False)
        out.info("New conandata.yml contents: {}".format(new_conandata_yml))
        tools.save(conandata_path, new_conandata_yml)

    @run_test("KB-H050", output)
    def test(out):
        allowlist = (
            "libgphoto2",
            "onetbb",
            "opencl-icd-loader",
            "paho-mqtt-c",
            "pdal",
            "tbb",
            "vulkan-loader",
            "nss",
        )
        if conanfile.name in allowlist:
            out.info("'{}' is part of the allowlist, skipping.".format(conanfile.name))
            return

        default_options = getattr(conanfile, "default_options")
        if default_options and isinstance(default_options, dict) and default_options.get("shared") is True:
            out.error("The option 'shared' must be 'False' by default. Update 'default_options'.")

    @run_test("KB-H056", output)
    def test(out):
        if str(conanfile.license).lower() in ["public domain", "public-domain", "public_domain"]:
            out.error("Public Domain is not a SPDX license. Use 'Unlicense' instead.")


@raise_if_error_output
def pre_source(output, conanfile, conanfile_path, **kwargs):
    conandata_source = os.path.join(os.path.dirname(conanfile_path), "conandata.yml")
    conanfile_content = tools.load(conanfile_path)

    @run_test("KB-H010", output)
    def test(out):
        if conanfile.version == "system":
            return
        if not os.path.exists(conandata_source):
            out.error("Create a file 'conandata.yml' file with the sources "
                      "to be downloaded.")

        if "def source(self):" in conanfile_content:
            invalid_content = ["git checkout master", "git checkout devel", "git checkout develop"]
            if "git clone" in conanfile_content and "git checkout" in conanfile_content:
                fixed_sources = True
                for invalid in invalid_content:
                    if invalid in conanfile_content:
                        fixed_sources = False
                        break
            else:
                fixed_sources = True
                if ('**self.conan_data["sources"]' not in conanfile_content and
                    'tools.get' not in conanfile_content) and \
                   ('self.conan_data["sources"]' not in conanfile_content and
                    'tools.download' not in conanfile_content):
                    fixed_sources = False

            if not fixed_sources:
                out.error("Use 'tools.get(**self.conan_data[\"sources\"][\"XXXXX\"])' "
                          "in the source() method to get the sources.")


@raise_if_error_output
def post_source(output, conanfile, conanfile_path, **kwargs):

    def _is_pure_c():
        if not _is_recipe_header_only(conanfile):
            cpp_extensions = ["cc", "c++", "cpp", "cxx", "c++m", "cppm", "cxxm", "h++", "hh", "hxx", "hpp"]
            c_extensions = ["c", "h"]
            return not _get_files_with_extensions(conanfile.source_folder, cpp_extensions) and \
                       _get_files_with_extensions(conanfile.source_folder, c_extensions)

    @run_test("KB-H011", output)
    def test(out):
        if _is_pure_c():
            conanfile_content = tools.load(conanfile_path)
            low = conanfile_content.lower()

            if conanfile.settings.get_safe("compiler") and "del self.settings.compiler.libcxx" not in low:
                out.error("Can't detect C++ source files but recipe does not remove "
                          "'self.settings.compiler.libcxx'")

    @run_test("KB-H022", output)
    def test(out):
        if _is_pure_c():
            conanfile_content = tools.load(conanfile_path)
            low = conanfile_content.lower()
            if conanfile.settings.get_safe("compiler") and "del self.settings.compiler.cppstd" not in low:
                out.error("Can't detect C++ source files but recipe does not remove "
                          "'self.settings.compiler.cppstd'")

    @run_test("KB-H066", output)
    def test(out):
        _check_short_paths(conanfile_path, conanfile.source_folder, 120, out)


@raise_if_error_output
def pre_build(output, conanfile, **kwargs):

    @run_test("KB-H007", output)
    def test(out):
        has_fpic = conanfile.options.get_safe("fPIC")
        error = False
        if conanfile.settings.get_safe("os") == "Windows" and has_fpic:
            out.error("'fPIC' option not managed correctly. Please remove it for Windows "
                      "configurations: del self.options.fPIC")
            error = True
        if has_fpic and conanfile.options.get_safe("shared"):
            out.error("'fPIC' option not managed correctly. Please remove it for shared "
                      "option: del self.options.fPIC")
            error = True
        elif has_fpic and not error:
            out.success("OK. 'fPIC' option found and apparently well managed")
        else:
            out.info("'fPIC' option not found")


@raise_if_error_output
def post_package(output, conanfile, conanfile_path, **kwargs):
    this.reference = str(conanfile)
    @run_test("KB-H012", output)
    def test(out):
        if conanfile.version == "system":
            return
        licenses_folder = os.path.join(os.path.join(conanfile.package_folder, "licenses"))
        if not os.path.exists(licenses_folder):
            out.error("No 'licenses' folder found in package: %s " % conanfile.package_folder)
            return
        licenses = []
        for root, dirnames, filenames in os.walk(licenses_folder):
            for filename in filenames:
                licenses.append(filename)
        if not licenses:
            out.error("Not known valid licenses files "
                      "found at: %s\n"
                      "Files: %s" % (licenses_folder, ", ".join(licenses)))

    @run_test("KB-H013", output)
    def test(out):
        if conanfile.name in ["cmake", "android-ndk", "zulu-openjdk", "mingw-w64", "mingw-builds",
                              "openjdk", "mono"]:
            return

        base_known_folders = ["lib", "bin", "include", "res", "licenses"]
        known_folders = {
            'icu': base_known_folders + ['config', ]
        }.get(conanfile.name, base_known_folders)

        for filename in os.listdir(conanfile.package_folder):
            if os.path.isdir(os.path.join(conanfile.package_folder, filename)):
                if filename not in known_folders:
                    out.error("Unknown folder '{}' in the package".format(filename))
            else:
                if filename not in ["conaninfo.txt", "conanmanifest.txt", "licenses"]:
                    out.error("Unknown file '{}' in the package".format(filename))
        if out.failed:
            out.info("If you are trying to package a tool put all the contents under the 'bin' folder")

    @run_test("KB-H014", output)
    def test(out):
        if conanfile.version == "system":
            return

        # INFO: allowlist for package names
        if conanfile.name in [
            "autoconf",
            "autoconf-archive",
            "automake",
            "cccl",
            "extra-cmake-modules",
            "gnu-config",
            "gtk-doc-stub",
            "ms-gsl",
            "poppler-data",
            "wayland-protocols",
            "xorg-cf-files",
            "xorg-macros",
            "opentelemetry-proto",
            "create-dmg",
            "googleapis",
            "grpc-proto",
        ]:
            return
        if not _files_match_settings(conanfile, conanfile.package_folder, out):
            out.error("Packaged artifacts does not match the settings used: os=%s, compiler=%s"
                      % (_get_os(conanfile), conanfile.settings.get_safe("compiler")))

    @run_test("KB-H015", output)
    def test(out):
        if not _shared_files_well_managed(conanfile, conanfile.package_folder):
            out.error("Package with 'shared' option did not contains any shared artifact")

    @run_test("KB-H020", output)
    def test(out):
        if conanfile.name in ["cmake", "msys2", "strawberryperl", "android-ndk", "emsdk"]:
            return
        bad_files = _get_files_following_patterns(conanfile.package_folder, ["*.pc"])
        if bad_files:
            out.error("The conan-center repository doesn't allow the packages to contain `pc` "
                      "files. The packages have to "
                      "be located using generators and the declared `cpp_info` information")
            out.error("Found files: {}".format("; ".join(bad_files)))

    @run_test("KB-H016", output)
    def test(out):
        if conanfile.name in ["cmake", "msys2", "strawberryperl", "pybind11", "ignition-cmake",
                              "extra-cmake-modules", "emsdk"]:
            return
        bad_files = _get_files_following_patterns(conanfile.package_folder, ["Find*.cmake",
                                                                             "*Config.cmake",
                                                                             "*-config.cmake"])
        if bad_files:
            out.error("The conan-center repository doesn't allow the packages to contain CMake "
                      "find modules or config files. The packages have to "
                      "be located using generators and the declared `cpp_info` information")

            out.error("Found files: {}".format("; ".join(bad_files)))

    @run_test("KB-H017", output)
    def test(out):
        bad_files = _get_files_following_patterns(conanfile.package_folder, ["*.pdb"])
        if bad_files:
            out.error("The conan-center repository doesn't allow PDB files")
            out.error("Found files: {}".format("; ".join(bad_files)))

    @run_test("KB-H018", output)
    def test(out):
        bad_files = _get_files_following_patterns(conanfile.package_folder, ["*.la"])
        if bad_files:
            out.error("Libtool files found (*.la). Do not package *.la files "
                      "but library files (.a) ")
            out.error("Found files: {}".format("; ".join(bad_files)))

    @run_test("KB-H021", output)
    def test(out):
        if conanfile.name in ["powershell", "android-ndk", "emsdk"]:
            return
        bad_files = _get_files_following_patterns(conanfile.package_folder,
                                                  ["msvcr*.dll", "msvcp*.dll", "vcruntime*.dll", "concrt*.dll"])
        if bad_files:
            out.error("The conan-center repository doesn't allow Microsoft Visual Studio runtime files.")
            out.error("Found files: {}".format("; ".join(bad_files)))

    @run_test("KB-H066", output)
    def test(out):
        _check_short_paths(conanfile_path, conanfile.package_folder, 160, out)

    @run_test("KB-H043", output)
    def test(out):
        dict_deplibs_libs = _deplibs_from_shlibs(conanfile, out)
        all_system_libs = _all_system_libs(_get_os(conanfile))

        needed_system_libs = set(dict_deplibs_libs.keys()).intersection(all_system_libs)

        if _get_os(conanfile) == "Macos":
            deps_system_libs = set(conanfile.deps_cpp_info.frameworks)
        else:
            deps_system_libs = set(conanfile.deps_cpp_info.system_libs)

        conanfile_system_libs = set(m.group(2) for m in re.finditer(r"""(["'])([a-zA-Z0-9._-]+)(\1)""", tools.load(conanfile_path))).intersection(all_system_libs)

        missing_system_libs = needed_system_libs.difference(deps_system_libs.union(conanfile_system_libs))

        attribute = 'frameworks' if _get_os(conanfile) == "Macos" else 'system_libs'
        for missing_system_lib in missing_system_libs:
            libs = dict_deplibs_libs[missing_system_lib]
            for lib in libs:
                out.warn("Library '{}' links to system library '{}' but it is not in cpp_info.{}.".format(lib, missing_system_lib, attribute))


@raise_if_error_output
def post_package_info(output, conanfile, reference, **kwargs):
    if not hasattr(this, "reference") or str(reference) != this.reference:
        return

    @run_test("KB-H019", output)
    def test(out):
        if conanfile.name in ["android-ndk", "cmake", "msys2", "strawberryperl"]:
            return
        bad_files = _get_files_following_patterns(conanfile.package_folder, ["*.cmake"])
        build_dirs = {bd.replace("\\", "/") for bd in conanfile.cpp_info.build_paths}
        for component in conanfile.cpp_info.components.values():
            build_dirs.update({bd.replace("\\", "/") for bd in component.build_paths})
        files_missplaced = []

        build_modules = []
        if isinstance(conanfile.cpp_info.build_modules, dict):
            build_modules.extend(conanfile.cpp_info.build_modules["cmake_find_package"])
            build_modules.extend(conanfile.cpp_info.build_modules["cmake_find_package_multi"])
        else:
            out.warn("cpp_info.build_modules is not a dictionary")
        for component_name, component in conanfile.cpp_info.components.items():
            if isinstance(component.build_modules, dict):
                build_modules.extend(component.build_modules["cmake_find_package"])
                build_modules.extend(component.build_modules["cmake_find_package_multi"])
            else:
                out.warn('cpp_info.components["%s"].build_modules is not a dictionary' % component_name)
        build_modules = [bm.replace("\\", "/") for bm in build_modules]

        for filename in bad_files:
            if any(os.path.samefile(filename, module) for module in build_modules):
                continue
            for bdir in build_dirs:
                bdir = os.path.relpath(bdir, conanfile.package_folder)
                bdir = bdir.replace("\\", "/")
                bdir = "" if bdir == "." else bdir
                bdir = "./{}".format(bdir)
                # https://github.com/conan-io/conan/issues/5401
                if bdir == "./":
                    if os.path.dirname(filename) == ".":
                        break
                elif os.path.commonprefix([bdir, filename]) == bdir:
                    break
            else:
                files_missplaced.append(filename)

        if files_missplaced:
            out.warn("The *.cmake files have to be placed in a folder declared as "
                     "`cpp_info.builddirs`. Currently folders declared: {}".format(build_dirs))
            out.warn("Found files: {}".format("; ".join(files_missplaced)))

    @run_test("KB-H054", output)
    def test(out):
        def _test_component(component):
            libs_to_search = list(component.libs)
            for p in component.libdirs:
                if not os.path.isdir(p):
                    continue
                libs_found = tools.collect_libs(conanfile, p)
                libs_to_search = [l for l in libs_to_search if l not in libs_found]
                libs_to_search = [l for l in libs_to_search if not os.path.isfile(os.path.join(p, l))]
            for l in libs_to_search:
                out.error(f"Component {conanfile.name}::{component.name} library '{l}' is listed in the recipe, "
                           "but not found installed at self.cpp_info.libdirs. Make sure you compiled the library correctly. If so, then the library name should probably be fixed. Otherwise, then the component should be removed.")

        if not conanfile.cpp_info.components:
            _test_component(conanfile.cpp_info)
        for c in conanfile.cpp_info.components:
            _test_component(conanfile.cpp_info.components[c])

    @run_test("KB-H071", output)
    def test(out):
        def _test_component(component):
            for d in component.includedirs:
                if not os.path.isdir(d):
                    out.error(f"Component {conanfile.name}::{component.name} include dir '{d}' is listed in the recipe, "
                               "but not found in package folder. The include dir should probably be fixed or removed.")
        if not conanfile.cpp_info.components:
            _test_component(conanfile.cpp_info)
        for c in conanfile.cpp_info.components:
            _test_component(conanfile.cpp_info.components[c])


def _get_files_following_patterns(folder, patterns):
    ret = []
    with tools.chdir(folder):
        for (root, _, filenames) in os.walk("."):
            for filename in filenames:
                for pattern in patterns:
                    if fnmatch.fnmatch(filename, pattern):
                        ret.append(os.path.join(root, filename).replace("\\", "/"))
    return sorted(ret)


def _get_files_with_extensions(folder, extensions):
    files = []
    with tools.chdir(folder):
        for (root, _, filenames) in os.walk("."):
            for filename in filenames:
                for ext in [ext for ext in extensions if ext != ""]:
                    if filename.endswith(".%s" % ext):
                        files.append(os.path.join(root, filename))
                    # Look for possible executables
                    elif ("" in extensions and "." not in filename
                          and not filename.endswith(".") and "license" not in filename.lower()):
                        files.append(os.path.join(root, filename))
    return files


def _shared_files_well_managed(conanfile, folder):
    shared_extensions = ["dll", "so", "dylib"]
    shared_name = "shared"
    try:
        options_dict = {key: value for key, value in conanfile.options.values.as_list()}
    except Exception:
        options_dict = {key: value for key, value in conanfile.options.items()}
    if shared_name in options_dict.keys() and options_dict[shared_name] == "True":
        if not _get_files_with_extensions(folder, shared_extensions):
            return False
    return True


def _files_match_settings(conanfile, folder, output):
    header_extensions = ["h", "h++", "hh", "hxx", "hpp"]
    visual_extensions = ["lib", "dll", "exe", "bat"]
    mingw_extensions = ["a", "lib", "a.dll", "dll", "exe", "sh"]
    # The "" extension is allowed to look for possible executables
    linux_extensions = ["a", "so", "sh", ""]
    freebsd_extensions = ["a", "so", "sh", ""]
    macos_extensions = ["a", "dylib", ""]

    has_header = _get_files_with_extensions(folder, header_extensions)
    has_visual = _get_files_with_extensions(folder, visual_extensions)
    has_mingw = _get_files_with_extensions(folder, mingw_extensions)
    has_linux = _get_files_with_extensions(folder, linux_extensions)
    has_freebsd = _get_files_with_extensions(folder, freebsd_extensions)
    has_macos = _get_files_with_extensions(folder, macos_extensions)
    settings_os = _get_os(conanfile)

    if not has_header and not has_visual and not has_mingw and not has_linux and not has_freebsd and not has_macos:
        output.error("Empty package")
        return False
    if _is_recipe_header_only(conanfile):
        if not has_header and (has_visual or has_mingw or has_linux or has_macos):
            output.error("Package for Header Only does not contain artifacts with these extensions: "
                         "%s" % header_extensions)
            return False
        else:
            return True
    if settings_os == "Windows":
        if conanfile.settings.get_safe("compiler") == "Visual Studio":
            if not has_visual:
                output.error("Package for Visual Studio does not contain artifacts with these "
                             "extensions: %s" % visual_extensions)
            return has_visual
        elif conanfile.settings.get_safe("compiler") == "gcc":
            if not has_mingw:
                output.error("Package for MinGW does not contain artifacts with these extensions: "
                             "%s" % mingw_extensions)
            return has_mingw
        else:
            return has_visual or has_mingw
    if settings_os == "Linux":
        if not has_linux:
            output.error("Package for Linux does not contain artifacts with these extensions: "
                         "%s" % linux_extensions)
        return has_linux
    if settings_os == "FreeBSD":
        if not has_freebsd:
            output.error("Package for FreeBSD does not contain artifacts with these extensions: "
                         "%s" % freebsd_extensions)
        return has_freebsd
    if settings_os == "Macos":
        if not has_macos:
            output.error("Package for Macos does not contain artifacts with these extensions: "
                         "%s" % macos_extensions)
        return has_macos
    if settings_os is None:
        if not has_header and (has_visual or has_mingw or has_linux or has_freebsd or has_macos):
            output.error("Package for Header Only does not contain artifacts with these extensions: "
                         "%s" % header_extensions)
            return False
        else:
            return True
    output.warn("OS %s might not be supported. Skipping..." % settings_os)
    return True


def _is_recipe_header_only(conanfile):
    without_settings = not bool(_get_settings(conanfile))
    package_id_method = getattr(conanfile, "package_id")
    header_only_id = "self.info.header_only()" in inspect.getsource(package_id_method)
    settings_clear = "self.info.settings.clear()" in inspect.getsource(package_id_method)
    info_clear = "self.info.clear()" in inspect.getsource(package_id_method)
    return header_only_id or without_settings or settings_clear or info_clear


def _get_settings(conanfile):
    settings = getattr(conanfile, "settings")
    if isinstance(settings, Settings):
        return None if not settings.values.fields else settings
    else:
        return settings


def _get_os(conanfile):
    settings = _get_settings(conanfile)
    if not settings:
        return None
    return settings.get_safe("os") or settings.get_safe("os_build")

def _skip_test_package(root, filename):
    filename = os.path.relpath(root, filename).replace("\\", "/")
    return filename.startswith("test_package/build") or filename.startswith("test_package/test_output")

def _check_short_paths(conanfile_path, folder_path, max_length_path, output):
    conanfile_content = tools.load(conanfile_path)
    if not re.search(r"(\s{4}|\t)short_paths\s*=", conanfile_content):
        windows_max_path = 256
        # INFO: Need to reserve around 160 characters for package folder path
        file_max_length_path = windows_max_path - max_length_path
        with tools.chdir(folder_path):
            for (root, _, filenames) in os.walk("."):
                for filename in filenames:
                    filepath = os.path.join(root, filename).replace("\\", "/")
                    if len(filepath) >= file_max_length_path:
                        output.warn(
                            f"The file '{filepath}' has a very long path and may exceed Windows max path length. "
                            "Add 'short_paths = True' in your recipe.")
                        break

def _get_compiler(conanfile):
    settings = _get_settings(conanfile)
    if not settings:
        return None
    return settings.get_safe("compiler")


def _all_system_libs(os_):
    if os_ == "Linux":
        return _GLIBC_LIBS
    elif os_ == "Windows":
        return _WIN32_LIBS
    else:
        return _OSX_LIBS


def _deplibs_from_shlibs(conanfile, out):
    deplibs = dict()
    os_ = _get_os(conanfile)
    shlext = {
        "Windows": "dll",
        "Macos": "dylib"
    }.get(os_, "so")
    libraries = _get_files_with_extensions(conanfile.package_folder, [shlext])
    if not libraries:
        return deplibs
    if os_ == "Linux" or tools.is_apple_os(os_) or _get_compiler(conanfile) not in ["Visual Studio", "msvc"]:
        objdump = tools.get_env("OBJDUMP") or tools.which("objdump")
        if not objdump:
            out.warn("objdump not found")
            return deplibs
        for library in libraries:
            if _get_os(conanfile) == "Windows":
                cmd = [objdump, "--section=.idata", "-x", library]
            else:
                cmd = [objdump, "-p", library]
            try:
                objdump_output = subprocess.check_output(cmd, cwd=conanfile.package_folder).decode()
            except subprocess.CalledProcessError:
                out.warn("Running objdump on '{}' failed. Is the environment variable OBJDUMP correctly configured?".format(library))
                continue
            if _get_os(conanfile) == "Windows":
                for dep_lib_match in re.finditer(r"DLL Name: (.*).dll", objdump_output, re.IGNORECASE):
                    dep_lib_base = dep_lib_match.group(1).lower()
                    deplibs.setdefault(dep_lib_base, []).append(library)
            elif _get_os(conanfile) == "Macos":
                load_commands = {}
                number = None
                for line in objdump_output.splitlines():
                    if line.startswith("Load command"):
                        tokens = line.split("Load command")
                        if len(tokens) == 2:
                            number = int(tokens[1])
                            load_commands[number] = dict()
                    elif number is not None:
                        line = line.strip()
                        tokens = line.split(None, 1)
                        if len(tokens) == 2:
                            load_commands[number][tokens[0]] = tokens[1]
                r = r"/System/Library/Frameworks/(.*)\.framework/Versions/(.*)/(.*) \(offset (.*)\)"
                r = re.compile(r)
                for load_command in load_commands.values():
                    if load_command.get("cmd") == "LC_LOAD_DYLIB":
                        name = load_command.get("name", '')
                        match = re.match(r, name)
                        if not match:
                            continue
                        deplibs.setdefault(match.group(1), []).append(library)
            else:
                dep_libs_fn = list(l.replace("NEEDED", "").strip() for l in objdump_output.splitlines() if "NEEDED" in l)
                for dep_lib_fn in dep_libs_fn:
                    dep_lib_match = re.match(r"lib(.*).{}(?:\.[0-9]+)*".format(shlext), dep_lib_fn)
                    if not dep_lib_match:
                        continue
                    deplibs.setdefault(dep_lib_match.group(1), []).append(library)
    elif _get_compiler(conanfile) in ["Visual Studio", "msvc"] or _get_os == "Windows":
        with tools.vcvars(conanfile):
            for library in libraries:
                try:
                    dumpbin_output = subprocess.check_output(["dumpbin", "-dependents", library], cwd=conanfile.package_folder).decode()
                except subprocess.CalledProcessError:
                    out.warn("Running dumpbin on '{}' failed.".format(library))
                    continue
                for l in re.finditer(r"([a-z0-9\-_]+)\.dll", dumpbin_output, re.IGNORECASE):
                    dep_lib_base = l.group(1).lower()
                    deplibs.setdefault(dep_lib_base, []).append(library)
    return deplibs


_GLIBC_LIBS = {
    "anl", "BrokenLocale", "crypt", "dl", "g", "m", "mvec", "nsl", "nss_compat", "nss_db", "nss_dns",
    "nss_files", "nss_hesiod", "pthread", "resolv", "rt", "thread_db", "util",
}

_WIN32_LIBS = {
    "aclui", "activeds", "adsiid", "advapi32", "advpack", "ahadmin", "amstrmid", "authz", "aux_ulib",
    "avifil32", "avrt", "bcrypt", "bhsupp", "bits", "bthprops", "cabinet", "certadm", "certidl",
    "certpoleng", "clfsmgmt", "clfsw32", "clusapi", "comctl32", "comdlg32", "comsvcs", "corguids",
    "correngine", "credui", "crypt32", "cryptnet", "cryptui", "cryptxml", "cscapi", "d2d1", "d3d10",
    "d3d10_1", "d3d11", "d3d8thk", "d3d9", "davclnt", "dbgeng", "dbghelp", "dciman32", "dhcpcsvc",
    "dhcpcsvc6", "dhcpsapi", "dinput8", "dmoguids", "dnsapi", "dpx", "drt", "drtprov", "drttransport",
    "dsound", "dsprop", "dsuiext", "dtchelp", "dwrite", "dxgi", "dxva2", "eappcfg", "eappprxy",
    "ehstorguids", "elscore", "esent", "evr", "evr_vista", "faultrep", "fci", "fdi", "fileextd", "fontsub",
    "format", "framedyd", "framedyn", "fwpuclnt", "fxsutility", "gdi32", "gdiplus", "gpedit", "gpmuuid",
    "hlink", "htmlhelp", "httpapi", "icm32", "icmui", "iepmapi", "imagehlp", "imgutil", "imm32",
    "infocardapi", "iphlpapi", "iprop", "irprops", "kernel32", "ksguid", "ksproxy", "ksuser", "ktmw32",
    "loadperf", "locationapi", "lz32", "magnification", "mapi32", "mbnapi_uuid", "mf", "mfplat",
    "mfplat_vista", "mfplay", "mfreadwrite", "mfuuid", "mf_vista", "mgmtapi", "mmc", "mpr", "mqoa", "mqrt",
    "msacm32", "mscms", "mscoree", "mscorsn", "msctfmonitor", "msdasc", "msdelta", "msdmo", "msdrm", "msi",
    "msimg32", "mspatchc", "dwmapi", "glu32", "iscsidsc", "mprapi", "msrating", "nmsupp", "prntvpt",
    "scarddlg", "sisbkup", "wdsbp", "mstask", "msvfw32", "mswsock", "msxml2", "msxml6", "mtx", "mtxdm",
    "muiload", "ncrypt", "ndfapi", "ndproxystub", "netapi32", "netsh", "newdev", "nmapi", "normaliz",
    "ntdsapi", "ntmsapi", "ntquery", "odbc32", "odbcbcp", "odbccp32", "ole32", "oleacc", "oleaut32", "oledb",
    "oledlg", "opengl32", "osptk", "p2p", "p2pgraph", "parser", "pathcch", "pdh", "photoacquireuid",
    "portabledeviceguids", "powrprof", "propsys", "psapi", "quartz", "qutil", "qwave", "rasapi32", "rasdlg",
    "resutils", "rpcns4", "rpcrt4", "rstrtmgr", "rtm", "rtutils", "sapi", "sas", "sbtsv", "scrnsave",
    "scrnsavw", "searchsdk", "secur32", "sensapi", "sensorsapi", "setupapi", "sfc", "shdocvw", "shell32",
    "shfolder", "shlwapi", "slc", "slcext", "slwga", "snmpapi", "sporder", "srclient", "sti", "strmiids",
    "strsafe", "structuredquery", "svcguid", "t2embed", "tapi32", "taskschd", "tbs", "tdh", "tlbref",
    "traffic", "transcodeimageuid", "tspubplugincom", "txfw32", "uiautomationcore", "urlmon", "user32",
    "userenv", "usp10", "uuid", "uxtheme", "vds_uuid", "version", "vfw32", "virtdisk", "vpccominterfaces",
    "vssapi", "vss_uuid", "vstorinterface", "wbemuuid", "wcmguid", "wdsclientapi", "wdsmc", "wdspxe",
    "wdstptc", "webservices", "wecapi", "wer", "wevtapi", "wiaguid", "winbio", "windowscodecs",
    "windowssideshowguids", "winfax", "winhttp", "wininet", "winmm", "winsatapi", "winscard", "winspool",
    "winstrm", "wintrust", "wlanapi", "wlanui", "wldap32", "wmcodecdspuuid", "wmdrmsdk", "wmiutils",
    "wmvcore", "workspaceax", "ws2_32", "wsbapp_uuid", "wscapi", "wsdapi", "wsmsvc", "wsnmp32", "wsock32",
    "wtsapi32", "wuguid", "xaswitch", "xinput", "xmllite", "xolehlp", "xpsprint",
}.difference({"kernel32", "user32", "gdi32", "winspool", "shell32", "ole32", "oleaut32", "uuid", "comdlg32", "advapi32"})

# /System/Library/Frameworks
_OSX_LIBS = {
    'AGL', 'AVFAudio', 'AVFoundation', 'AVKit', 'Accelerate', 'Accessibility', 'Accounts',
    'AdServices', 'AdSupport', 'AddressBook', 'AppKit', 'AppTrackingTransparency', 'AppleScriptKit',
    'AppleScriptObjC', 'ApplicationServices', 'AudioToolbox', 'AudioUnit', 'AudioVideoBridging',
    'AuthenticationServices', 'AutomaticAssessmentConfiguration', 'Automator', 'BackgroundTasks',
    'BusinessChat', 'CFNetwork', 'CalendarStore', 'CallKit', 'Carbon', 'ClassKit', 'CloudKit',
    'Cocoa', 'Collaboration', 'ColorSync', 'Combine', 'Contacts', 'ContactsUI', 'CoreAudio',
    'CoreAudioKit', 'CoreAudioTypes', 'CoreBluetooth', 'CoreData', 'CoreDisplay', 'CoreFoundation',
    'CoreGraphics', 'CoreHaptics', 'CoreImage', 'CoreLocation', 'CoreMIDI', 'CoreMIDIServer',
    'CoreML', 'CoreMedia', 'CoreMediaIO', 'CoreMotion', 'CoreServices', 'CoreSpotlight',
    'CoreTelephony', 'CoreText', 'CoreVideo', 'CoreWLAN', 'CryptoKit', 'CryptoTokenKit',
    'DVDPlayback', 'DeveloperToolsSupport', 'DeviceCheck', 'DirectoryService', 'DiscRecording',
    'DiscRecordingUI', 'DiskArbitration', 'DriverKit', 'EventKit', 'ExceptionHandling',
    'ExecutionPolicy', 'ExternalAccessory', 'FWAUserLib', 'FileProvider', 'FileProviderUI',
    'FinderSync', 'ForceFeedback', 'Foundation', 'GLKit', 'GLUT', 'GSS', 'GameController',
    'GameKit', 'GameplayKit', 'HIDDriverKit', 'Hypervisor', 'ICADevices', 'IMServicePlugIn',
    'IOBluetooth', 'IOBluetoothUI', 'IOKit', 'IOSurface', 'IOUSBHost', 'IdentityLookup',
    'ImageCaptureCore', 'ImageIO', 'InputMethodKit', 'InstallerPlugins', 'InstantMessage',
    'Intents', 'JavaNativeFoundation', 'JavaRuntimeSupport', 'JavaScriptCore', 'JavaVM', 'Kerberos',
    'Kernel', 'KernelManagement', 'LDAP', 'LatentSemanticMapping', 'LinkPresentation',
    'LocalAuthentication', 'MLCompute', 'MapKit', 'MediaAccessibility', 'MediaLibrary',
    'MediaPlayer', 'MediaToolbox', 'Message', 'Metal', 'MetalKit', 'MetalPerformanceShaders',
    'MetalPerformanceShadersGraph', 'MetricKit', 'ModelIO', 'MultipeerConnectivity',
    'NaturalLanguage', 'NearbyInteraction', 'NetFS', 'Network', 'NetworkExtension',
    'NetworkingDriverKit', 'NotificationCenter', 'OSAKit', 'OSLog', 'OpenAL', 'OpenCL',
    'OpenDirectory', 'OpenGL', 'PCIDriverKit', 'PCSC', 'PDFKit', 'ParavirtualizedGraphics',
    'PassKit', 'PencilKit', 'Photos', 'PhotosUI', 'PreferencePanes', 'PushKit', 'Python', 'QTKit',
    'Quartz', 'QuartzCore', 'QuickLook', 'QuickLookThumbnailing', 'RealityKit', 'ReplayKit', 'Ruby',
    'SafariServices', 'SceneKit', 'ScreenSaver', 'ScreenTime', 'ScriptingBridge', 'Security',
    'SecurityFoundation', 'SecurityInterface', 'SensorKit', 'ServiceManagement', 'Social',
    'SoundAnalysis', 'Speech', 'SpriteKit', 'StoreKit', 'SwiftUI', 'SyncServices', 'System',
    'SystemConfiguration', 'SystemExtensions', 'TWAIN', 'Tcl', 'Tk', 'UIKit', 'USBDriverKit',
    'UniformTypeIdentifiers', 'UserNotifications', 'UserNotificationsUI', 'VideoDecodeAcceleration',
    'VideoSubscriberAccount', 'VideoToolbox', 'Virtualization', 'Vision', 'WebKit', 'WidgetKit',
    '_AVKit_SwiftUI', '_AuthenticationServices_SwiftUI', '_MapKit_SwiftUI', '_QuickLook_SwiftUI',
    '_SceneKit_SwiftUI', '_SpriteKit_SwiftUI', '_StoreKit_SwiftUI', 'iTunesLibrary', 'vecLib',
    'vmnet'
}

def _load_conanfile(conanfile_path):
    python_requires = ConanPythonRequire(None, None)
    _, conanfile_obj = parse_conanfile(conanfile_path,
                                       python_requires=python_requires,
                                       generator_manager=None)
    return conanfile_obj
