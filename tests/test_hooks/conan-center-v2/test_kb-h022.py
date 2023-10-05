import os
import textwrap
import shutil
from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save


class TestKBH022(ConanClientV2TestCase):
    conanfile = textwrap.dedent("""\
            from conan import ConanFile            
            class AConan(ConanFile):
                pass
            """)
    conandata = textwrap.dedent("""
                        sources:
                            1.0:
                               url: fakeurl
                               md5: 12323423423
                            2.0:
                               url: fakeurl
                               md5: 12323423423
            """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH022, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def setup_method(self, method):
        self.conan(['profile', 'detect', '--force'])

    def test_regular_conandata_config(self):
        config = textwrap.dedent("""
        versions:
          1.0:
            folder: all
          2.0:
            folder: all
        """)
        save(self, "config.yml", content=config)
        save(self, os.path.join('all', 'conanfile.py'), content=self.conanfile)
        save(self, os.path.join("all", "conandata.yml"), content=self.conandata)
        output = self.conan(['export', 'all', '--name=name', '--version=0.1.0'])
        assert "pre_export(): [CONFIG.YML HAS NEW VERSION (KB-H022)] OK" in output

    def test_missing_version_in_config(self):
        config = textwrap.dedent("""
        versions:
          1.0:
            folder: all
        """)
        save(self, "config.yml", content=config)
        save(self, os.path.join("all", "conandata.yml"), content=self.conandata)
        save(self, os.path.join('all', 'conanfile.py'), content=self.conanfile)
        output = self.conan(['export', 'all', '--name=name', '--version=0.1.0'])
        assert 'pre_export(): ERROR: [CONFIG.YML HAS NEW VERSION (KB-H022)] The version "2.0" exists in "conandata.yml"' in output

    def test_missing_version_in_conandata(self):
        config = textwrap.dedent("""
        versions:
          1.0:
            folder: all
          2.0:
            folder: all
        """)
        conandata = textwrap.dedent("""
                                sources:
                                    1.0:
                                       url: fakeurl
                                       md5: 12323423423                                   
                    """)
        save(self, "config.yml", content=config)
        save(self, os.path.join('all', 'conanfile.py'), content=self.conanfile)
        save(self, os.path.join("all", "conandata.yml"), content=conandata)
        output = self.conan(['export', 'all', '--name=name', '--version=0.1.0'])
        assert "pre_export(): [CONFIG.YML HAS NEW VERSION (KB-H022)] OK" in output