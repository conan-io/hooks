import fnmatch
import inspect
import os
from logging import WARNING, ERROR, INFO, DEBUG, NOTSET

from conans import tools


class _HooksOutputErrorCollector(object):

    def __init__(self, output, test_name=None):
        self._output = output
        self._error = False
        self._test_name = test_name or ""
        self._error_level = int(os.getenv("CONAN_HOOK_ERROR_LEVEL", str(NOTSET)))

    def _get_message(self, message):
        if self._test_name:
            return "[{}] {}".format(self._test_name, message)
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
        if self._error_level and self._error_level <= ERROR:
            self._error = True
        self._output.error(self._get_message(message))

    @property
    def failed(self):
        return self._error

    def raise_if_error(self):
        if self._error:
            raise Exception("Some checks failed running the hook, check the output")


def raise_if_error_output(func):
    def wrapper(output, *args, **kwargs):
        output = _HooksOutputErrorCollector(output)
        ret = func(output, *args, **kwargs)
        output.raise_if_error()
        return ret
    return wrapper


def run_test(test_name, output):
    def tmp(func):
        out = _HooksOutputErrorCollector(output, test_name)
        ret = func(out)
        if not out.failed:
            out.success("OK")
        return ret

    return tmp


@raise_if_error_output
def pre_export(output, conanfile, conanfile_path, reference, **kwargs):
    conanfile_content = tools.load(conanfile_path)
    settings = getattr(conanfile, "settings", None)

    @run_test("REFERENCE LOWERCASE", output)
    def test(out):
        if reference.name != reference.name.lower():
            out.error("The library name has to be lowercase")
        if reference.version != reference.version.lower():
            out.error("The library version has to be lowercase")

    @run_test("RECIPE METADATA", output)
    def test(out):
        for field in ["url", "license", "description"]:
            field_value = getattr(conanfile, field, None)
            if not field_value:
                out.error("Conanfile doesn't have '%s' attribute. " % field)

    @run_test("HEADER ONLY", output)
    def test(out):
        build_method = getattr(conanfile, "build")
        # Check settings exist and build() is not the original one
        if not settings and "This conanfile has no build step" not in inspect.getsource(build_method):
            out.warn("Recipe does not declare 'settings' and has a 'build()' step")

    @run_test("NO COPY SOURCE", output)
    def test(out):
        no_copy_source = getattr(conanfile, "no_copy_source", None)
        if not settings and not no_copy_source:
            out.warn("This recipe seems to be for a header only library as it does not declare "
                     "'settings'. Please include 'no_copy_source' to avoid unnecessary copy steps")

    @run_test("FPIC OPTION", output)
    def test(out):
        options = getattr(conanfile, "options", None)
        installer = settings is not None and "os_build" in settings and "arch_build" in settings
        if settings and options and "fPIC" not in options and not installer:
            out.warn("This recipe does not include an 'fPIC' option. Make sure you are using the "
                     "right casing")
        elif options and not settings and ("fPIC" in options or "shared" in options):

            out.error("This recipe has 'shared' or 'fPIC' options but does not declare any "
                      "settings")

    @run_test("FPIC MANAGEMENT", output)
    def test(out):
        low = conanfile_content.lower()
        if '"fpic"' in low:
            remove_fpic_option = ['self.options.remove("fpic")',
                                  "self.options.remove('fpic')",
                                  'del self.options.fpic']
            if ("def config_options(self):" in low or "def configure(self):" in low)\
                    and any(r in low for r in remove_fpic_option):
                out.success("OK. 'fPIC' option found and apparently well managed")
            else:
                out.error("'fPIC' option not managed correctly. Please remove it for Windows "
                          "configurations: del self.options.fpic")
        else:
                out.info("'fPIC' option not found")

    @run_test("VERSION RANGES", output)
    def test(out):
        for num, line in enumerate(conanfile_content.splitlines()):
                if all([char in line for char in ("@", "[", "]")]):
                    out.error("Possible use of version ranges, line %s:\n %s" % (num, line))


@raise_if_error_output
def pre_source(output, conanfile, conanfile_path, **kwargs):
    conanfile_content = tools.load(conanfile_path)

    @run_test("IMMUTABLE SOURCES", output)
    def test(out):
        if "def source(self):" in conanfile_content:
            valid_content = [".zip", ".tar", ".tgz", ".tbz2", ".txz"]
            invalid_content = ["git checkout master", "git checkout devel", "git checkout develop"]
            if "git clone" in conanfile_content and "git checkout" in conanfile_content:
                fixed_sources = True
                for invalid in invalid_content:
                    if invalid in conanfile_content:
                        fixed_sources = False
            else:
                fixed_sources = False
                for valid in valid_content:
                    if valid in conanfile_content:
                        fixed_sources = True

            if not fixed_sources:
                out.error("Source files does not come from and immutable place. Checkout to a "
                          "commit/tag or download a compressed source file")


@raise_if_error_output
def post_source(output, conanfile, conanfile_path, **kwargs):

    @run_test("LIBCXX", output)
    def test(out):
        cpp_extensions = ["cc", "cpp", "cxx", "c++m", "cppm", "cxxm", "h++", "hh", "hxx", "hpp"]
        c_extensions = ["c", "h"]

        def _is_removing_libcxx():
            conanfile_content = tools.load(conanfile_path)
            low = conanfile_content.lower()
            conf = "def configure(self):"
            conf2 = "del self.settings.compiler.libcxx"
            return conf in low and conf2 in low

        if not _is_removing_libcxx()\
                and not _has_files_with_extensions(conanfile.source_folder, cpp_extensions) \
                and _has_files_with_extensions(conanfile.source_folder, c_extensions):
            out.error("Can't detect C++ source files but recipe does not remove 'compiler.libcxx'")


@raise_if_error_output
def post_build(output, conanfile, **kwargs):

    @run_test("MATCHING CONFIGURATION", output)
    def test(out):
        if not _files_match_settings(conanfile, conanfile.build_folder):
            out.error("Built artifacts does not match the settings used: os=%s, compiler=%s"
                      % (_get_os(conanfile), conanfile.settings.get_safe("compiler")))

    @run_test("SHARED ARTIFACTS", output)
    def test(out):
        if not _shared_files_well_managed(conanfile, conanfile.build_folder):
            out.error("Build with 'shared' option did not produce any shared artifact")


@raise_if_error_output
def post_package(output, conanfile, conanfile_path, **kwargs):

    @run_test("PACKAGE LICENSE", output)
    def test(out):
        licenses = []
        for root, dirnames, filenames in os.walk(conanfile.package_folder):
            for filename in filenames:
                if "licenses" in root.split(os.path.sep):
                    # licenses folder, almost anything here should be a license
                    if fnmatch.fnmatch(filename.lower(), "*copying*") or \
                            fnmatch.fnmatch(filename.lower(), "*readme*"):
                        licenses.append(os.path.join(root, filename))

                    if fnmatch.fnmatch(filename.lower(), "*license*"):
                        licenses.append(os.path.join(root, filename))
        if not licenses:
            out.error("No package licenses found in: %s. Please package the library "
                      "license to a 'licenses' folder" % conanfile.package_folder)

    @run_test("DEFAULT PACKAGE LAYOUT", output)
    def test(out):
        known_folders = ["lib", "bin", "include", "res"]
        for filename in os.listdir(conanfile.package_folder):
            if os.path.isdir(filename) and filename not in known_folders:
                out.error("Unknown folder {} in the package".format(filename))
            elif filename not in ["conaninfo.txt", "conanmanifest.txt", "licenses"]:
                out.error("Unknown file {} in the package".format(filename))

    @run_test("MATCHING CONFIGURATION", output)
    def test(out):
        if not _files_match_settings(conanfile, conanfile.package_folder):
            out.error("Packaged artifacts does not match the settings used: os=%s, compiler=%s"
                      % (_get_os(conanfile), conanfile.settings.get_safe("compiler")))

    @run_test("SHARED ARTIFACTS", output)
    def test(out):
        if not _shared_files_well_managed(conanfile, conanfile.package_folder):
            out.error("Package with 'shared' option did not contains any shared artifact")


def _has_files_with_extensions(folder, extensions):
    with tools.chdir(folder):
        for (root, _, filenames) in os.walk("."):
            for filename in filenames:
                for ext in extensions:
                    if filename.endswith(".%s" % ext):
                        return True
    return False


def _shared_files_well_managed(conanfile, folder):
    shared_extensions = ["dll", "so", "dylib"]
    shared_name = "shared"
    options_dict = {key: value for key, value in conanfile.options.values.as_list()}
    if shared_name in options_dict.keys():
        if _has_files_with_extensions(folder, shared_extensions):
            return options_dict[shared_name] == "True"
        else:
            return options_dict[shared_name] == "False"
    else:
        return True


def _files_match_settings(conanfile, folder):
    visual_extensions = ["lib", "dll", "exe"]
    mingw_extensions = ["a", "a.dll", "dll", "exe"]
    linux_extensions = ["a", "so"]
    macos_extensions = ["a", "dylib"]
    os = _get_os(conanfile)
    if os == "Windows":
        if conanfile.settings.get_safe("compiler") == "Visual Studio":
            if _has_files_with_extensions(folder, linux_extensions)\
                    or _has_files_with_extensions(folder, macos_extensions):
                return False
            return _has_files_with_extensions(folder, visual_extensions)
        else:
            return _has_files_with_extensions(folder, mingw_extensions)
    elif os == "Linux":
        if _has_files_with_extensions(folder, visual_extensions):
            return False
        return _has_files_with_extensions(folder, linux_extensions)
    elif os == "Macos":
        if _has_files_with_extensions(folder, visual_extensions):
            return False
        return _has_files_with_extensions(folder, macos_extensions)
    else:  # Not able to compare os setting
        return True


def _get_os(conanfile):
    settings = getattr(conanfile, "settings", None)
    if settings:
        for attrib in ["os", "os_build"]:
            the_os = settings.get_safe(attrib)
    else:
        the_os = None
    return the_os
