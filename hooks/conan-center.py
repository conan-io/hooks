import fnmatch
import os

from conans import tools


def pre_export(output, conanfile, conanfile_path, reference, **kwargs):
    conanfile_content = tools.load(conanfile_path)
    test = "[RECIPE METADATA]"
    metadata_error = False
    for field in ["url", "license", "description"]:
        field_value = getattr(conanfile, field, None)
        if not field_value:
            metadata_error = True
            output.error("%s Conanfile doesn't have '%s'. It is recommended to add it as attribute"
                         % (test, field))
    if not metadata_error:
        output.success("%s OK" % test)

    test = "[HEADER ONLY]"
    settings = getattr(conanfile, "settings", None)
    build = getattr(conanfile, "build", None)
    if not settings and build:
        output.warn("%s Recipe does not declare 'settings' and has a 'build()' step")
    else:
        output.success("%s OK" % test)

    test = "[NO COPY SOURCE]"
    no_copy_source = getattr(conanfile, "no_copy_source", None)
    if not settings and not no_copy_source:
        output.warn("%s This recipe seems to be for a header only library as it does not declare "
                    "'settings'. Please include 'no_copy_source' to avoid unnecessary copy steps"
                    % test)
    else:
        output.success("%s OK" % test)

    test = "[FPIC OPTION]"
    fpic_error = False
    options = getattr(conanfile, "options", None)
    if settings and options and "fPIC" not in options:
        fpic_error = True
        output.warn("%s This recipe does not include an 'fPIC' option. Make sure you are using the "
                    "right casing" % test)
    elif options and not settings and ("fPIC" in options or "shared" in options):
        fpic_error = True
        output.error("%s This recipe has 'shared' or 'fPIC' options but does not delcare any "
                     "settings" % test)
    if not fpic_error:
        output.success("%s OK" % test)

    test = "[FPIC MANAGEMENT]"
    low = conanfile_content.lower()
    if '"fpic"' in low:
        remove_fpic_option = ['self.options.remove("fpic")',
                              "self.options.remove('fpic')",
                              'del self.options.fpic']
        if ("def config_options(self):" in low or "def configure(self):" in low)\
                and any(r in low for r in remove_fpic_option):
            output.success("%s OK. 'fPIC' option found and apparently well managed" % test)
        else:
            output.error("%s 'fPIC' option not managed correctly. Please remove it for Windows "
            "configurations: del self.options.fpic" % test)
    else:
            output.info("%s 'fPIC' option not found" % test)

    test = "[VERSION RANGES]"
    version_ranges_error = False
    for num, line in enumerate(conanfile_content.splitlines()):
            if all([char in line for char in ("@", "[", "]")]):
                version_ranges_error = True
                output.error("%s Possible use of version ranges, line %s:\n %s" % (test, num, line))
    if not version_ranges_error:
        output.success("%s OK" % test)


def pre_source(output, conanfile, conanfile_path, **kwargs):
    conanfile_content = tools.load(conanfile_path)
    if "def source(self):" in conanfile_content:
        test = "[IMMUTABLE SOURCES]"
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
            output.error("%s Source files does not come from and immutable place. Checkout to a "
                         "commit/tag or download a compressed source file" % test)
        else:
            output.success("%s OK" % test)


def post_source(output, conanfile, conanfile_path, **kwargs):
    test = "[LIBCXX]"
    cpp_extensions = ["cpp", "cxx", "c++m", "cppm", "cxxm", "h++", "hh", "hxx", "hpp"]

    def _is_removing_libcxx():
        conanfile_content = tools.load(conanfile_path)
        low = conanfile_content.lower()
        conf = "def configure(self):"
        conf2 = "del self.settings.compiler.libcxx"
        return conf in low and conf2 in low

    if not _is_removing_libcxx()\
            and not _has_files_with_extensions(conanfile.source_folder, cpp_extensions):
        output.error("%s Can't detect C++ source files but recipe does not remove 'compiler.libcxx'"
                     % test)
    else:
        output.success("%s OK" % test)


def post_build(output, conanfile, **kwargs):
    test = "[MATCHING CONFIGURATION]"
    if not _files_match_settings(conanfile, conanfile.build_folder):
        output.error("%s Built artifacts does not match the settings used: os=%s, compiler=%s"
                     % (test, _get_os(conanfile), conanfile.settings.compiler))
    else:
        output.success("%s OK" % test)

    test = "[SHARED ARTIFACTS]"
    if not _shared_files_well_managed(conanfile, conanfile.build_folder):
        output.error("%s Build with 'shared' option did not produce any shared artifact" % test)
    else:
        output.success("%s OK" % test)


def post_package(output, conanfile, conanfile_path, **kwargs):
    test = "[PACKAGE LICENSE]"
    licenses = []
    for root, dirnames, filenames in os.walk(conanfile.package_folder):
        for filename in filenames:
            if "licenses" in root.split(os.path.sep):
                # licenses folder, almost anything here should be a license
                if fnmatch.fnmatch(filename.lower(), "*copying*") or fnmatch.fnmatch(filename.lower(), "*readme*"):
                    licenses.append(os.path.join(root, filename))

                if fnmatch.fnmatch(filename.lower(), "*license*"):
                    licenses.append(os.path.join(root, filename))
    if not licenses:
        output.error("%s No package licenses found in: %s. Please package the library license to a "
                     "'licenses' folder" % (test, conanfile.package_folder))
    else:
        output.success("%s OK. Licenses found in: %s" % (test, licenses))

    test = "[DEFAULT PACKAGE LAYOUT]"
    if not _default_package_structure(conanfile.package_folder):
        output.error("%s Generated package without default package structure. Check %s"
                     % (test, conanfile.package_folder))
    else:
        output.success("%s OK" % test)

    test = "[MATCHING CONFIGURATION]"
    if not _files_match_settings(conanfile, conanfile.package_folder):
        output.error("%s Packaged artifacts does not match the settings used: os=%s, compiler=%s"
                     % (test, _get_os(conanfile), conanfile.settings.compiler))
    else:
        output.success("%s OK" % test)

    test = "[SHARED ARTIFACTS]"
    if not _shared_files_well_managed(conanfile, conanfile.package_folder):
        output.error("%s Package with 'shared' option did not contains any shared artifact" % test)
    else:
        output.success("%s OK" % test)



def _has_files_with_extensions(folder, extensions):
    ret = False
    with tools.chdir(folder):
        for (root, _, filenames) in os.walk("."):
            for filename in filenames:
                for ext in extensions:
                    if filename.endswith(".%s" % ext):
                        ret = True
    return ret


def _shared_files_well_managed(conanfile, folder):
    shared_extensions = ["dll", "so", "dylib"]
    shared_name = "shared"
    options_dict = {}
    for key, value in conanfile.options.values.as_list():
        # FIXME: shared_name used to target both 'shared' for pacakge creation
        # and 'libname:shared' test_package
        if "shared" in key:
            shared_name = key
        options_dict[key] = value
    if shared_name in options_dict.keys():
        if _has_files_with_extensions(folder, shared_extensions):
            return options_dict[shared_name] == "True"
        else:
            return options_dict[shared_name] == "False"
    else:
        return False


def _files_match_settings(conanfile, folder):
    visual_extensions = ["lib", "dll", "exe"]
    mingw_extensions = ["a", "a.dll", "dll", "exe"]
    linux_extensions = ["a", "so"]
    macos_extensions = ["a", "dylib"]
    os = _get_os(conanfile)
    if os == "Windows":
        if conanfile.settings.compiler == "Visual Studio":
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


def _default_package_structure(folder):
    default_folders = ["lib", "bin", "include", "res"]
    for folder in os.listdir(folder):
        if folder in ["conaninfo.txt", "conanmanifest.txt", "licenses"]:
            continue
        if folder not in default_folders:
            return False
    return True


def _get_os(conanfile):
    if hasattr(conanfile.settings, "os"):
        return conanfile.settings.os
    return conanfile.settings.os_build
