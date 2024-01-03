import os
import shutil
import textwrap
import pytest
import platform

from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save


class TestKBH011(ConanClientV2TestCase):
    conanfile = textwrap.dedent("""\
            from conan import ConanFile
            from conan.tools.files import save
            import os
            class AConan(ConanFile):
                settings = "os", "arch", "compiler", "build_type"
                options = {"shared": [True, False]}
                default_options = {"shared": False}
                package_type = "library"

                def package(self):                                    
                    save(self, os.path.join(self.package_folder, "{lib}"), "whatever")
                    
                def package_info(self):
                    self.cpp_info.libs = ["foo"]
            """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH011, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def _get_library_name(self, shared):
        return {"Windows": {True: "bin/foo.dll", False: "lib/foo.lib"},
                "Linux": {True: "lib/libfoo.so", False: "lib/libfoo.a"},
                "Darwin": {True: "lib/libfoo.dylib", False: "lib/libfoo.a"}}[platform.system()][shared]

    def test_option_shared_lib_shared(self):
        save(self, "conanfile.py", content=self.conanfile.replace("{lib}", self._get_library_name(True)))
        output = self.conan(["create", "--name=foobar", "--version=0.1.0", "conanfile.py", "-o", "foobar/0.1.0:shared=True"])
        assert "[MATCHING CONFIGURATION (KB-H011)] OK" in output

    def test_option_static_lib_static(self):
        save(self, "conanfile.py", content=self.conanfile.replace("{lib}", self._get_library_name(False)))
        output = self.conan(["create", "--name=foobar", "--version=0.1.0", "conanfile.py", "-o", "foobar/0.1.0:shared=False"])
        assert "[MATCHING CONFIGURATION (KB-H011)] OK" in output

    def test_option_shared_lib_static(self):
        save(self, "conanfile.py", content=self.conanfile.replace("{lib}", self._get_library_name(False)))
        output = self.conan(["create", "--name=foobar", "--version=0.1.0", "conanfile.py", "-o", "foobar/0.1.0:shared=True"])
        assert "ERROR: [MATCHING CONFIGURATION (KB-H011)] Package with 'shared=True' option did not contain any shared artifact" in output
        assert "ERROR: [MATCHING CONFIGURATION (KB-H011)] Package type is 'shared-library' but contains static libraries" in output

    def test_option_static_lib_shared(self):
        save(self, "conanfile.py", content=self.conanfile.replace("{lib}", self._get_library_name(True)))
        output = self.conan(["create", "--name=foobar", "--version=0.1.0", "conanfile.py", "-o", "foobar/0.1.0:shared=False"])
        assert "ERROR: [MATCHING CONFIGURATION (KB-H011)] Package with 'shared=False' option did not contain any static artifact" in output
        assert "ERROR: [MATCHING CONFIGURATION (KB-H011)] Package type is 'static-library' but contains shared libraries" in output

    def test_static_and_shared_packaged(self):
        conanfile = textwrap.dedent("""\
                    from conan import ConanFile
                    from conan.tools.files import save
                    import os
                    class AConan(ConanFile):                                                    
                        def package(self):                                    
                            save(self, os.path.join(self.package_folder, "lib", "libfoo.a"), "whatever")
                            save(self, os.path.join(self.package_folder, "lib", "libfoo.so"), "whatever")                        
                    """)
        save(self, "conanfile.py", content=conanfile)
        output = self.conan(["create", "--name=foobar", "--version=0.1.0", "conanfile.py"])
        assert "ERROR: [MATCHING CONFIGURATION (KB-H011)] Package contains both shared and static flavors of these libraries" in output

    def test_package_type_share_lib_shared(self):
        save(self, "conanfile.py", content=self.conanfile.replace("library", "shared-library").replace("{lib}", self._get_library_name(True)))
        output = self.conan(["create", "--name=foobar", "--version=0.1.0", "conanfile.py", "-o", "foobar/0.1.0:shared=True"])
        assert "[MATCHING CONFIGURATION (KB-H011)] OK" in output

    def test_package_type_static_lib_static(self):
        save(self, "conanfile.py", content=self.conanfile.replace("library", "static-library").replace("{lib}", self._get_library_name(False)))
        output = self.conan(["create", "--name=foobar", "--version=0.1.0", "conanfile.py", "-o", "foobar/0.1.0:shared=False"])
        assert "[MATCHING CONFIGURATION (KB-H011)] OK" in output

    def test_package_type_static_lib_shared(self):
        save(self, "conanfile.py", content=self.conanfile.replace("library", "static-library").replace("{lib}", self._get_library_name(True)))
        output = self.conan(["create", "--name=foobar", "--version=0.1.0", "conanfile.py", "-o", "foobar/0.1.0:shared=True"])
        assert "ERROR: [MATCHING CONFIGURATION (KB-H011)] Package type is 'static-library' but contains shared libraries" in output

    def test_package_type_shared_lib_static(self):
        save(self, "conanfile.py", content=self.conanfile.replace("library", "shared-library").replace("{lib}", self._get_library_name(False)))
        output = self.conan(["create", "--name=foobar", "--version=0.1.0", "conanfile.py", "-o", "foobar/0.1.0:shared=False"])
        assert "ERROR: [MATCHING CONFIGURATION (KB-H011)] Package type is 'shared-library' but contains static libraries" in output