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

        conanfile = textwrap.dedent("""\
                       import os
                       from conans import ConanFile, tools

                       class AConan(ConanFile):

                           def source(self):
                               tools.download(self.conan_data["sources"]["all"]["url"])
                       """)
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['create', '.', 'name/version@user/channel'], expected_return_code=1)
        self.assertIn("[IMMUTABLE SOURCES (KB-H010)] OK", output)

    def _check_conandata(self, conandata):
        tools.save('conanfile.py', content=self.conanfile)
        tools.save('conandata.yml', content=conandata)
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
        tools.save('conanfile.py', content=self.conanfile)
        conandata = textwrap.dedent("""
                    sources:
                      "1.69.0":
                          url: "url1.69.0"
                          sha256: "sha256_1.69.0"
                          sha1: "md5_1.69.0"
                          md5: "sha1_1.69.0"
                          """)
        tools.save('conandata.yml', content=conandata)
        export_output = self.conan(['export', '.', 'name/1.69.0@jgsogo/test'])
        self.assertNotIn("ERROR: [CONANDATA.YML FORMAT (KB-H030)]", export_output)
        self.assertNotIn("WARN: [CONANDATA.YML FORMAT (KB-H030)]", export_output)
        self.assertIn("[CONANDATA.YML FORMAT (KB-H030)] OK", export_output)

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
            self.assertNotIn("{", output)
            conandata = yaml.safe_load(output)

            if version == "1.69.0":
                self.assertEqual(expected_conandata_1690, conandata)
            if version == "1.70.0":
                self.assertEqual(expected_conandata_1700, conandata)
            if version == "1.71.0":
                self.assertEqual(expected_conandata_1710, conandata)

    def test_versions_as_string(self):
        tools.save('conanfile.py', content=self.conanfile)
        conandata = textwrap.dedent("""
            sources:
              1.73:
                url: "url1.69.0"
        """)

        tools.save('conandata.yml', content=conandata)
        output = self.conan(['export', '.', 'name/1.70.0@jgsogo/test'])
        self.assertIn("ERROR: [CONANDATA.YML FORMAT (KB-H030)] Versions in conandata.yml should be strings", output)

    def test_unknown_field(self):
        tools.save('conanfile.py', content=self.conanfile)
        conandata = textwrap.dedent("""
            random_field: "random"
            """)
        tools.save('conandata.yml', content=conandata)
        output = self.conan(['export', '.', 'name/1.70.0@jgsogo/test'])
        self.assertIn("ERROR: [CONANDATA.YML FORMAT (KB-H030)]", output)
        self.assertIn("First level entries ['random_field'] not allowed. Use only first "
                      "level entries ['sources', 'patches'] in conandata.yml", output)

    def test_unknown_subentry_sources(self):
        tools.save('conanfile.py', content=self.conanfile)
        conandata = textwrap.dedent("""
            sources:
              "1.70.0":
                url: "url1.69.0"
                sha256: "sha1.69.0"
                other: "more_data"
            """)
        tools.save('conandata.yml', content=conandata)
        output = self.conan(['export', '.', 'name/1.70.0@jgsogo/test'])
        self.assertIn("ERROR: [CONANDATA.YML FORMAT (KB-H030)]", output)
        self.assertNotIn("First level entries", output)
        self.assertIn("Additional entries ['other'] not allowed in 'sources':'1.70.0' of "
                      "conandata.yml", output)

    def test_unknown_subentry_patches(self):
        tools.save('conanfile.py', content=self.conanfile)
        conandata = textwrap.dedent("""
            patches:
              "1.70.0":
                patches: "1.70.0.patch"
            """)
        tools.save('conandata.yml', content=conandata)
        output = self.conan(['export', '.', 'name/1.70.0@jgsogo/test'])
        self.assertIn("ERROR: [CONANDATA.YML FORMAT (KB-H030)]", output)
        self.assertNotIn("First level entries", output)
        self.assertIn("Additional entries ['patches'] not allowed in 'patches':'1.70.0' "
                      "of conandata.yml", output)

    def test_unknown_subentry_in_list(self):
        tools.save('conanfile.py', content=self.conanfile)
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
        tools.save('conandata.yml', content=conandata)
        output = self.conan(['export', '.', 'name/1.70.0@jgsogo/test'])
        self.assertIn("ERROR: [CONANDATA.YML FORMAT (KB-H030)]", output)

        self.assertNotIn("First level entries", output)
        self.assertIn("Additional entries ['other_field'] not allowed in 'patches':'1.70.0' "
                      "of conandata.yml", output)

    def test_empty_checksum(self):
        tools.save('conanfile.py', content=self.conanfile)
        conandata = textwrap.dedent("""
            sources:
              "1.70.0":
                url: "url1.69.0"
                sha256: ""
            """)
        tools.save('conandata.yml', content=conandata)
        output = self.conan(['export', '.', 'name/1.70.0@jgsogo/test'])
        self.assertIn("ERROR: [CONANDATA.YML FORMAT (KB-H030)]", output)
        self.assertIn("The entry 'sha256' cannot be empty in conandata.yml.", output)

    def test_prefer_sha256(self):
        tools.save('conanfile.py', content=self.conanfile)
        for checksum in ['md5', 'sha1']:
            conandata = textwrap.dedent(f"""
                sources:
                  "1.70.0":
                    url: "url1.69.0"
                    {checksum}: "cf23df2207d99a74fbe169e3eba035e633b65d94"
                """)
            tools.save('conandata.yml', content=conandata)
            output = self.conan(['export', '.', 'name/1.70.0@jgsogo/test'])
            self.assertIn("WARN: [CONANDATA.YML FORMAT (KB-H030)]", output)
            self.assertIn("Consider 'sha256' instead of ['md5', 'sha1']. It's considerably more secure than others.", output)

            conandata = textwrap.dedent(f"""
                            sources:
                              "1.69.0":
                                url: "url1.69.0"
                                {checksum}: "cf23df2207d99a74fbe169e3eba035e633b65d94"
                              "1.70.0":
                                url: "url1.70.0"
                                {checksum}: "cf23df2207d99a74fbe169e3eba035e633b65d94"
                            """)
            tools.save('conandata.yml', content=conandata)
            output = self.conan(['export', '.', 'name/1.70.0@jgsogo/test'])
            self.assertIn("WARN: [CONANDATA.YML FORMAT (KB-H030)]", output)
            self.assertIn("Consider 'sha256' instead of ['md5', 'sha1']. It's considerably more secure than others.",
                          output)

    def test_empty_checksum(self):
        tools.save('conanfile.py', content=self.conanfile)
        conandata = textwrap.dedent(f"""
            sources:
                "1.70.0":
                    url: "url1.69.0"
            """)
        tools.save('conandata.yml', content=conandata)
        output = self.conan(['export', '.', 'name/1.70.0@jgsogo/test'])
        self.assertIn("ERROR: [CONANDATA.YML FORMAT (KB-H030)]", output)
        self.assertIn("The checksum key 'sha256' must be declared and can not be empty.", output)

        conandata = textwrap.dedent("""
                    sources:
                      "1.69.0":
                        url: "url1.69.0"
                        sha256: "sha1.69.0"
                      "1.70.0":
                        url: "url1.70.0"
                    patches:
                      "1.70.0":
                        - patch_file: "001-1.70.0.patch"
                          base_path: "source_subfolder/1.70.0"
                    """)
        tools.save('conandata.yml', content=conandata)
        output = self.conan(['export', '.', 'name/1.70.0@jgsogo/test'])
        self.assertIn("ERROR: [CONANDATA.YML FORMAT (KB-H030)]", output)
        self.assertIn("The checksum key 'sha256' must be declared and can not be empty.", output)

    def test_zulu_openjdk(self):
        tools.save('conanfile.py', content=self.conanfile)
        conandata = textwrap.dedent("""
            sources:
              "11.0.8":
                "Windows": {
                  "url": "https://cdn.azul.com/zulu/bin/zulu11.41.23-ca-jdk11.0.8-win_x64.zip",
                  "sha256": "3602ed7bae52898c540c2d3ae3230c081cf061b219d14fb9ac15a47f4226d307",
                }
                "Linux": {
                  "url": "https://cdn.azul.com/zulu/bin/zulu11.41.23-ca-jdk11.0.8-linux_x64.tar.gz",
                  "sha256": "f8aee4ab30ca11ab3c8f401477df0e455a9d6b06f2710b2d1b1ddcf06067bc79",
                }
                "Macos": {
                  "url": "https://cdn.azul.com/zulu/bin/zulu11.41.23-ca-jdk11.0.8-macosx_x64.tar.gz",
                  "sha256": "1ed070ea9a27030bcca4d7c074dec1d205d3f3506166d36faf4d1b9e083ab365",
                }
            
              "11.0.12":
                "Windows":
                  "x86_64": {
                    "url": "https://cdn.azul.com/zulu/bin/zulu11.50.19-ca-jdk11.0.12-win_x64.zip",
                    "sha256": "42ae65e75d615a3f06a674978e1fa85fdf078cad94e553fee3e779b2b42bb015",
                  }
                "Linux":
                  "x86_64": {
                    "url": "https://cdn.azul.com/zulu/bin/zulu11.50.19-ca-jdk11.0.12-linux_x64.tar.gz",
                    "sha256": "b8e8a63b79bc312aa90f3558edbea59e71495ef1a9c340e38900dd28a1c579f3",
                  }
                "Macos":
                  "x86_64": {
                    "url": "https://cdn.azul.com/zulu/bin/zulu11.50.19-ca-jdk11.0.12-macosx_x64.tar.gz",
                    "sha256": "0b8c8b7cf89c7c55b7e2239b47201d704e8d2170884875b00f3103cf0662d6d7",
                  }
                  "armv8" : {
                    "url": "https://cdn.azul.com/zulu/bin/zulu11.50.19-ca-jdk11.0.12-macosx_aarch64.tar.gz",
                    "sha256": "e908a0b4c0da08d41c3e19230f819b364ff2e5f1dafd62d2cf991a85a34d3a17",
                  }
        """)
        tools.save('conandata.yml', content=conandata)
        output = self.conan(['export', '.', 'zulu-openjdk/11.0.12@user/testing'])
        self.assertIn("[CONANDATA.YML FORMAT (KB-H030)] OK", output)
