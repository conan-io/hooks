import os
import textwrap
import unittest
import yaml

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase
from conans import __version__ as conan_version


@unittest.skipUnless(conan_version >= "1.16.0", "Conan > 1.16.0 needed")
class ConanData(ConanClientTestCase):
    conanfile = textwrap.dedent("""\
        import os
        from conans import ConanFile, tools

        class AConan(ConanFile):

            def source(self):
                pass
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(ConanData, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_missing_conandata(self):
        tools.save('conanfile.py', content=self.conanfile)
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertIn("[IMMUTABLE SOURCES (KB-H010)] Create a file 'conandata.yml' file with the "
                      "sources to be downloaded.", output)

    def test_no_missing_conandata_but_not_used(self):
        tools.save('conanfile.py', content=self.conanfile)
        tools.save('conandata.yml', content="")
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertIn("[IMMUTABLE SOURCES (KB-H010)] Use 'tools.get(**self.conan_data[\"sources\"]", output)

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
        self.assertIn("[IMMUTABLE SOURCES (KB-H010)] OK", output)

    def test_reduce_conandata(self):
        tools.save('conanfile.py', content=self.conanfile)
        conandata = textwrap.dedent("""
            sources:
              "1.69.0":
                url: "url1.69.0"
                sha256: "sha1.69.0"
                other: "more_data"
              "1.70.0":
                url: "url1.70.0"
                sha256: "sha1.70.0"
            patches:
              "1.70.0":
                patches: "1.70.0.patch"
              "1.71.0":
                patches: "1.71.0.patch"
            random_field: "random"
            field_introduced_in_the_future:
              "1.71.0":
                something: "else"
            """)
        tools.save('conandata.yml', content=conandata)
        for version in ["1.69.0", "1.70.0", "1.71.0"]:
            self.conan(['export', '.', 'name/%s@jgsogo/test' % version])
            output = self.conan(['get', 'name/%s@jgsogo/test' % version, 'conandata.yml'])
            conandata = yaml.safe_load(output)

            self.assertNotIn("random_field", conandata)

            if version in ["1.69.0", "1.70.0"]:
                self.assertEqual("url%s" % version, conandata["sources"][version]["url"])
                self.assertEqual("sha%s" % version, conandata["sources"][version]["sha256"])
                self.assertNotIn("field_introduced_in_the_future", conandata)
            if version in ["1.70.0", "1.71.0"]:
                self.assertIn("%s.patch" % version, conandata["patches"][version]["patches"])
            if version == "1.69.0":
                self.assertEqual("more_data", conandata["sources"][version]["other"])
                self.assertNotIn("patches", conandata)
            if version == "1.70.0":
                self.assertNotIn("other", conandata["sources"][version])
            if version == "1.71.0":
                self.assertNotIn("sources", conandata)
                self.assertIn("else",
                              conandata["field_introduced_in_the_future"][version]["something"])
