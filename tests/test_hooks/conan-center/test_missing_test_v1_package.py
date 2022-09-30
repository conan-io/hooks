import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class TestMissingTestV1Package(ConanClientTestCase):
    conanfile = textwrap.dedent("""\
        from conan import ConanFile
        class AConan(ConanFile):
            topics = ("foobar",)
            pass
        """)

    test_package_conanfile = textwrap.dedent("""\
            from conan import ConanFile
            from conan.tools.cmake import CMake, cmake_layout
            from conan.tools.build import can_run

            class TestPackageConan(ConanFile):
                settings = "os", "arch", "compiler", "build_type"
                generators = "CMakeDeps", "CMakeToolchain", "VirtualRunEnv"
                test_type = "explicit"
            
                def requirements(self):
                    self.requires(self.tested_reference_str)
            
                def layout(self):
                    cmake_layout(self)
            
                def build(self):
                    cmake = CMake(self)
                    cmake.configure()
                    cmake.build()
            
                def test(self):
                    if can_run(self):
                        bin_path = os.path.join(self.cpp.build.bindirs[0], "test_package")
                        self.run(bin_path, env="conanrun")
                
            """)

    test_v1_package_conanfile = textwrap.dedent("""\
            from conans import ConanFile, CMake
            from conan.tools.build import cross_building
            import os
            
            
            # legacy validation with Conan 1.x
            class TestPackageV1Conan(ConanFile):
                settings = "os", "arch", "compiler", "build_type"
                generators = "cmake", "cmake_find_package_multi"
            
                def build(self):
                    cmake = CMake(self)
                    cmake.configure()
                    cmake.build()
            
                def test(self):
                    if not cross_building(self):
                        bin_path = os.path.join("bin", "test_package")
                        self.run(bin_path, run_environment=True)
            """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestMissingTestV1Package, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_valid_folder_structure(self):
        tools.save('conanfile.py', content=self.conanfile)
        tools.save('test_package/conanfile.py', content=self.test_package_conanfile)
        tools.save('test_v1_package/conanfile.py', content=self.test_v1_package_conanfile)
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("[TEST V1 PACKAGE FOLDER (KB-H073)] OK", output)

    def test_missing_legacy_test_package(self):
        tools.save('conanfile.py', content=self.conanfile)
        tools.save('test_package/conanfile.py', content=self.test_package_conanfile)
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [TEST V1 PACKAGE FOLDER (KB-H073)] The test_package seems be prepared for Conan v2, "
                      "but test_v1_package is missing.", output)
