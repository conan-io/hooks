import fnmatch
import inspect
import os
import re
import glob
import subprocess
import shutil
import platform
from io import StringIO

from logging import WARNING, ERROR, INFO, DEBUG, NOTSET

import yaml
from conans.util.runners import check_output_runner

from conan.tools.files import load, chdir, collect_libs
from conan.tools.apple import is_apple_os
from conan.tools.microsoft import is_msvc, VCVars


try:
    from conans import Settings
except ImportError:
    from conans.model.settings import Settings

kb_errors = {"KB-H001": "RECIPE METADATA",
             "KB-H002": "RECIPE REFERENCE",
             "KB-H003": "HEADER_ONLY, NO COPY SOURCE",
             "KB-H004": "FPIC OPTION",
             "KB-H005": "FPIC MANAGEMENT",
             "KB-H006": "RECIPE FOLDER SIZE",
             "KB-H007": "IMMUTABLE SOURCES",
             "KB-H008": "PURE-C MANAGEMENT",
             "KB-H009": "PACKAGE LICENSE",
             "KB-H010": "DEFAULT PACKAGE LAYOUT",
             "KB-H011": "MATCHING CONFIGURATION",
             "KB-H012": "NOT ALLOWED CONFIG-FILES",
             "KB-H013": "METADATA FILES",
             "KB-H014": "CMAKE FILE NOT IN BUILD FOLDERS",
             "KB-H015": "EXPORT LICENSE",
             "KB-H016": "TEST PACKAGE FOLDER",
             "KB-H017": "META LINES",
             "KB-H018": "CONANDATA.YML FORMAT",
             "KB-H019": "SYSTEM REQUIREMENTS",
             "KB-H020": "NOT ALLOWED ATTRIBUTES",
             "KB-H021": "MISSING SYSTEM LIBS",
             "KB-H022": "CMAKEFILE LINT",
             "KB-H023": "DEFAULT SHARED OPTION VALUE",
             "KB-H024": "CONFIG.YML HAS NEW VERSION",
             "KB-H025": "LIBRARY DOES NOT EXIST",
             "KB-H026": "SINGLE REQUIRES",
             "KB-H027": "TOOLS RENAME",
             "KB-H028": "FILE CONSISTENCY",
             "KB-H029": "SHORT_PATHS USAGE",
             "KB-H030": "TEST PACKAGE - NO DEFAULT OPTIONS",
             "KB-H031": "MANDATORY SETTINGS",
             "KB-H032": "INCLUDE PATH DOES NOT EXIST",
             "KB-H033": "REQUIREMENT OVERRIDE PARAMETER",
             "KB-H034": "APPLE RELOCATABLE SHARED LIBS",
             }


class _HooksOutputErrorCollector(object):

    def __init__(self, conanfile, output, kb_id=None):
        self._conanfile = conanfile
        self._output = output
        self._error = False
        self._test_name = kb_errors[kb_id] if kb_id else ""
        self.kb_id = kb_id
        if self.kb_id:
            self.kb_url = kb_url(self.kb_id)
        # FIXME: Move it to conf file. For now, we can not retrieve conf as external method
        # conf_hook_level = conanfile.conf.get("hooks.conan_center:error_level", check_type=str) or ""
        conf_hook_level = os.getenv("CONAN_HOOK_ERROR_LEVEL", "")
        self._error_level = {
            "error": ERROR,
            "warning": WARNING,
            "warn": WARNING,
            "info": INFO,
            "debug": DEBUG,
        }.get(conf_hook_level.lower(), NOTSET)

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

    def warning(self, message):
        if self._error_level and self._error_level <= WARNING:
            self._error = True
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
    def wrapper(conanfile, *args, **kwargs):
        output = _HooksOutputErrorCollector(conanfile, conanfile.output)
        setattr(conanfile, "hook_output", output)
        ret = func(conanfile, *args, **kwargs)
        conanfile.hook_output.raise_if_error()
        return ret

    return wrapper


def kb_url(kb_id):
    return "https://github.com/conan-io/conan-center-index/blob/master/docs/error_knowledge_base.md#{}".format(kb_id)


def run_test(kb_id, conanfile):
    def tmp(func):
        out = _HooksOutputErrorCollector(conanfile, conanfile.hook_output, kb_id)
        try:
            ret = func(out)
            if not out.failed:
                out.success("OK")
            return ret
        except Exception as e:
            out.error("Exception raised from hook: {} (type={})".format(e, type(e).__name__))
            raise

    return tmp


def load_yml(conanfile, path):
    if os.path.isfile(path):
        return yaml.safe_load(load(conanfile, path))
    return None


@raise_if_error_output
def pre_export(conanfile):
    conanfile_path = os.path.join(conanfile.recipe_folder, "conanfile.py")
    conanfile_content = load(conanfile, conanfile_path)
    export_folder_path = os.path.dirname(conanfile_path)
    settings = _get_settings(conanfile)
    header_only = _is_recipe_header_only(conanfile)
    installer = settings is not None and "os_build" in settings and "arch_build" in settings

    @run_test("KB-H001", conanfile)
    def test(out):
        def _message_attr(attributes, out_method):
            for field in attributes:
                field_value = getattr(conanfile, field, None)
                if not field_value:
                    out_method(f"The mandatory attribute '{field}' is missing. Please, add it to the recipe.")

        _message_attr(["url", "license", "description", "homepage", "topics"], out.error)

        if getattr(conanfile, "author", None):
            out.error(f"Conanfile should not contain author attribute because all recipes are owned by the community. Please, remove it.")

        if str(conanfile.license).lower() in ["public domain", "public-domain", "public_domain"]:
            out.error("Public Domain is not a SPDX license. Please, check the correct license name")

        topics = getattr(conanfile, "topics", []) or []
        invalid_topics = ["conan", conanfile.name]
        for topic in topics:
            if topic in invalid_topics:
                out.warning(f"The topic '{topic}' is invalid and should be removed from topics attribute.")
            if topic != topic.lower():
                out.warning(f"The topic '{topic}' is invalid; even names and acronyms should be formatted entirely in lowercase.")

        url = getattr(conanfile, "url", None)
        if url and not url.startswith("https://github.com/conan-io/conan-center-index"):
            out.error("The attribute 'url' should point to: https://github.com/conan-io/conan-center-index")

    @run_test("KB-H002", conanfile)
    def test(out):
        if not re.search(r"\s{4}name\s*=", conanfile_content):
            out.error("The 'name' attribute should be declared with the package name.")

        for attribute in ["version", "user", "channel"]:
            if re.search(fr"\s\s\s\s{attribute}\s*=", conanfile_content):
                out.error(f"The attribute '{attribute}' should not be declared in the recipe. Please, remove it.")

    @run_test("KB-H003", conanfile)
    def test(out):
        no_copy_source = getattr(conanfile, "no_copy_source", None)
        if not settings and header_only and not no_copy_source:
            out.warning("This recipe is a header only library as it does not declare "
                     "'settings'. Please include 'no_copy_source' to avoid unnecessary copy steps")

    @run_test("KB-H004", conanfile)
    def test(out):
        options = getattr(conanfile, "options", None)
        if settings and options and not header_only and "fPIC" not in options and not installer:
            out.warning("This recipe does not include an 'fPIC' option. Make sure you are using the right casing")

    @run_test("KB-H006", conanfile)
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
        out.success(f"Total recipe size: {total_size_kb} KB")
        if total_size_kb > max_folder_size:
            out.error(f"The size of your recipe folder ({total_size_kb} KB) is larger than the maximum allowed"
                      " size ({max_folder_size}KB).")

    @run_test("KB-H015", conanfile)
    def test(out):
        for attr_it in ["exports", "exports_sources"]:
            exports = getattr(conanfile, attr_it, None)
            if exports is None:
                continue
            exports = [exports] if isinstance(exports, str) else exports
            for exports_it in exports:
                for license_it in ["copying", "license", "copyright"]:
                    if license_it in exports_it.lower():
                        out.error("The ConanCenterIndex does not allow exporting recipes. Instead, collect extract directly from source files.")

    @run_test("KB-H016", conanfile)
    def test(out):
        dir_path = os.path.dirname(conanfile_path)
        test_package_path = os.path.join(dir_path, "test_package")
        if not os.path.exists(test_package_path):
            out.error("There is no 'test_package' for this recipe")
        elif not os.path.exists(os.path.join(test_package_path, "conanfile.py")):
            out.error("There is no 'conanfile.py' in 'test_package' folder")

    @run_test("KB-H017", conanfile)
    def test(out):
        def _search_for_metaline(from_line, to_line, lines):
            for index in range(from_line, to_line):
                line_number = index + 1
                if "# -*- coding:" in lines[index] or \
                        "# coding=" in lines[index]:
                    out.error("PEP 263 (encoding) is not allowed in the conanfile. "
                              f"Remove the line {line_number}")
                if "#!" in lines[index]:
                    out.error("Shebang (#!) detected in your recipe. "
                              f"Remove the line {line_number}")
                if "# vim:" in lines[index]:
                    out.error("vim editor configuration detected in your recipe. "
                              f"Remove the line {line_number}")

        def _check_conanfile_content(content, path):
            patterns = [r'#\s*pylint\s*:\s*skip-file\s*', '#\s*pylint\s*:\s*disable-all\s*',
                        '#\s*pylint\s*:\s*disable=']
            for pattern in patterns:
                if re.search(pattern, content):
                    out.error(f"Pylint can not be skipped, remove '#pylint' line from '{path}'")

        conanfile_lines = conanfile_content.splitlines()
        first_lines_range = 5 if len(conanfile_lines) > 5 else len(conanfile_lines)
        _search_for_metaline(0, first_lines_range, conanfile_lines)

        last_lines_range = len(conanfile_lines) - 3 if len(conanfile_lines) > 8 else len(conanfile_lines)
        _search_for_metaline(last_lines_range, len(conanfile_lines), conanfile_lines)

        recipe_folder = os.path.dirname(conanfile_path)
        recipes = _get_files_following_patterns(conanfile, recipe_folder, [r"conanfile.py", ])
        for recipe in recipes:
            recipe_path = os.path.join(recipe_folder, recipe)
            recipe_content = load(conanfile, recipe_path)
            _check_conanfile_content(recipe_content, recipe_path)

    @run_test("KB-H019", conanfile)
    def test(out):
        if conanfile.version == "system":
            out.info("'system' versions are allowed to install system requirements.")
            return
        if "def system_requirements" in conanfile_content:
            out.error("The method 'system_requirements()' is not allowed for regular packages. Please, use only Conan packages to install system requirements.")
        if "system.package_manager" in conanfile_content:
            out.error("Installing system requirements using 'system.package_manager' is not allowed. Please, use only Conan packages to install system requirements.")

    @run_test("KB-H018", conanfile)
    def test(out):
        conandata_path = os.path.join(export_folder_path, "conandata.yml")
        version = conanfile.version
        allowed_first_level = ["sources", "patches"]
        allowed_sources = ["md5", "sha1", "sha256", "url"]
        allowed_patches = ["patch_file", "base_path", "url", "sha256", "sha1", "md5", "patch_type", "patch_source",
                           "patch_description"]
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

        conandata_yml = load_yml(conanfile, conandata_path)
        if not conandata_yml:
            return
        entries = _not_allowed_entries(list(conandata_yml.keys()), allowed_first_level)
        if entries:
            out.error(f"First level entries {entries} not allowed. Use only first level entries {allowed_first_level} in conandata.yml")

        google_source_regex = re.compile(r"https://\w+.googlesource.com/")

        for entry in conandata_yml:
            if entry in ['sources', 'patches']:
                if not isinstance(conandata_yml[entry], dict):
                    out.error(f"Expecting a dictionary with versions as keys under '{entry}' element")
                else:
                    versions = conandata_yml[entry].keys()
                    if any([not isinstance(it, str) for it in versions]):
                        out.error("Versions in conandata.yml should be strings. Add quotes around the numbers")

            def validate_one(e, name, allowed):
                not_allowed = _not_allowed_entries(e, allowed)
                if not_allowed:
                    out.error(f"Additional entries {not_allowed} not allowed in '{name}':'{version}' of conandata.yml")
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
                out.warning(f"Consider 'sha256' instead of {weak_checksums}. It's considerably more secure than others.")

    @run_test("KB-H020", conanfile)
    def test(out):
        search_attrs = ["build_policy", "upload_policy", "revision_mode", "package_id_embed_mode", "package_id_non_embed_mode", "package_id_unknown_mode"]
        forbidden_attrs = []
        for attr in search_attrs:
            if re.search(fr"\s{4}{attr}\s*=", conanfile_content):
                forbidden_attrs.append(attr)

        if forbidden_attrs:
            out.error(f"Some attributes are affecting the packaging behavior and are not allowed, please, remove them: '{forbidden_attrs}'")

    @run_test("KB-H022", conanfile)
    def test(out):
        dir_path = os.path.dirname(conanfile_path)
        for (root, _, filenames) in os.walk(dir_path):
            for filename in filenames:
                if filename.lower().startswith("cmake") and (filename.endswith(".txt") or filename.endswith(".cmake")):
                    cmake_path = os.path.join(root, filename)
                    cmake_content = load(conanfile, cmake_path).lower()
                    if "cmake_verbose_makefile" in cmake_content.lower():
                        out.error(f"The CMake definition 'set(CMAKE_VERBOSE_MAKEFILE ON)' is not allowed. Please, remove it from {cmake_path}.")
                    if re.search(r"cmake_minimum_required\(version [\"']?2", cmake_content):
                        out.error(f"The {cmake_path} requires CMake 3.15 at least. Update to 'cmake_minimum_required(VERSION 3.15)'.")
                    if "cmake_minimum_required" not in cmake_content:
                        out.error(f"The CMake file '{cmake_path}' must contain a minimum version "
                                  "declared at the beginning (e.g. cmake_minimum_required(VERSION 3.15))")

    @run_test("KB-H024", conanfile)
    def test(out):
        config_path = os.path.abspath(os.path.join(export_folder_path, os.path.pardir, "config.yml"))
        config_yml = load_yml(conanfile, config_path)

        conandata_path = os.path.join(export_folder_path, "conandata.yml")
        conandata_yml = load_yml(conanfile, conandata_path)

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
                out.error(f'The version "{version}" exists in "{conandata_path}" but not in "{config_path}", so it will not be built.'
                          f' Please update "{config_path}" to include newly added version "{version}".')

    @run_test("KB-H026", conanfile)
    def test(out):
        for prefix in ["", "build_", "tool_"]:
            if hasattr(conanfile, f"{prefix}requires") and \
                    callable(getattr(conanfile, f"{prefix}requirements", None)):
                out.error(f"Both '{prefix}requires' attribute and '{prefix}requirements()' method should not "
                          "be declared at same recipe.")

    @run_test("KB-H027", conanfile)
    def test(out):
        def _check_content(content, path):
            if "os.rename" in content:
                out.warning(f"The 'os.rename' in {path} may cause permission error on Windows."
                         " Use 'conan.tools.files.rename(self, src, dst)' instead.")
            elif "tools.rename(" in content and "tools.rename(self," not in content:
                out.warning(f"The 'tools.rename' in {path} is outdated and may cause permission error on Windows."
                         " Use 'conan.tools.files.rename(self, src, dst)' instead.")

        _check_content(conanfile_content, "conanfile.py")
        test_package_path = os.path.join(os.path.dirname(conanfile_path), "test_package", "conanfile.py")
        if os.path.exists(test_package_path):
            test_package_content = load(conanfile, test_package_path)
            _check_content(test_package_content, "test_package/conanfile.py")

    @run_test("KB-H028", conanfile)
    def test(out):
        ext_to_be_checked = [".cmake", ".conf", ".cfg", ".diff", ".md", ".patch", ".py", ".txt",
                             ".yml", ".am", ".xml", ".json", ".in", ".ac", ".tsx", ".tmx",
                             ".proto", ".capnp", ".c", ".cc", ".c++", ".cpp", ".cxx", ".c++m",
                             ".cppm", ".cxxm", ".h++", ".hh", ".hxx", ".hpp", ".qrc", ".pro",
                             ".build", ".s", ".asm"]
        files_noext = "Makefile", "GNUMakefile"
        disallowed_chars = '<>:"/\\|+?*%,; '
        recipe_folder = os.path.dirname(conanfile_path)
        for root, _, files in os.walk(recipe_folder):
            if _skip_test_package(root, recipe_folder):
                continue
            for file in files:
                if any(it in disallowed_chars for it in file):
                    out.error(f"The file '{file}' uses illegal characters ({disallowed_chars}) for its name. Please, rename that file.")
                if file.endswith("."):
                    out.error(f"The file '{file}' ends with a dot. Please, remove the dot from the end.")
            for filename in files:
                if not any(filename.lower().endswith(ext) for ext in ext_to_be_checked):
                    continue
                lines = open(os.path.join(root, filename), 'rb').readlines()
                if any(line.endswith(b'\r\n') for line in lines):
                    out.error(f"The file '{filename}' uses CRLF. Please, replace by LF to avoid errors with diff tools.")

        def _check_final_newline(path):
            try:
                last_char = load(conanfile, path)[-1]
            except (OSError, IndexError):
                return  # File is empty ==> ignore
            if last_char not in ("\n", "\r"):
                out.error(f"File '{path}' does not end with an endline. Please, add it to avoid issues with some diff tools.")

        for root, _, filenames in os.walk(export_folder_path):
            if _skip_test_package(root, export_folder_path):
                # Discard any file in temp builds
                continue
            for filename in filenames:
                _, fileext = os.path.splitext(filename)
                if filename in files_noext or fileext.lower() in ext_to_be_checked:
                    _check_final_newline(os.path.join(root, filename))

        config_yml = os.path.join(export_folder_path, os.path.pardir, "config.yml")
        if os.path.isfile(config_yml):
            _check_final_newline(config_yml)

    @run_test("KB-H030", conanfile)
    def test(out):
        test_package_path = os.path.join(os.path.dirname(conanfile_path), "test_package", "conanfile.py")
        if os.path.isfile(test_package_path):
            try:
                for attribute in ["default_options", "version", "name", "license", "author", "exports", "build_policy"]:
                    match = re.search(rf"\s{4}({attribute})\s*=", conanfile_content)
                    if match:
                        out.error(f"The attribute '{attribute}' is not allowed on test_package/conanfile.py, remove it.")
            except Exception as e:
                out.warning("Invalid conanfile: {}".format(e))

    @run_test("KB-H031", conanfile)
    def test(out):
        settings = getattr(conanfile, "settings", None)
        if settings:
            settings = settings if isinstance(settings, (list, tuple)) else [settings]
            missing = [x for x in ["os", "arch", "compiler", "build_type"] if x not in settings]
            if missing:
                out.warning(f"The values '{missing}' are missing on 'settings' attribute. Update settings with the missing "
                         "values and use 'package_id(self)' method to manage the package ID.")
        else:
            out.warning("No 'settings' detected in your conanfile.py. Please, be sure that your package is a header-only.")



    @run_test("KB-H033", conanfile)
    def test(out):
        for method in ["self.requires", "self.build_requires", "self.test_requires"]:
            pattern = method + r'self.requires\(.*override=True.*\)'
            match = re.search(pattern, conanfile_content)
            if match:
                out.error(f"{method}('package/version', override=True) is forbidden, do not force override parameter.")


@raise_if_error_output
def post_export(conanfile):

    @run_test("KB-H023", conanfile)
    def test(out):
        allowlist = (
            "glib",
            "libgphoto2",
            "moltenvk",
            "nss",
            "onetbb",
            "opencl-icd-loader",
            "paho-mqtt-c",
            "pdal",
            "tbb",
            "vulkan-loader",
        )
        if conanfile.name in allowlist:
            out.info(f"'{conanfile.name}' is part of the allowlist, skipping.")
            return

        default_options = getattr(conanfile, "default_options")
        if default_options and isinstance(default_options, dict) and default_options.get("shared") is True:
            out.error("The option 'shared' must be 'False' by default. Update 'default_options' to 'shared=False'.")




@raise_if_error_output
def pre_source(conanfile):
    conanfile_path = os.path.join(conanfile.recipe_folder, "conanfile.py")
    conandata_source = os.path.join(os.path.dirname(conanfile_path), "conandata.yml")
    conanfile_content = load(conanfile, conanfile_path)

    @run_test("KB-H007", conanfile)
    def test(out):
        if conanfile.version == "system":
            return
        if not os.path.exists(conandata_source):
            out.error("Create a file 'conandata.yml' file with the sources "
                      "to be downloaded.")

        if "def source(self):" in conanfile_content:
            for line in conanfile_content.splitlines():
                if line.strip().startswith("#"):
                    continue
                if "git clone" in line or "git checkout" in line:
                    out.error("Git commands not allowed in 'source()' method. Use the conan.tools.files.get() with self.conan_data instead.")
                    break

            if 'self.conan_data' not in conanfile_content and 'get(self' not in conanfile_content and 'download(self' not in conanfile_content:
                out.error("Use 'get(self, **self.conan_data[\"sources\"][\"XXXXX\"])' "
                          "in the source() method to get the sources.")


@raise_if_error_output
def post_source(conanfile):
    conanfile_path = os.path.join(conanfile.recipe_folder, "conanfile.py")

    def _is_pure_c():
        if not _is_recipe_header_only(conanfile):
            cpp_extensions = ["cc", "c++", "cpp", "cxx", "c++m", "cppm", "cxxm", "h++", "hh", "hxx", "hpp"]
            c_extensions = ["c", "h"]
            return not _get_files_with_extensions(conanfile, conanfile.source_folder, cpp_extensions) and \
                _get_files_with_extensions(conanfile, conanfile.source_folder, c_extensions)

    @run_test("KB-H008", conanfile)
    def test(out):
        if _is_pure_c():
            conanfile_content = load(conanfile, conanfile_path)
            low = conanfile_content.lower()

            if conanfile.settings.get_safe("compiler") and \
                    ("del self.settings.compiler.libcxx" not in low and
                     'self.settings.rm_safe("compiler.libcxx")' not in low and
                     "self.settings.rm_safe('compiler.libcxx')" not in low and
                     "self.settings.compiler.rm_safe('libcxx')" not in low and
                     'self.settings.compiler.rm_safe("libcxx")' not in low):
                out.error("Can't detect C++ source files but recipe does not remove "
                          "'self.settings.compiler.libcxx'")

            if conanfile.settings.get_safe("compiler") and \
                    ("del self.settings.compiler.cppstd" not in low and
                     'self.settings.rm_safe("compiler.cppstd")' not in low and
                     "self.settings.rm_safe('compiler.cppstd')" not in low and
                     'self.settings.compiler.rm_safe("cppstd")' not in low and
                     "self.settings.compiler.rm_safe('cppstd')" not in low):
                out.error("Can't detect C++ source files but recipe does not remove "
                          "'self.settings.compiler.cppstd'")

    @run_test("KB-H029", conanfile)
    def test(out):
        _check_short_paths(conanfile, conanfile_path, conanfile.source_folder, 120, out)


@raise_if_error_output
def pre_build(conanfile):
    @run_test("KB-H005", conanfile)
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
def post_package(conanfile):
    conanfile_path = os.path.join(conanfile.recipe_folder, "conanfile.py")

    @run_test("KB-H009", conanfile)
    def test(out):
        if conanfile.version == "system":
            return

        licenses_folder = os.path.join(os.path.join(conanfile.package_folder, "licenses"))
        if not os.path.exists(licenses_folder):
            out.error(f"No 'licenses' folder found in package folder: {conanfile.package_folder}")
            return

        if not os.listdir(licenses_folder):
            out.error(f"No license files found in the license folder: {licenses_folder}")
            return

        for root, dirnames, filenames in os.walk(licenses_folder):
            for filename in filenames:
                license_path = os.path.join(licenses_folder, filename)
                if os.stat(license_path).st_size == 0:
                    out.error(f"Empty license file found: {filename}")

    @run_test("KB-H010", conanfile)
    def test(out):
        if conanfile.name in ["cmake", "android-ndk", "zulu-openjdk", "mingw-w64", "mingw-builds",
                              "openjdk", "mono", "gcc", "mold"]:
            return

        base_known_folders = ["lib", "bin", "include", "res", "licenses", "metadata"]
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

    @run_test("KB-H011", conanfile)
    def test(out):
        if conanfile.version == "system":
            return

        if not _shared_files_well_managed(conanfile, conanfile.package_folder):
            out.error("Package with 'shared=True' option did not contain any shared artifact")

        if not _static_files_well_managed(conanfile, conanfile.package_folder):
            out.error("Package with 'shared=False' option did not contain any static artifact")

        (result, message) = _package_type_well_managed(conanfile, conanfile.package_folder)
        if not result:
            out.error(message)

        libs_both_static_shared = _get_libs_if_static_and_shared(conanfile)
        if libs_both_static_shared:
            out.error(f"Package contains both shared and static flavors of these libraries: {', '.join(libs_both_static_shared)}. Please, remove according the to shared option.")

        # INFO: allow list for package names
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
            out.error(f"Packaged artifacts does not match the settings used: os={_get_os(conanfile)}, compiler={conanfile.settings.get_safe('compiler')}")

    @run_test("KB-H020", conanfile)
    def test(out):
        allowlist = ["cmake", "msys2", "strawberryperl", "android-ndk", "pybind11", "emsdk", "ignition-cmake", "extra-cmake-modules"]
        forbidden_exts = ["Find*.cmake", "*Config.cmake", "*-config.cmake", "*.pc"]
        bad_files = _get_files_following_patterns(conanfile, conanfile.package_folder, forbidden_exts)
        if bad_files and conanfile.name not in allowlist:
            out.error("The CCI doesn't allow the packages to contain build configuration files."
                      " Please, remove all files from the package folder."
                      " In case these files are really required, declare them in `cpp_info` information")
            out.error("Found files: {}".format("; ".join(bad_files)))

    @run_test("KB-H013", conanfile)
    def test(out):
        if conanfile.name in ["powershell", "android-ndk", "emsdk"]:
            return

        for ext in ["*.pdb", "*.la", "msvcr*.dll", "msvcp*.dll", "vcruntime*.dll", "concrt*.dll"]:
            pdb_files = _get_files_following_patterns(conanfile, conanfile.package_folder, [ext])
            metadata_files = _get_files_following_patterns(conanfile, conanfile.package_metadata_folder, [ext])
            diff_files = [x for x in pdb_files if x not in metadata_files]
            if diff_files:
                out.error(f"Files '{ext}' are not allowed as part of the package. Found files: {diff_files}. Please, move those files to self.package_metadata_folder.")

    @run_test("KB-H029", conanfile)
    def test(out):
        _check_short_paths(conanfile, conanfile_path, conanfile.package_folder, 160, out)

    @run_test("KB-H021", conanfile)
    def test(out):
        # FIXME: Need check for false-positive when showing third-party dependencies instead
        dict_deplibs_libs = _deplibs_from_shlibs(conanfile, out)
        all_system_libs = _all_system_libs(_get_os(conanfile))

        needed_system_libs = set(dict_deplibs_libs.keys()).intersection(all_system_libs)

        if _get_os(conanfile) == "Macos":
            deps_system_libs = set(
                [frameworks for dep in conanfile.dependencies.values() for frameworks in dep.cpp_info.frameworks])
        else:
            deps_system_libs = set(
                [system_libs for dep in conanfile.dependencies.values() for system_libs in dep.cpp_info.system_libs])

        conanfile_system_libs = set(m.group(2) for m in re.finditer(r"""(["'])([a-zA-Z0-9._-]+)(\1)""",
                                                                    load(conanfile, conanfile_path))).intersection(
            all_system_libs)

        missing_system_libs = needed_system_libs.difference(deps_system_libs.union(conanfile_system_libs))

        attribute = 'frameworks' if _get_os(conanfile) == "Macos" else 'system_libs'
        for missing_system_lib in missing_system_libs:
            libs = dict_deplibs_libs[missing_system_lib]
            for lib in libs:
                out.warning(f"Library '{lib}' links to system library '{missing_system_lib}' but it is not in cpp_info.{attribute}.")

    @run_test("KB-H034", conanfile)
    def test(out):
        # TODO: Complex hook that could be simplified/revisited
        if not is_apple_os(conanfile):
            return
        not_relocatable_libs = _get_non_relocatable_shared_libs(conanfile)
        if not_relocatable_libs:
            out.warning(f"install_name dir of these shared libs is not @rpath: {', '.join(not_relocatable_libs)}")


@raise_if_error_output
def post_package_info(conanfile):

    @run_test("KB-H025", conanfile)
    def test(out):
        # TODO: Complex hook that could be simplified/revisited
        def _test_component(component):
            libs_to_search = list(component.libs)
            for p in component.libdirs:
                if not os.path.isdir(p):
                    continue
                libs_found = collect_libs(conanfile, p)
                libs_to_search = [l for l in libs_to_search if l not in libs_found]
                libs_to_search = [l for l in libs_to_search if not os.path.isfile(os.path.join(p, l))]
            for l in libs_to_search:
                out.error(f"Component {conanfile.name}::{component.name} library '{l}' is listed in the recipe, "
                          "but not found installed at self.cpp_info.libdirs. Make sure you compiled the library correctly. If so, then the library name should probably be fixed. Otherwise, then the component should be removed.")

        if not conanfile.cpp_info.components:
            _test_component(conanfile.cpp_info)
        for c in conanfile.cpp_info.components:
            _test_component(conanfile.cpp_info.components[c])

    @run_test("KB-H032", conanfile)
    def test(out):
        def _test_component(component):
            for d in component.includedirs:
                if not os.path.isdir(d):
                    component_name = component.name if hasattr(component, "name") else conanfile.name
                    out.error(
                        f"Component {conanfile.name}::{component_name} include dir '{d}' is listed in the recipe, "
                        "but not found in package folder. The include dir should probably be fixed or removed.")

        if not conanfile.cpp_info.components:
            _test_component(conanfile.cpp_info)
        for c in conanfile.cpp_info.components:
            _test_component(conanfile.cpp_info.components[c])


def _get_files_following_patterns(conanfile, folder, patterns):
    ret = []
    with chdir(conanfile, folder):
        for (root, _, filenames) in os.walk("."):
            for filename in filenames:
                for pattern in patterns:
                    if fnmatch.fnmatch(filename, pattern):
                        ret.append(os.path.join(root, filename).replace("\\", "/"))
    return sorted(ret)


def _get_files_with_extensions(conanfile, folder, extensions):
    files = []
    with chdir(conanfile, folder):
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
        if not _get_files_with_extensions(conanfile, folder, shared_extensions):
            return False

    package_type = getattr(conanfile, "package_type", None)
    if package_type and package_type in ["library", "shared-library"]:
            return False

    return True


def _static_files_well_managed(conanfile, folder):
    static_extensions = ["a", "lib"]
    shared_name = "shared"
    try:
        options_dict = {key: value for key, value in conanfile.options.values.as_list()}
    except Exception:
        options_dict = {key: value for key, value in conanfile.options.items()}
    if shared_name in options_dict.keys() and options_dict[shared_name] == "False":
        if not _get_files_with_extensions(conanfile, folder, static_extensions):
            return False
    return True


def _package_type_well_managed(conanfile, folder):
    shared_extensions = ["dll", "so", "dylib"]
    static_extensions = ["a", "lib"]
    package_type = getattr(conanfile, "package_type", None)
    if package_type:
        static_libs = _get_files_with_extensions(conanfile, folder, static_extensions)
        if static_libs and package_type not in ["library", "static-library"]:
            return False, f"Package type is '{package_type}' but contains static libraries: {', '.join(static_libs)}"
        shared_libs = _get_files_with_extensions(conanfile, folder, shared_extensions)
        if shared_libs and package_type not in ["library", "shared-library"]:
            return False, f"Package type is '{package_type}' but contains shared libraries: {', '.join(shared_libs)}"
    return True, None


def _get_libs_if_static_and_shared(conanfile):
    # TODO: to improve. We only check whether we can find the same lib name with a static or
    # shared extension. Therefore:
    #   - it can't check anything useful for cl like compilers (Visual Studio, clang-cl, Intel-cc) for the moment
    #   - it can't detect a bad packaging if static & shared flavors have different names
    static_extension = "a"
    import_lib_extension = "dll.a"
    shared_extensions = ["so", "dylib"]

    static_libs = set()
    shared_libs = set()

    libdirs = [os.path.join(conanfile.package_folder, libdir)
               for libdir in getattr(conanfile.cpp.package, "libdirs")]
    for libdir in libdirs:
        # Collect statib libs.
        # Pay attention to not pick up import libs while collecting static libs !
        static_libs.update([re.sub(fr"\.{static_extension}$", "", os.path.basename(p))
                            for p in glob.glob(os.path.join(libdir, f"*.{static_extension}"))
                            if not p.endswith(f".{import_lib_extension}")])

        # Collect shared libs and import libs
        for ext in shared_extensions + [import_lib_extension]:
            shared_libs.update([re.sub(fr"\.{ext}$", "", os.path.basename(p))
                                for p in glob.glob(os.path.join(libdir, f"*.{ext}"))])

    result = list(static_libs.intersection(shared_libs))
    result.sort()
    return result


def _files_match_settings(conanfile, folder, output):
    header_extensions = ["h", "h++", "hh", "hxx", "hpp"]
    visual_extensions = ["lib", "dll", "exe", "bat"]
    mingw_extensions = ["a", "lib", "a.dll", "dll", "exe", "sh"]
    # The "" extension is allowed to look for possible executables
    linux_extensions = ["a", "so", "sh", ""]
    freebsd_extensions = ["a", "so", "sh", ""]
    macos_extensions = ["a", "dylib", ""]

    has_header = _get_files_with_extensions(conanfile, folder, header_extensions)
    has_visual = _get_files_with_extensions(conanfile, folder, visual_extensions)
    has_mingw = _get_files_with_extensions(conanfile, folder, mingw_extensions)
    has_linux = _get_files_with_extensions(conanfile, folder, linux_extensions)
    has_freebsd = _get_files_with_extensions(conanfile, folder, freebsd_extensions)
    has_macos = _get_files_with_extensions(conanfile, folder, macos_extensions)
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
    output.warning("OS %s might not be supported. Skipping..." % settings_os)
    return True


def _is_recipe_header_only(conanfile):
    without_settings = not bool(_get_settings(conanfile))
    package_id_method = getattr(conanfile, "package_id") if hasattr(conanfile, "package_id") else None
    if package_id_method:
        header_only_id = "self.info.header_only()" in inspect.getsource(package_id_method)
        settings_clear = "self.info.settings.clear()" in inspect.getsource(package_id_method)
        info_clear = "self.info.clear()" in inspect.getsource(package_id_method)
        return header_only_id or without_settings or settings_clear or info_clear
    return without_settings


def _get_settings(conanfile):
    settings = getattr(conanfile, "settings")
    if isinstance(settings, Settings):
        return None if not settings.items() else settings
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


def _check_short_paths(conanfile, conanfile_path, folder_path, max_length_path, output):
    conanfile_content = load(conanfile, conanfile_path)
    if not re.search(r"(\s{4}|\t)short_paths\s*=", conanfile_content):
        windows_max_path = 256
        # INFO: Need to reserve around 160 characters for package folder path
        file_max_length_path = windows_max_path - max_length_path
        with chdir(conanfile, folder_path):
            for (root, _, filenames) in os.walk("."):
                for filename in filenames:
                    filepath = os.path.join(root, filename).replace("\\", "/")
                    if len(filepath) >= file_max_length_path:
                        output.warning(
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
    libraries = _get_files_with_extensions(conanfile, conanfile.package_folder, [shlext])
    if not libraries:
        return deplibs
    if os_ == "Linux" or is_apple_os(conanfile) or not is_msvc(conanfile):
        objdump = os.getenv("OBJDUMP") or shutil.which("objdump")
        if not objdump:
            out.warning("objdump not found")
            return deplibs
        for library in libraries:
            if _get_os(conanfile) == "Windows":
                cmd = [objdump, "--section=.idata", "-x", library]
            else:
                cmd = [objdump, "-p", library]
            try:
                objdump_output = subprocess.check_output(cmd, cwd=conanfile.package_folder).decode()
            except subprocess.CalledProcessError:
                out.warning(
                    "Running objdump on '{}' failed. Is the environment variable OBJDUMP correctly configured?".format(
                        library))
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
                dep_libs_fn = list(
                    l.replace("NEEDED", "").strip() for l in objdump_output.splitlines() if "NEEDED" in l)
                for dep_lib_fn in dep_libs_fn:
                    dep_lib_match = re.match(r"lib(.*).{}(?:\.[0-9]+)*".format(shlext), dep_lib_fn)
                    if not dep_lib_match:
                        continue
                    deplibs.setdefault(dep_lib_match.group(1), []).append(library)
    elif is_msvc(conanfile) or _get_os == "Windows":
        VCVars(conanfile).generate(scope=None)
        for library in libraries:
            try:
                buffer = StringIO()
                with chdir(conanfile, conanfile.package_folder):
                    conanfile.run(f"dumpbin -dependents {library}", buffer, env=["conanvcvars"])
                dumpbin_output = buffer.getvalue()
            except subprocess.CalledProcessError:
                out.warning("Running dumpbin on '{}' failed.".format(library))
                continue
            for l in re.finditer(r"([a-z0-9\-_]+)\.dll", dumpbin_output, re.IGNORECASE):
                dep_lib_base = l.group(1).lower()
                deplibs.setdefault(dep_lib_base, []).append(library)
    return deplibs


def _get_non_relocatable_shared_libs(conanfile):
    if platform.system() != "Darwin":
        return None

    bad_shared_libs = []

    libdirs = [os.path.join(conanfile.package_folder, libdir)
               for libdir in getattr(conanfile.cpp.package, "libdirs")]
    for libdir in libdirs:
        for dylib_path in glob.glob(os.path.join(libdir, "*.dylib")):
            command = f"otool -D {dylib_path}"
            install_name = check_output_runner(command).strip().split(":")[1].strip()
            install_name_dir = os.path.dirname(install_name)
            if install_name_dir != "@rpath":
                bad_shared_libs.append(os.path.basename(dylib_path))

    return bad_shared_libs


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
}.difference(
    {"kernel32", "user32", "gdi32", "winspool", "shell32", "ole32", "oleaut32", "uuid", "comdlg32", "advapi32"})

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