import os
import textwrap
import unittest

from conan.tools.files import save

from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase


class TestConanData(ConanClientV2TestCase):
    conanfile = textwrap.dedent("""\
        import os
        from conan import ConanFile

        class AConan(ConanFile):
            name = "name"

            def source(self):
                pass
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestConanData, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'hook_reduce_conandata')})
        return kwargs

    def test_reduce_conandata(self):
        conandata = textwrap.dedent("""
            sources:
              "1.69.0":
                url: "url1_1.69.0"
                sha256: "sha1_1.69.0"
              "1.70.0":
                url: "url1_1.70.0"
                sha256: "sha1_1.70.0"
            patches:
              "1.69.0":
                patch_file: "001-1.69.0.patch"
                base_path: "source_subfolder/1.69.0"
              "1.70.0":
                patch_file: "001-1.70.0.patch"
                base_path: "source_subfolder/1.70.0"
        """)
        save(None, 'conanfile.py', content=self.conanfile)
        save(None, 'conandata.yml', content=conandata)
        export_output = self.conan(['export', '.', '--version=1.69.0'])
        assert '1.70.0' not in export_output
        assert 'New conandata.yml contents: "1.69.0":' in export_output
