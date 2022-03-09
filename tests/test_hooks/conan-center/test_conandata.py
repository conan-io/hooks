import os
import textwrap
import unittest
import yaml

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase
from tests.utils.compat import save
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
        save('conanfile.py', content=self.conanfile)
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertIn("[IMMUTABLE SOURCES (KB-H010)] Create a file 'conandata.yml' file with the "
                      "sources to be downloaded.", output)

    def test_no_missing_conandata_but_not_used(self):
        save('conanfile.py', content=self.conanfile)
        save('conandata.yml', content="")
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
        save('conanfile.py', content=conanfile)
        save('conandata.yml', content=conandata)
        output = self.conan(['create', '.', 'name/version@user/channel'], expected_return_code=1)
        self.assertIn("[IMMUTABLE SOURCES (KB-H010)] OK", output)

        conanfile = textwrap.dedent("""\
                       import os
                       from conans import ConanFile, tools

                       class AConan(ConanFile):

                           def source(self):
                               tools.download(self.conan_data["sources"]["all"]["url"])
                       """)
        save('conanfile.py', content=conanfile)
        output = self.conan(['create', '.', 'name/version@user/channel'], expected_return_code=1)
        self.assertIn("[IMMUTABLE SOURCES (KB-H010)] OK", output)

    def _check_conandata(self, conandata):
        save('conanfile.py', content=self.conanfile)
        save('conandata.yml', content=conandata)
        export_output = self.conan(['export', '.', 'name/1.69.0@jgsogo/test'])
        self.assertNotIn("ERROR: [CONANDATA.YML FORMAT (KB-H030)]", export_output)
        self.assertIn("[CONANDATA.YML FORMAT (KB-H030)] OK", export_output)

    def test_single_source(self):
        conandata = textwrap.dedent("""
                    sources:
                      "1.69.0":
                            url: "url1_1.69.0"
                            sha256: "sha1_1.69.0"
                    patches:
                      "1.69.0":
                            patch_file: "001-1.69.0.patch"
                            base_path: "source_subfolder/1.69.0"
                          """)
        self._check_conandata(conandata)

    def test_single_source_mirror(self):
        conandata = textwrap.dedent("""
                    sources:
                      "1.69.0":
                            url: [
                          "mirror1/url1_1.69.0",
                          "mirror2/url1_1.69.0",
                          ]
                            sha256: "sha1_1.69.0"
                    patches:
                      "1.69.0":
                            patch_file: "001-1.69.0.patch"
                            base_path: "source_subfolder/1.69.0"
                          """)
        self._check_conandata(conandata)

    def test_multiple_sources(self):
        conandata = textwrap.dedent("""
                    sources:
                      "1.69.0":
                          - url: "url1_1.69.0"
                            sha256: "sha1_1.69.0"
                          - url: "url2_1.69.0"
                            sha256: "sha2_1.69.0"
                    patches:
                      "1.69.0":
                            patch_file: "001-1.69.0.patch"
                            base_path: "source_subfolder/1.69.0"
                          """)
        self._check_conandata(conandata)

    def test_multiple_sources_mirror(self):
        conandata = textwrap.dedent("""
                    sources:
                      "1.69.0":
                          - url: [
                          "mirror1/url1_1.69.0",
                          "mirror2/url1_1.69.0",
                          ]
                            sha256: "sha1_1.69.0"
                          - url: [
                          "mirror1/url2_1.69.0",
                          "mirror2/url2_1.69.0",
                          ]
                            sha256: "sha2_1.69.0"
                    patches:
                      "1.69.0":
                            patch_file: "001-1.69.0.patch"
                            base_path: "source_subfolder/1.69.0"
                          """)
        self._check_conandata(conandata)

    def test_different_sources_per_config_level1(self):
        conandata = textwrap.dedent("""
                    sources:
                      "1.69.0":
                          "Macos":
                              - url: "url1_1.69.0"
                                sha256: "sha1_1.69.0"
                          "Linux":
                              - url: "url2_1.69.0"
                                sha256: "sha2_1.69.0"
                    patches:
                      "1.69.0":
                          "Macos":
                                patch_file: "001-1.69.0-mac.patch"
                                base_path: "source_subfolder/1.69.0"
                          "Linux":
                                patch_file: "001-1.69.0-lin.patch"
                                base_path: "source_subfolder/1.69.0"
                          """)
        self._check_conandata(conandata)

    def test_different_sources_per_config_level1_mirror(self):
        conandata = textwrap.dedent("""
                    sources:
                      "1.69.0":
                          "Macos":
                              - url: [
                          "mirror1/url1_1.69.0",
                          "mirror2/url1_1.69.0",
                          ]
                                sha256: "sha1_1.69.0"
                          "Linux":
                              - url: [
                          "mirror1/url2_1.69.0",
                          "mirror2/url2_1.69.0",
                          ]
                                sha256: "sha2_1.69.0"
                    patches:
                      "1.69.0":
                          "Macos":
                                patch_file: "001-1.69.0-mac.patch"
                                base_path: "source_subfolder/1.69.0"
                          "Linux":
                                patch_file: "001-1.69.0-lin.patch"
                                base_path: "source_subfolder/1.69.0"
                          """)
        self._check_conandata(conandata)

    def test_different_sources_per_config_level2(self):
        conandata = textwrap.dedent("""
                    sources:
                      "1.69.0":
                          "Macos":
                              "apple-clang":
                                  - url: "url1_1.69.0"
                                    sha256: "sha1_1.69.0"
                          "Linux":
                              "gcc":
                                    url: "url2_1.69.0"
                                    sha256: "sha2_1.69.0"
                    patches:
                      "1.69.0":
                          "Macos":
                              "apple-clang":
                                    patch_file: "001-1.69.0-mac.patch"
                                    base_path: "source_subfolder/1.69.0"
                          "Linux":
                              "gcc":
                                    patch_file: "001-1.69.0-lin.patch"
                                    base_path: "source_subfolder/1.69.0"
                          """)
        self._check_conandata(conandata)

    def test_different_sources_per_config_level2_mirror(self):
        conandata = textwrap.dedent("""
                    sources:
                      "1.69.0":
                          "Macos":
                              "apple-clang":
                                  - url: [
                          "mirror1/url1_1.69.0",
                          "mirror2/url1_1.69.0",
                          ]
                                    sha256: "sha1_1.69.0"
                          "Linux":
                              "gcc":
                                  - url: [
                          "mirror1/url2_1.69.0",
                          "mirror2/url2_1.69.0",
                          ]
                                    sha256: "sha2_1.69.0"
                    patches:
                      "1.69.0":
                          "Macos":
                              "apple-clang":
                                    patch_file: "001-1.69.0-mac.patch"
                                    base_path: "source_subfolder/1.69.0"
                          "Linux":
                              "gcc":
                                    patch_file: "001-1.69.0-lin.patch"
                                    base_path: "source_subfolder/1.69.0"
                          """)
        self._check_conandata(conandata)

    def test_sha1_md5(self):
        save('conanfile.py', content=self.conanfile)
        conandata = textwrap.dedent("""
                    sources:
                      "1.69.0":
                          url: "url1.69.0"
                          sha256: "sha256_1.69.0"
                          sha1: "md5_1.69.0"
                          md5: "sha1_1.69.0"
                          """)
        save('conandata.yml', content=conandata)
        export_output = self.conan(['export', '.', 'name/1.69.0@jgsogo/test'])
        self.assertNotIn("ERROR: [CONANDATA.YML FORMAT (KB-H030)]", export_output)
        self.assertIn("[CONANDATA.YML FORMAT (KB-H030)] OK", export_output)

    def test_reduce_conandata(self):
        save('conanfile.py', content=self.conanfile)
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
        save('conandata.yml', content=conandata)
        for version in ["1.69.0", "1.70.0", "1.71.0"]:
            export_output = self.conan(['export', '.', 'name/%s@jgsogo/test' % version])
            self.assertNotIn("ERROR: [CONANDATA.YML FORMAT (KB-H030)]", export_output)
            output = self.conan(['get', 'name/%s@jgsogo/test' % version, 'conandata.yml'])
            self.assertNotIn("{", output)
            conandata = yaml.safe_load(output)

            if version == "1.69.0":
                self.assertEqual(expected_conandata_1690, conandata)
            if version == "1.70.0":
                self.assertEqual(expected_conandata_1700, conandata)
            if version == "1.71.0":
                self.assertEqual(expected_conandata_1710, conandata)

    def test_versions_as_string(self):
        save('conanfile.py', content=self.conanfile)
        conandata = textwrap.dedent("""
            sources:
              1.73:
                url: "url1.69.0"
        """)

        save('conandata.yml', content=conandata)
        output = self.conan(['export', '.', 'name/1.70.0@jgsogo/test'])
        self.assertIn("ERROR: [CONANDATA.YML FORMAT (KB-H030)] Versions in conandata.yml should be strings", output)

    def test_unknown_field(self):
        save('conanfile.py', content=self.conanfile)
        conandata = textwrap.dedent("""
            random_field: "random"
            """)
        save('conandata.yml', content=conandata)
        output = self.conan(['export', '.', 'name/1.70.0@jgsogo/test'])
        self.assertIn("ERROR: [CONANDATA.YML FORMAT (KB-H030)]", output)
        self.assertIn("First level entries ['random_field'] not allowed. Use only first "
                      "level entries ['sources', 'patches'] in conandata.yml", output)

    def test_unknown_subentry_sources(self):
        save('conanfile.py', content=self.conanfile)
        conandata = textwrap.dedent("""
            sources:
              "1.70.0":
                url: "url1.69.0"
                sha256: "sha1.69.0"
                other: "more_data"
            """)
        save('conandata.yml', content=conandata)
        output = self.conan(['export', '.', 'name/1.70.0@jgsogo/test'])
        self.assertIn("ERROR: [CONANDATA.YML FORMAT (KB-H030)]", output)
        self.assertNotIn("First level entries", output)
        self.assertIn("Additional entries ['other'] not allowed in 'sources':'1.70.0' of "
                      "conandata.yml", output)

    def test_unknown_subentry_patches(self):
        save('conanfile.py', content=self.conanfile)
        conandata = textwrap.dedent("""
            patches:
              "1.70.0":
                patches: "1.70.0.patch"
            """)
        save('conandata.yml', content=conandata)
        output = self.conan(['export', '.', 'name/1.70.0@jgsogo/test'])
        self.assertIn("ERROR: [CONANDATA.YML FORMAT (KB-H030)]", output)
        self.assertNotIn("First level entries", output)
        self.assertIn("Additional entries ['patches'] not allowed in 'patches':'1.70.0' "
                      "of conandata.yml", output)

    def test_unknown_subentry_in_list(self):
        save('conanfile.py', content=self.conanfile)
        conandata = textwrap.dedent("""
            patches:
              "1.70.0":
                - patch_file: "001-1.70.0.patch"
                  base_path: "source_subfolder/1.70.0"
                  other_field: "whatever"
                - url: "https://fake_url.com/custom.patch"
                  checksum: "sha_custom"
                  base_path: "source_subfolder"
            """)
        save('conandata.yml', content=conandata)
        output = self.conan(['export', '.', 'name/1.70.0@jgsogo/test'])
        self.assertIn("ERROR: [CONANDATA.YML FORMAT (KB-H030)]", output)

        self.assertNotIn("First level entries", output)
        self.assertIn("Additional entries ['other_field'] not allowed in 'patches':'1.70.0' "
                      "of conandata.yml", output)
