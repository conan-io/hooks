import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class ConanData(ConanClientTestCase):


    def _get_environ(self, **kwargs):
        kwargs = super(ConanData, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_missing_conandata(self):
        conanfile = textwrap.dedent("""\
            import os
            from conans import ConanFile, tools

            class AConan(ConanFile):
                pass
            """)
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertIn("[IMMUTABLE SOURCES] Create a file 'conandata.yml' file with the "
                      "sources to be downloaded.", output)

    def test_no_missing_conandata_but_not_used(self):
        conanfile = textwrap.dedent("""\
                import os
                from conans import ConanFile, tools

                class AConan(ConanFile):
                    
                    def source(self):
                        pass
                """)
        tools.save('conanfile.py', content=conanfile)
        tools.save('conandata.yml', content="")
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertIn("[IMMUTABLE SOURCES] Use the \'conandata.yml\' file to describe "
                      "where to get the source code", output)

    def test_correct_usage(self):
        conanfile = textwrap.dedent("""\
                       import os
                       from conans import ConanFile, tools

                       class AConan(ConanFile):

                           def source(self):
                               tools.get(**self.conan_data["sources"]["all"])
                       """)
        conandata = textwrap.dedent("""
                    sources:
                        all:
                           url: fakeurl
                           md5: 12323423423
                       """)
        tools.save('conanfile.py', content=conanfile)
        tools.save('conandata.yml', content=conandata)
        output = self.conan(['create', '.', 'name/version@user/channel'], expected_return_code=1)
        self.assertIn("[IMMUTABLE SOURCES] OK", output)
        self.assertIn("Invalid URL 'fakeurl': No schema supplied", output)

