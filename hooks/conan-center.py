import fnmatch
import inspect
import re
import os
from collections import defaultdict

import yaml
from logging import WARNING, ERROR, INFO, DEBUG, NOTSET

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
             "KB-H027": "CONAN CENTER INDEX URL",
             "KB-H028": "CMAKE MINIMUM VERSION",
             "KB-H029": "TEST PACKAGE - RUN ENVIRONMENT",
             "KB-H030": "CONANDATA.YML FORMAT",
             "KB-H031": "CONANDATA.YML REDUCE",
             "KB-H033": "APPLE FRAMEWORK",
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
    return "https://github.com/conan-io/conan-center-index/wiki/Error-Knowledge-Base#{}".format(kb_id)


def run_test(kb_id, output):
    def tmp(func):
        out = _HooksOutputErrorCollector(output, kb_id)
        ret = func(out)
        if not out.failed:
            out.success("OK")
        return ret

    return tmp


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

        _message_attr(["url", "license", "description", "homepage"], out.error)
        _message_attr(["topics"], out.warn)

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
        vrange_match = re.compile(r'.*[\'"][a-zA-Z0-9_+.-]+\/\[.+\]@[a-zA-Z0-9_+.\/-]+[\'"].*')
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
            for index in range(from_line,to_line):
                line_number = index + 1
                if "# -*- coding:" in lines[index] or \
                   "# coding=" in lines[index]:
                    out.error("PEP 263 (encoding) is not allowed in the conanfile. " \
                              "Remove the line {}".format(line_number))
                if "#!" in lines[index]:
                    out.error("Shebang (#!) detected in your recipe. " \
                              "Remove the line {}".format(line_number))
                if "# vim:" in lines[index]:
                    out.error("vim editor configuration detected in your recipe. " \
                              "Remove the line {}".format(line_number))

        lines = conanfile_content.splitlines()
        first_lines_range = 5 if len(lines) > 5 else len(lines)
        _search_for_metaline(0, first_lines_range, lines)

        last_lines_range = len(lines) -3 if len(lines) > 8 else len(lines)
        _search_for_metaline(last_lines_range, len(lines), lines)

    @run_test("KB-H027", output)
    def test(out):
        url = getattr(conanfile, "url", None)
        if url and not url.startswith("https://github.com/conan-io/conan-center-index"):
            out.error("The attribute 'url' should point to: " \
                      "https://github.com/conan-io/conan-center-index")

    @run_test("KB-H028", output)
    def test(out):
        def _find_cmake_minimum(folder):
            for (root, _, filenames) in os.walk(folder):
                for filename in filenames:
                    if filename.lower().startswith("cmake") and \
                    (filename.endswith(".txt") or filename.endswith(".cmake")):
                        cmake_path = os.path.join(root, filename)
                        cmake_content = tools.load(cmake_path).lower()
                        if not "cmake_minimum_required(version" in cmake_content and \
                           not "cmake_minimum_required (version" in cmake_content:
                            file_path = os.path.join(os.path.relpath(root), filename)
                            out.error("The CMake file '%s' must contain a minimum version " \
                                      "declared (e.g. cmake_minimum_required(VERSION 3.1.2))" %
                                      file_path)

        dir_path = os.path.dirname(conanfile_path)
        _find_cmake_minimum(dir_path)

    @run_test("KB-H029", output)
    def test(out):
        test_package_path = os.path.join(export_folder_path, "test_package")
        if not os.path.exists(os.path.join(test_package_path, "conanfile.py")):
            return

        test_package_conanfile = tools.load(os.path.join(test_package_path, "conanfile.py"))
        if "RunEnvironment" in test_package_conanfile:
            out.error("The 'RunEnvironment()' build helper is no longer needed. "
                      "It has been integrated into the self.run(..., run_environment=True)")

    @run_test("KB-H033", output)
    def test(out):
        if "cpp_info.shared_link_flags" in conanfile_content and "-framework" in conanfile_content:
            out.error("Apple Frameworks should be packaged using 'self.cpp_info.frameworks'")

    @run_test("KB-H030", output)
    def test(out):
        conandata_path = os.path.join(export_folder_path, "conandata.yml")
        version = conanfile.version
        allowed_first_level = ["sources", "patches"]
        allowed_sources = ["url", "sha256"]
        allowed_patches = ["patch_file", "base_path", "url", "sha256"]

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

        if os.path.exists(conandata_path):
            conandata = tools.load(conandata_path)
            conandata_yml = yaml.safe_load(conandata)
            if not conandata_yml:
                return
            entries = _not_allowed_entries(list(conandata_yml.keys()), allowed_first_level)
            if entries:
                out.error("First level entries %s not allowed. Use only first level entries %s in "
                          "conandata.yml" % (entries, allowed_first_level))

            for entry in conandata_yml:
                if version not in conandata_yml[entry]:
                    continue
                for element in conandata_yml[entry][version]:
                    if entry == "patches":
                        entries = _not_allowed_entries(element, allowed_patches)
                        if entries:
                            out.error("Additional entries %s not allowed in 'patches':'%s' of "
                                      "conandata.yml" % (entries, version))
                            return
                    if entry == "sources":
                        entries = _not_allowed_entries(element, allowed_sources)
                        if entries:
                            out.error("Additional entry %s not allowed in 'sources':'%s' of "
                                      "conandata.yml" % (entries, version))
                            return


@raise_if_error_output
def post_export(output, conanfile, conanfile_path, reference, **kwargs):
    export_folder_path = os.path.dirname(conanfile_path)

    @run_test("KB-H031", output)
    def test(out):
        conandata_path = os.path.join(export_folder_path, "conandata.yml")
        version = conanfile.version

        if os.path.exists(conandata_path):
            conandata = tools.load(conandata_path)
            conandata_yml = yaml.safe_load(conandata)
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


@raise_if_error_output
def pre_source(output, conanfile, conanfile_path, **kwargs):
    conandata_source = os.path.join(os.path.dirname(conanfile_path), "conandata.yml")
    conanfile_content = tools.load(conanfile_path)

    @run_test("KB-H010", output)
    def test(out):
        if not os.path.exists(conandata_source):
            out.error("Create a file 'conandata.yml' file with the sources "
                      "to be downloaded.")

        if "def source(self):" in conanfile_content:
            needed_content = ['**self.conan_data["sources"]']
            invalid_content = ["git checkout master", "git checkout devel", "git checkout develop"]
            if "git clone" in conanfile_content and "git checkout" in conanfile_content:
                fixed_sources = True
                for invalid in invalid_content:
                    if invalid in conanfile_content:
                        fixed_sources = False
                        break
            else:
                fixed_sources = True
                for valid in needed_content:
                    if valid not in conanfile_content:
                        fixed_sources = False
                        break

            if not fixed_sources:
                out.error("Use 'tools.get(**self.conan_data[\"sources\"][\"XXXXX\"])' "
                          "in the source() method to get the sources.")


@raise_if_error_output
def post_source(output, conanfile, conanfile_path, **kwargs):

    def _is_pure_c():
        if not _is_recipe_header_only(conanfile):
            cpp_extensions = ["cc", "cpp", "cxx", "c++m", "cppm", "cxxm", "h++", "hh", "hxx", "hpp"]
            c_extensions = ["c", "h"]
            return not _get_files_with_extensions(conanfile.source_folder, cpp_extensions) and \
                   _get_files_with_extensions(conanfile.source_folder, c_extensions)

    @run_test("KB-H011", output)
    def test(out):
        if _is_pure_c():
            conanfile_content = tools.load(conanfile_path)
            low = conanfile_content.lower()

            if "del self.settings.compiler.libcxx" not in low:
                out.error("Can't detect C++ source files but recipe does not remove "
                          "'self.settings.compiler.libcxx'")

    @run_test("KB-H022", output)
    def test(out):
        if _is_pure_c():
            conanfile_content = tools.load(conanfile_path)
            low = conanfile_content.lower()
            if "del self.settings.compiler.cppstd" not in low:
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
        # INFO: Whitelist for package names
        if conanfile.name in ["ms-gsl", "cccl"]:
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
        if conanfile.name in ["cmake", "msys2", "strawberryperl"]:
            return
        bad_files = _get_files_following_patterns(conanfile.package_folder, ["*.pc"])
        if bad_files:
            out.error("The conan-center repository doesn't allow the packages to contain `pc` "
                      "files. The packages have to "
                      "be located using generators and the declared `cpp_info` information")
            out.error("Found files:\n{}".format("\n".join(bad_files)))

    @run_test("KB-H016", output)
    def test(out):
        if conanfile.name in ["cmake", "msys2", "strawberryperl"]:
            return
        bad_files = _get_files_following_patterns(conanfile.package_folder, ["Find*.cmake",
                                                                             "*Config.cmake",
                                                                             "*-config.cmake"])
        if bad_files:
            out.error("The conan-center repository doesn't allow the packages to contain CMake "
                      "find modules or config files. The packages have to "
                      "be located using generators and the declared `cpp_info` information")
            out.error("Found files:\n{}".format("\n".join(bad_files)))

    @run_test("KB-H017", output)
    def test(out):
        bad_files = _get_files_following_patterns(conanfile.package_folder, ["*.pdb"])
        if bad_files:
            out.error("The conan-center repository doesn't allow PDB files")
            out.error("Found files:\n{}".format("\n".join(bad_files)))

    @run_test("KB-H018", output)
    def test(out):
        bad_files = _get_files_following_patterns(conanfile.package_folder, ["*.la"])
        if bad_files:
            out.error("Libtool files found (*.la). Do not package *.la files "
                      "but library files (.a) ")
            out.error("Found files:\n{}".format("\n".join(bad_files)))

    @run_test("KB-H021", output)
    def test(out):
        bad_files = _get_files_following_patterns(conanfile.package_folder, ["msvcr*.dll", "msvcp*.dll", "vcruntime*.dll", "concrt*.dll"])
        if bad_files:
            out.error("The conan-center repository doesn't allow Microsoft Visual Studio runtime files.")
            out.error("Found files:\n{}".format("\n".join(bad_files)))

def post_package_info(output, conanfile, reference, **kwargs):

    @run_test("KB-H019", output)
    def test(out):
        if conanfile.name in ["cmake", "msys2", "strawberryperl"]:
            return
        bad_files = _get_files_following_patterns(conanfile.package_folder, ["*.cmake"])
        build_dirs = conanfile.cpp_info.builddirs
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
            out.error("Found files:\n{}".format("\n".join(files_missplaced)))


def _get_files_following_patterns(folder, patterns):
    ret = []
    with tools.chdir(folder):
        for (root, _, filenames) in os.walk("."):
            for filename in filenames:
                for pattern in patterns:
                    if fnmatch.fnmatch(filename, pattern):
                        ret.append(os.path.join(root, filename).replace("\\", "/"))
    return ret


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
    visual_extensions = ["lib", "dll", "exe"]
    mingw_extensions = ["a", "a.dll", "dll", "exe"]
    # The "" extension is allowed to look for possible executables
    linux_extensions = ["a", "so", ""]
    macos_extensions = ["a", "dylib", ""]

    has_header = _get_files_with_extensions(folder, header_extensions)
    has_visual = _get_files_with_extensions(folder, visual_extensions)
    has_mingw = _get_files_with_extensions(folder, mingw_extensions)
    has_linux = _get_files_with_extensions(folder, linux_extensions)
    has_macos = _get_files_with_extensions(folder, macos_extensions)
    os = _get_os(conanfile)

    if not has_header and not has_visual and not has_mingw and not has_linux and not has_macos:
        output.error("Empty package")
        return False
    if _is_recipe_header_only(conanfile):
        if not has_header and (has_visual or has_mingw or has_linux or has_macos):
            output.error("Package for Header Only does not contain artifacts with these extensions: "
                         "%s" % header_extensions)
            return False
        else:
            return True
    if os == "Windows":
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
    if os == "Linux":
        if not has_linux:
            output.error("Package for Linux does not contain artifacts with these extensions: "
                         "%s" % linux_extensions)
        return has_linux
    if os == "Macos":
        if not has_macos:
            output.error("Package for Macos does not contain artifacts with these extensions: "
                         "%s" % macos_extensions)
        return has_macos
    if os is None:
        if not has_header and (has_visual or has_mingw or has_linux or has_macos):
            output.error("Package for Header Only does not contain artifacts with these extensions: "
                         "%s" % header_extensions)
            return False
        else:
            return True
    return False


def _is_recipe_header_only(conanfile):
    without_settings = not bool(_get_settings(conanfile))
    package_id_method = getattr(conanfile, "package_id")
    header_only_id = "self.info.header_only()" in inspect.getsource(package_id_method)
    return header_only_id or without_settings


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
