import os
import shutil
import textwrap
from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save


class TestKBH018(ConanClientV2TestCase):
    conanfile = textwrap.dedent("""
                        from conan import ConanFile
                        from conan.tools.system.package_manager import Apt
                        class AConan(ConanFile):
                            def system_requirements(self):
                                pass
                        """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH018, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def test_system_package(self):
        save(self, 'conanfile.py', content=self.conanfile)
        output = self.conan(['export', '--name=foobar', '--version=system', 'conanfile.py'])
        assert "[SYSTEM REQUIREMENTS (KB-H018)] OK" in output

    def test_regular_package(self):
        save(self, 'conanfile.py', content=self.conanfile.format(placeholder="#!/usr/bin/env python"))
        output = self.conan(['export', '--name=foobar', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [SYSTEM REQUIREMENTS (KB-H018)] The method 'system_requirements()' is not allowed for regular packages" in output
        assert "ERROR: [SYSTEM REQUIREMENTS (KB-H018)] Installing system requirements using 'system.package_manager' is not allowed" in output