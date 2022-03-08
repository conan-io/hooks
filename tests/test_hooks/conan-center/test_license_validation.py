import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class TestLicenseValidation(ConanClientTestCase):
    conanfile = textwrap.dedent("""\
        from conans import ConanFile
        class AConan(ConanFile):
                license = "{}"
        """)
    conandata = textwrap.dedent("""\
        sources:
          8.9.2:
            - url: https://github.com/approvals/ApprovalTests.cpp/releases/download/v.8.9.2/ApprovalTests.v.8.9.2.hpp
              sha256: e743f1b83afb045cb9bdee310e438a3ed610a549240e4b4c4c995e548c773da5
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestLicenseValidation, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_expected_license(self):
        tools.save('conanfile.py', content=self.conanfile)
        tools.save('conandata.yml', content=self.conandata)
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("[LICENSE VALIDATION (KB-H070)] OK", output)
