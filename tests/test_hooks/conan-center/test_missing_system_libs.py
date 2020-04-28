import os
from parameterized import parameterized
import textwrap
import unittest

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase
from conans import __version__ as conan_version


@unittest.skipUnless(conan_version >= "1.19.0", "Conan >= 1.19.0 needed")
@unittest.skipIf(tools.is_apple_os(tools.detected_os()), "Apple os'es are not supported")
class ConanMissingSystemLibs(ConanClientTestCase):
    cmakelists = textwrap.dedent("""\
        cmake_minimum_required(VERSION 2.8)
        project(hooks_systemlib_test LANGUAGES C)
        
        include(conanbuildinfo.cmake)
        conan_basic_setup()
        
        set(LINK_TO {link_lib})
        if(LINK_TO)
            find_library(LINK_LIB_FULL_PATH {link_lib})
            if(LINK_LIB_FULL_PATH)
                set(LINK_TO ${{LINK_LIB_FULL_PATH}})
            endif()
        endif()
        
        add_library({name} simplelib.c)
        set_property(TARGET {name} PROPERTY PREFIX lib)
        target_link_libraries({name} ${{LINK_TO}} ${{CONAN_LIBS}})
        include(GNUInstallDirs)
        install(TARGETS {name}
            ARCHIVE DESTINATION ${{CMAKE_INSTALL_LIBDIR}}
            LIBRARY DESTINATION ${{CMAKE_INSTALL_LIBDIR}}
            RUNTIME DESTINATION ${{CMAKE_INSTALL_BINDIR}})
    """)

    source_c = textwrap.dedent("""\
        #if defined({name}_EXPORTS)
        #  if defined(_WIN32)
        #    define API_EXPORTS __declspec(dllexport)
        #  else
        #    define API_EXPORTS __attribute__((visibility("default")))
        #  endif
        #else
        #  define API_EXPORTS
        #endif
        
        {includes}
        
        API_EXPORTS
        int {name}_function(int arg) {{
            {function_call};
            return 42;
        }}
    """)

    conanfile = textwrap.dedent("""\
        import os
        from conans import CMake, ConanFile, tools

        class AConan(ConanFile):
            exports_sources = "CMakeLists.txt", "simplelib.c"
            settings = "os", "arch", "compiler", "build_type"
            options = {{"shared": [True, False], "fPIC": [True, False],}}
            default_options = {{"shared": False, "fPIC": True,}}
            generators = "cmake"
            requires = {requires}
                
            def package(self):
                cmake = CMake(self)
                cmake.configure()
                cmake.build()
                cmake.install()
                
            def package_info(self):
                self.cpp_info.libs = ["{name}"]
                if self.options.shared:
                    self.cpp_info.system_libs = {system_libs_shared}
                else:
                    self.cpp_info.system_libs = {system_libs_static}
        """)

    conanfile_test = textwrap.dedent("""\
        from conans import ConanFile

        class AConan(ConanFile):
            def test(self):
                pass
        """)

    class OSBuildInfo(object):
        def __init__(self, includes, link_libs, shlibs_bases, function):
            self.includes = includes
            self.libs = link_libs
            self.shlibs_bases = shlibs_bases
            self.function = function

    @property
    def _os_build_info(self):
        return {
            "Linux": self.OSBuildInfo(["dlfcn.h"], ["libdl.so"], ["dl"], "dlclose((void*)0)"),
            "Windows": self.OSBuildInfo(["winsock.h"], ["ws2_32.lib"], ["ws2_32"], "ntohs(0x4200)"),
            # "Macos": self.OSBuildInfo([], ["m"], "(int)tan(42.)"),
        }[tools.detected_os()]

    @property
    def _os_build_info2(self):
        return {
            "Linux": self.OSBuildInfo(["time.h"], ["librt.so"], ["rt"], "clock_settime(CLOCK_REALTIME, 0)"),
            "Windows": self.OSBuildInfo(["shlwapi.h"], ["shlwapi.lib"], ["shlwapi"], "PathIsDirectory(\"C:\\Windows\")"),
            # "Macos": self.OSBuildInfo([], ["m"], "(int)tan(42.)"),
        }[tools.detected_os()]

    @property
    def _shlext(self):
        return {
            "Windows": "dll",
            "Linux": "so",
            # "Macos": "dylib",
        }[tools.detected_os()]

    @property
    def _shlibdir(self):
        return {
            "Windows": "bin",
            "Linux": "lib",
            # "Macos": "lib",
        }[tools.detected_os()]

    def _get_environ(self, **kwargs):
        kwargs = super(ConanMissingSystemLibs, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def _write_files(self, osbuildinfo, system_libs_shared, system_libs_static, requires=(), name="simplelib", subdir="."):
        tools.save(os.path.join(subdir, "conanfile.py"), content=self.conanfile.format(name=name, system_libs_shared=repr(system_libs_shared), system_libs_static=repr(system_libs_static), requires=repr(requires)))
        tools.save(os.path.join(subdir, "CMakeLists.txt"), content=self.cmakelists.format(name=name, link_lib=" ".join(osbuildinfo.libs)))
        tools.save(os.path.join(subdir, "simplelib.c"), content=self.source_c.format(name=name, includes="\n".join("#include <{}>".format(include) for include in osbuildinfo.includes), function_call=osbuildinfo.function))
        tools.save(os.path.join(subdir, "test_package", "conanfile.py"), content=self.conanfile_test)

    def test_no_system_lib(self):
        osbuildinfo = self.OSBuildInfo([], [], [], "42")
        self._write_files(osbuildinfo=osbuildinfo, system_libs_static=[], system_libs_shared=[])
        output = self.conan(["create", ".", "name/version@user/channel", "-o", "name:shared=True"])
        self.assertIn("[MISSING SYSTEM LIBS (KB-H043)] OK", output)
        for lib in self._os_build_info.shlibs_bases:
            library = os.path.join(".", self._shlibdir, "libsimplelib.{}".format(self._shlext))
            self.assertNotIn("[MISSING SYSTEM LIBS (KB-H043)] Library '{library}' links to system library '{syslib}' but it is not in cpp_info.system_libs.".format(library=library, shlext=self._shlext, syslib=lib), output)

    @unittest.skipUnless(not tools.is_apple_os(tools.detected_os()), "Macos is not supported")
    def test_system_lib_correct(self):
        self._write_files(osbuildinfo=self._os_build_info, system_libs_static=self._os_build_info.shlibs_bases, system_libs_shared=[])
        output = self.conan(["create", ".", "name/version@user/channel", "-o", "name:shared=True"])
        self.assertIn("[MISSING SYSTEM LIBS (KB-H043)] OK", output)
        for lib in self._os_build_info.shlibs_bases:
            library = os.path.join(".", self._shlibdir, "libsimplelib.{}".format(self._shlext))
            self.assertNotIn("[MISSING SYSTEM LIBS (KB-H043)] Library '{library}' links to system library '{syslib}' but it is not in cpp_info.system_libs.".format(library=library, shlext=self._shlext, syslib=lib), output)

    @unittest.skipUnless(not tools.is_apple_os(tools.detected_os()), "Macos is not supported")
    def test_system_lib_missing(self):
        self._write_files(osbuildinfo=self._os_build_info, system_libs_static=[], system_libs_shared=[])
        output  = self.conan(["create", ".", "name/version@user/channel", "-o", "name:shared=True"])
        for lib in self._os_build_info.shlibs_bases:
            library = os.path.join(".", self._shlibdir, "libsimplelib.{}".format(self._shlext))
            self.assertIn("[MISSING SYSTEM LIBS (KB-H043)] Library '{library}' links to system library '{syslib}' but it is not in cpp_info.system_libs.".format(library=library, shlext=self._shlext, syslib=lib), output)

    @unittest.skipUnless(not tools.is_apple_os(tools.detected_os()), "Macos is not supported")
    @parameterized.expand([
        ("shared_dependency", True),
        ("static_dependency", False),
    ])
    def test_dep_system_lib_ok(self, name, dep_shared):
        self._write_files(subdir="dep", name="dep", osbuildinfo=self._os_build_info, system_libs_static=self._os_build_info.shlibs_bases, system_libs_shared=[])
        self.conan(["create", "dep", "dep/version@user/channel", "-o", "dep:shared={}".format(dep_shared)])
        self._write_files(subdir="lib", name="lib", requires=("dep/version@user/channel", ), osbuildinfo=self._os_build_info2, system_libs_static=self._os_build_info2.shlibs_bases, system_libs_shared=[])
        output = self.conan(["create", "lib", "lib/version@user/channel", "-o", "lib:shared=True", "-o", "dep:shared={}".format(dep_shared)])
        self.assertIn("[MISSING SYSTEM LIBS (KB-H043)] OK", output)
        for lib in self._os_build_info.shlibs_bases:
            library = os.path.join(".", self._shlibdir, "liblib.{}".format(self._shlext))
            self.assertNotIn("[MISSING SYSTEM LIBS (KB-H043)] Library '{library}' links to system library '{syslib}' but it is not in cpp_info.system_libs.".format(library=library, shlext=self._shlext, syslib=lib), output)
        for lib in self._os_build_info2.shlibs_bases:
            library = os.path.join(".", self._shlibdir, "liblib.{}".format(self._shlext))
            self.assertNotIn("[MISSING SYSTEM LIBS (KB-H043)] Library '{library}' links to system library '{syslib}' but it is not in cpp_info.system_libs.".format(library=library, shlext=self._shlext, syslib=lib), output)

    @unittest.skipUnless(not tools.is_apple_os(tools.detected_os()), "Macos is not supported")
    @parameterized.expand([
        ("shared_dependency", True),
        ("static_dependency", False),
    ])
    def test_dep_system_lib_missing(self, name, dep_shared):
        self._write_files(subdir="dep", name="dep", osbuildinfo=self._os_build_info, system_libs_static=self._os_build_info.shlibs_bases, system_libs_shared=[])
        self.conan(["create", "dep", "dep/version@user/channel", "-o", "dep:shared={}".format(dep_shared)])
        self._write_files(subdir="lib", name="lib", requires=("dep/version@user/channel", ), osbuildinfo=self._os_build_info2, system_libs_static=[], system_libs_shared=[])
        output = self.conan(["create", "lib", "lib/version@user/channel", "-o", "lib:shared=True", "-o", "dep:shared={}".format(dep_shared)])
        self.assertIn("[MISSING SYSTEM LIBS (KB-H043)] OK", output)
        for lib in self._os_build_info.shlibs_bases:
            library = os.path.join(".", self._shlibdir, "liblib.{}".format(self._shlext))
            self.assertNotIn("[MISSING SYSTEM LIBS (KB-H043)] Library '{library}' links to system library '{syslib}' but it is not in cpp_info.system_libs.".format(library=library, shlext=self._shlext, syslib=lib), output)
        for lib in self._os_build_info2.shlibs_bases:
            library = os.path.join(".", self._shlibdir, "liblib.{}".format(self._shlext))
            self.assertIn("[MISSING SYSTEM LIBS (KB-H043)] Library '{library}' links to system library '{syslib}' but it is not in cpp_info.system_libs.".format(library=library, shlext=self._shlext, syslib=lib), output)
