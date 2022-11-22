import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class TestHeaderOnlyExtensions(ConanClientTestCase):
    """
    False positive from https://github.com/conan-io/conan-center-index/pull/14330
    post_package(): ERROR: [STATIC ARTIFACTS (KB-H074)] Package with 'shared=False' option did not contain any static artifact
    """

    conanfile = textwrap.dedent("""\
        from conan import ConanFile
        from conan.tools.files import get, copy
        from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
        from conan.tools.layout import basic_layout
        import os
        
        required_conan_version = ">=1.53.0"
        
        class MiniaudioConan(ConanFile):
            name = "miniaudio"
            settings = "os", "arch", "compiler", "build_type"
            options = {
                "shared": [True, False],
                "fPIC": [True, False],
                "header_only": [True, False],
            }
            default_options = {
                "shared": False,
                "fPIC": True,
                "header_only": True,
            }
        
            def config_options(self):
                if self.settings.os == "Windows":
                    del self.options.fPIC
        
            def configure(self):
                if self.options.shared:
                    self.options.rm_safe("fPIC")
                self.settings.rm_safe("compiler.libcxx")
                self.settings.rm_safe("compiler.cppstd")
        
            def layout(self):
                if self.options.header_only:
                    basic_layout(self, src_folder="src")
                else:
                    cmake_layout(self, src_folder="src")
        
            def package_id(self):
                if self.options.header_only:
                    self.info.clear()
        
            def generate(self):
                if self.options.header_only:
                    return
        
                tc = CMakeToolchain(self)
                tc.variables["MINIAUDIO_VERSION_STRING"] = self.version
                tc.generate()

            def build(self):
                if self.options.header_only:
                    return
        
                cmake = CMake(self)
                cmake.configure(build_script_folder=os.path.join(self.source_folder, os.pardir))
                cmake.build()
        
            def package(self):
                copy(self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
                copy(
                    self,
                    pattern="**",
                    dst=os.path.join(self.package_folder, "include", "extras"),
                    src=os.path.join(self.source_folder, "extras"),
                )
        
                if self.options.header_only:
                    copy(
                        self,
                        pattern="miniaudio.h",
                        dst=os.path.join(self.package_folder, "include"),
                        src=self.source_folder)
                    copy(
                        self,
                        pattern="miniaudio.*",
                        dst=os.path.join(self.package_folder, "include", "extras", "miniaudio_split"),
                        src=os.path.join(self.source_folder, "extras", "miniaudio_split"),
                    )
                else:
                    cmake = CMake(self)
                    cmake.install()
        
            def package_info(self):
                if self.options.header_only:
                    self.cpp_info.bindirs = []
                    self.cpp_info.libdirs = []
                else:
                    self.cpp_info.libs = ["miniaudio"]
                    if self.options.shared:
                        self.cpp_info.defines.append("MA_DLL")

        """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestHeaderOnlyExtensions, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_create_header_only(self):
        tools.save('conanfile.py', content=self.conanfile)
        output = self.conan(['create', '.', 'miniaudio/0.11.11@', '-o', 'miniaudio:header_only=True'])
        self.assertIn("[STATIC ARTIFACTS (KB-H074)] OK", output)
