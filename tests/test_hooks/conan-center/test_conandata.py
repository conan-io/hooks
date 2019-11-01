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
              "1.70.0":
                url: "url1.70.0"
                sha256: "sha1.70.0"
            patches:
              "1.70.0":
                - patch_file: "001-1.70.0.patch"
                  base_path: "source_subfolder/1.70.0"
                - url: "https://fake_url.com/custom.patch"
                  sha256: "sha_custom"
                  base_path: "source_subfolder"
              "1.71.0":
                - patch_file: "001-1.71.0.patch"
                  base_path: "source_subfolder/1.71.0"
            """)
        expected_conandata_1690 = {
            "sources":
                {
                    "1.69.0":
                        {
                            "url": "url1.69.0",
                            "sha256": "sha1.69.0"
                        }
                }
            }
        expected_conandata_1700 = {
            "sources":
                {
                    "1.70.0":
                        {
                            "url": "url1.70.0",
                            "sha256": "sha1.70.0"
                        }
                },
            "patches":
                {
                    "1.70.0":
                        [
                            {
                                "patch_file": "001-1.70.0.patch",
                                "base_path": "source_subfolder/1.70.0"
                            },
                            {
                                "url": "https://fake_url.com/custom.patch",
                                "sha256": "sha_custom",
                                "base_path": "source_subfolder"
                            }
                        ]
                }
            }
        expected_conandata_1710 = {
            "patches":
                {
                    "1.71.0":
                        [
                            {
                                "patch_file": "001-1.71.0.patch",
                                "base_path": "source_subfolder/1.71.0"
                            }
                        ]
                }
            }
        tools.save('conandata.yml', content=conandata)
        for version in ["1.69.0", "1.70.0", "1.71.0"]:
            export_output = self.conan(['export', '.', 'name/%s@jgsogo/test' % version])
            self.assertNotIn("ERROR: [CONANDATA.YML FORMAT (KB-H030)]", export_output)
            output = self.conan(['get', 'name/%s@jgsogo/test' % version, 'conandata.yml'])
            conandata = yaml.safe_load(output)

            if version == "1.69.0":
                self.assertEqual(expected_conandata_1690, conandata)
            if version == "1.70.0":
                self.assertEqual(expected_conandata_1700, conandata)
            if version == "1.71.0":
                self.assertEqual(expected_conandata_1710, conandata)

    def test_wrong_conandata_format(self):
        tools.save('conanfile.py', content=self.conanfile)
        conandata_sources = textwrap.dedent("""
            sources:
              "1.70.0":
                url: "url1.69.0"
                sha256: "sha1.69.0"
                other: "more_data"
            """)
        conandata_patches = textwrap.dedent("""
            patches:
              "1.70.0":
                patches: "1.70.0.patch"
            """)
        conandata_random = textwrap.dedent("""
            random_field: "random"
                    """)
        conandata_patches_specific = textwrap.dedent("""
            patches:
              "1.70.0":
                - patch_file: "001-1.70.0.patch"
                  base_path: "source_subfolder/1.70.0"
                  other_field: "whatever"
                - url: "https://fake_url.com/custom.patch"
                  checksum: "sha_custom"
                  base_path: "source_subfolder"
            """)
        for conandata in [conandata_random, conandata_sources, conandata_patches,
                          conandata_patches_specific]:
            print(conandata)
            tools.save('conandata.yml', content=conandata)
            output = self.conan(['export', '.', 'name/1.70.0@jgsogo/test'])
            self.assertIn("ERROR: [CONANDATA.YML FORMAT (KB-H030)]", output)

            if conandata == conandata_random:
                self.assertIn("First level entries ['random_field'] not allowed. Use only first "
                              "level entries ['sources', 'patches'] in conandata.yml", output)
            if conandata == conandata_sources:
                self.assertNotIn("First level entries", output)
                self.assertIn("Additional entry ['other'] not allowed in 'sources':'1.70.0' of "
                              "conandata.yml", output)
            if conandata == conandata_patches:
                self.assertNotIn("First level entries", output)
                self.assertIn("Additional entries ['patches'] not allowed in 'patches':'1.70.0' "
                              "of conandata.yml", output)
            if conandata == conandata_patches_specific:
                self.assertNotIn("First level entries", output)
                self.assertIn("Additional entries ['other_field'] not allowed in 'patches':'1.70.0' "
                              "of conandata.yml", output)
