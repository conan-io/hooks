import fnmatch
import inspect
import os
import re
from logging import WARNING, ERROR, INFO, DEBUG, NOTSET

import yaml
from conans import tools, Settings

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
             "KB-H040": "NO TARGET NAME",
             "KB-H041": "NO FINAL ENDLINE",
             "KB-H044": "NO REQUIRES.ADD()",
             "KB-H045": "DELETE OPTIONS",
             "KB-H046": "CMAKE VERBOSE MAKEFILE",
             "KB-H047": "NO ASCII CHARACTERS",
             "KB-H048": "CMAKE VERSION REQUIRED",
             "KB-H049": "CMAKE WINDOWS EXPORT ALL SYMBOLS",
             "KB-H050": "DEFAULT SHARED OPTION VALUE",
             "KB-H051": "DEFAULT OPTIONS AS DICTIONARY",
             "KB-H052": "CONFIG.YML HAS NEW VERSION",
             "KB-H053": "PRIVATE IMPORTS",
             "KB-H054": "LIBRARY DOES NOT EXIST"
             }


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
        self._output.warn(self._get_message(message))

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
            out.error("Exception raised from hook: {}".format(e))
            raise e

    return tmp


def load_yml(path):
    if os.path.isfile(path):
        return yaml.safe_load(tools.load(path))
    return None


@raise_if_error_output
def pre_export(output, conanfile, conanfile_path, reference, **kwargs):
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
        if reference.version != reference.version.lower():
            out.error("The library version has to be lowercase")

    @run_test("KB-H003", output)
    def test(out):
        def _message_attr(attributes, out_method):
            for field in attributes:
                field_value = getattr(conanfile, field, None)
                if not field_value:
                    out_method("Conanfile doesn't have '%s' attribute. " % field)

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
            if os.path.relpath(path, dir_path).replace("\\", "/").startswith("test_package/build"):
                # Discard any file in temp builds
                continue
            for files_it in files:
                file_path = os.path.join(path, files_it)
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
                       os.path.join("test_package", "build") not in root:
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
        if conanfile.name in ["libusb", "backward-cpp"] or conanfile.version == "system":
            out.info("'{}' is part of the allowlist.".format(conanfile.name))
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
        allowed_sources = ["url", "sha256", "sha1", "md5"]
        allowed_patches = ["patch_file", "base_path", "url", "sha256", "sha1", "md5"]

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

    @run_test("KB-H040", output)
    def test(out):
        if "self.cpp_info.name =" in conanfile_content:
            out.error("CCI uses the name of the package for cmake generator."
                      " Use 'cpp_info.names' instead.")

        for generator in ["cmake", "cmake_multi"]:
            if "self.cpp_info.names['{}']".format(generator) in conanfile_content or \
               'self.cpp_info.names["{}"]'.format(generator) in conanfile_content:
                out.error("CCI uses the name of the package for {0} generator. "
                          "Conanfile should not contain 'self.cpp_info.names['{0}']'. "
                          " Use 'cmake_find_package' and 'cmake_find_package_multi' instead.".format(generator))

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
            if os.path.relpath(root, export_folder_path).replace("\\", "/").startswith("test_package/build"):
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

    @run_test("KB-H047", output)
    def test(out):

        def _check_non_ascii(filename, content):
            import unicodedata
            for num, line in enumerate(content.splitlines(), 1):
                bad_chars = {num: char for num, char in enumerate(line, 1) if ord(char) >= 128}
                if bad_chars:
                    out.error("The file '{}' contains a non-ascii character at line ({})."
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

        _check_non_ascii("conanfile.py", conanfile_content)
        test_package_dir = os.path.join(os.path.dirname(conanfile_path), "test_package")
        test_package_path = os.path.join(test_package_dir, "conanfile.py")
        if os.path.exists(test_package_path):
            test_package_content = tools.load(test_package_path)
            _check_non_ascii("test_package/conanfile.py", test_package_content)

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

@raise_if_error_output
def post_export(output, conanfile, conanfile_path, reference, **kwargs):
    export_folder_path = os.path.dirname(conanfile_path)

    @run_test("KB-H031", output)
    def test(out):
        conandata_path = os.path.join(export_folder_path, "conandata.yml")
        version = conanfile.version

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
        if conanfile.name in ["opencl-icd-loader", "paho-mqtt-c", "tbb", "pdal"]:
            out.info("'{}' is part of the allowlist, skipping.".format(conanfile.name))
            return

        default_options = getattr(conanfile, "default_options")
        if default_options and isinstance(default_options, dict) and default_options.get("shared") is True:
            out.error("The option 'shared' must be 'False' by default. Update 'default_options'.")


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


@raise_if_error_output
def pre_build(output, conanfile, **kwargs):

    @run_test("KB-H007", output)
    def test(out):
        has_fpic = conanfile.options.get_safe("fPIC")
        if conanfile.settings.get_safe("os") == "Windows" and has_fpic:
            out.error("'fPIC' option not managed correctly. Please remove it for Windows "
                      "configurations: del self.options.fpic")
        elif has_fpic:
            out.success("OK. 'fPIC' option found and apparently well managed")
        else:
            out.info("'fPIC' option not found")


@raise_if_error_output
def post_package(output, conanfile, conanfile_path, **kwargs):
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
        if conanfile.name in ["cmake", "android-ndk"]:
            return
        known_folders = ["lib", "bin", "include", "res", "licenses"]
        for filename in os.listdir(conanfile.package_folder):
            if os.path.isdir(os.path.join(conanfile.package_folder, filename)):
                if filename not in known_folders:
                    out.error("Unknown folder '{}' in the package".format(filename))
            else:
                if filename not in ["conaninfo.txt", "conanmanifest.txt", "licenses"]:
                    out.error("Unknown file '{}' in the package".format(filename))
        if out.failed:
            out.info("If you are trying to package a tool put all the contents under the 'bin' "
                     "folder")

    @run_test("KB-H014", output)
    def test(out):
        if conanfile.version == "system":
            return

        # INFO: Whitelist for package names
        if conanfile.name in ["ms-gsl", "cccl", "poppler-data", "extra-cmake-modules", "gnu-config", "autoconf", "automake"]:
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
        if conanfile.name in ["cmake", "msys2", "strawberryperl", "android-ndk"]:
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
                              "extra-cmake-modules"]:
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
        bad_files = _get_files_following_patterns(conanfile.package_folder,
                                                  ["msvcr*.dll", "msvcp*.dll", "vcruntime*.dll", "concrt*.dll"])
        if bad_files:
            out.error("The conan-center repository doesn't allow Microsoft Visual Studio runtime files.")
            out.error("Found files: {}".format("; ".join(bad_files)))


def post_package_info(output, conanfile, reference, **kwargs):

    @run_test("KB-H019", output)
    def test(out):
        if conanfile.name in ["android-ndk", "cmake", "msys2", "strawberryperl"]:
            return
        bad_files = _get_files_following_patterns(conanfile.package_folder, ["*.cmake"])
        build_dirs = [bd.replace("\\", "/") for bd in conanfile.cpp_info.builddirs]
        for component in conanfile.cpp_info.components.values():
            build_dirs.extend([bd.replace("\\", "/") for bd in component.builddirs])
        files_missplaced = []

        for filename in bad_files:
            for bdir in build_dirs:
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
            out.error("The *.cmake files have to be placed in a folder declared as "
                      "`cpp_info.builddirs`. Currently folders declared: {}".format(build_dirs))
            out.error("Found files: {}".format("; ".join(files_missplaced)))


    @run_test("KB-H054", output)
    def test(out):
        def _test_component(component):
            libs_to_search = component.libs.copy()
            for p in component.libdirs:
                libs_found = tools.collect_libs(conanfile, p)
                if not libs_found:
                    out.warn("Component %s::%s libdir \"%s\" does not contain any library" % (conanfile.name, component.name, p))
                libs_declared_and_found = [l for l in libs_found if l in libs_to_search]
                if not libs_declared_and_found:
                    out.warn("Component %s::%s libdir \"%s\" does not contain any declared library" % (conanfile.name, component.name, p))
                for l in libs_declared_and_found:
                    libs_to_search.remove(l)
            for l in libs_to_search:
                out.error("Component %s::%s library \"%s\" not found in libdirs" % (conanfile.name, component.name, l))

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
    options_dict = {key: value for key, value in conanfile.options.values.as_list()}
    if shared_name in options_dict.keys() and options_dict[shared_name] == "True":
        if not _get_files_with_extensions(folder, shared_extensions):
            return False
    return True


def _files_match_settings(conanfile, folder, output):
    header_extensions = ["h", "h++", "hh", "hxx", "hpp"]
    visual_extensions = ["lib", "dll", "exe", "bat"]
    mingw_extensions = ["a", "a.dll", "dll", "exe", "sh"]
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

    output.error("OS %s might not be supported" % settings_os)
    return False


def _is_recipe_header_only(conanfile):
    without_settings = not bool(_get_settings(conanfile))
    package_id_method = getattr(conanfile, "package_id")
    header_only_id = "self.info.header_only()" in inspect.getsource(package_id_method)
    settings_clear = "self.info.settings.clear()" in inspect.getsource(package_id_method)
    return header_only_id or without_settings or settings_clear


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
