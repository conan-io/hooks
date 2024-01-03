import os
import shutil
import textwrap
import yaml
from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save


class TestKBH017(ConanClientV2TestCase):
    conanfile = textwrap.dedent("""\
                        from conan import ConanFile
                        class AConan(ConanFile):
                            pass                       
                        """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH017, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def _check_conandata(self, conandata):
        save(self, 'conanfile.py', content=self.conanfile)
        save(self, 'conandata.yml', content=conandata)
        export_output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [CONANDATA.YML FORMAT (KB-H017)]" not in export_output
        assert "[CONANDATA.YML FORMAT (KB-H017)] OK" in export_output

    def test_single_source(self):
        conandata = textwrap.dedent("""
                    sources:
                      "0.1.0":
                            url: "url1_0.1.0"
                            sha256: "sha1_0.1.0"
                    patches:
                      "1.69.0":
                            patch_file: "001-1.69.0.patch"
                            base_path: "source_subfolder/1.69.0"
                          """)
        self._check_conandata(conandata)

    def test_single_source_mirror(self):
        conandata = textwrap.dedent("""
                    sources:
                      "0.1.0":
                            url: [
                          "mirror1/url1_1.69.0",
                          "mirror2/url1_1.69.0",
                          ]
                            sha256: "sha1_1.69.0"
                    patches:
                      "0.1.0":
                            patch_file: "001-1.69.0.patch"
                            base_path: "source_subfolder/1.69.0"
                          """)
        self._check_conandata(conandata)

    def test_multiple_sources(self):
        conandata = textwrap.dedent("""
                    sources:
                      "0.1.0":
                          - url: "url1_1.69.0"
                            sha256: "sha1_1.69.0"
                          - url: "url2_1.69.0"
                            sha256: "sha2_1.69.0"
                    patches:
                      "0.1.0":
                            patch_file: "001-1.69.0.patch"
                            base_path: "source_subfolder/1.69.0"
                          """)
        self._check_conandata(conandata)

    def test_multiple_sources_mirror(self):
        conandata = textwrap.dedent("""
                    sources:
                      "0.1.0":
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
                      "0.1.0":
                            patch_file: "001-1.69.0.patch"
                            base_path: "source_subfolder/1.69.0"
                          """)
        self._check_conandata(conandata)

    def test_different_sources_per_config_level1(self):
        conandata = textwrap.dedent("""
                    sources:
                      "0.1.0":
                          "Macos":
                              - url: "url1_1.69.0"
                                sha256: "sha1_1.69.0"
                          "Linux":
                              - url: "url2_1.69.0"
                                sha256: "sha2_1.69.0"
                    patches:
                      "0.1.0":
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
                      "0.1.0":
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
                      "0.1.0":
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
                      "0.1.0":
                          "Macos":
                              "apple-clang":
                                  - url: "url1_1.69.0"
                                    sha256: "sha1_1.69.0"
                          "Linux":
                              "gcc":
                                    url: "url2_1.69.0"
                                    sha256: "sha2_1.69.0"
                    patches:
                      "0.1.0":
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
                      "0.1.0":
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
                      "0.1.0":
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
        save(self, 'conanfile.py', content=self.conanfile)
        conandata = textwrap.dedent("""
                    sources:
                      "0.1.0":
                          url: "url1.69.0"
                          sha256: "sha256_1.69.0"
                          sha1: "md5_1.69.0"
                          md5: "sha1_1.69.0"
                          """)
        save(self, 'conandata.yml', content=conandata)
        export_output = self.conan(['export', '--name=name', '--version=version', 'conanfile.py'])
        assert "ERROR: [CONANDATA.YML FORMAT (KB-H017)]" not in export_output
        assert "WARN: [CONANDATA.YML FORMAT (KB-H017)]" not in export_output
        assert "[CONANDATA.YML FORMAT (KB-H017)] OK" in export_output

    def test_versions_as_string(self):
        save(self, 'conanfile.py', content=self.conanfile)
        conandata = textwrap.dedent("""
            sources:
              1.69:
                url: "url1.69.0"                
        """)

        save(self, 'conandata.yml', content=conandata)
        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [CONANDATA.YML FORMAT (KB-H017)] Versions in conandata.yml should be strings" in output

    def test_unknown_field(self):
        save(self, 'conanfile.py', content=self.conanfile)
        conandata = textwrap.dedent("""
            random_field: "random"
            """)
        save(self, 'conandata.yml', content=conandata)
        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [CONANDATA.YML FORMAT (KB-H017)]" in output
        assert "First level entries ['random_field'] not allowed. Use only first level entries ['sources', 'patches'] in conandata.yml" in output

    def test_unknown_subentry_sources(self):
        save(self, 'conanfile.py', content=self.conanfile)
        conandata = textwrap.dedent("""
            sources:
              "0.1.0":
                url: "url1.69.0"
                sha256: "sha1.69.0"
                other: "more_data"
            """)
        save(self, 'conandata.yml', content=conandata)
        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [CONANDATA.YML FORMAT (KB-H017)] Additional entries ['other'] not allowed in 'sources':'0.1.0' of conandata.yml" in output

    def test_unknown_subentry_patches(self):
        save(self, 'conanfile.py', content=self.conanfile)
        conandata = textwrap.dedent("""
            patches:
              "0.1.0":
                patches: "0.1.0.patch"
            """)
        save(self, 'conandata.yml', content=conandata)
        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [CONANDATA.YML FORMAT (KB-H017)] Additional entries ['patches'] not allowed in 'patches':'0.1.0' of conandata.yml" in output

    def test_unknown_subentry_in_list(self):
        save(self, 'conanfile.py', content=self.conanfile)
        conandata = textwrap.dedent("""
            patches:
              "0.1.0":
                - patch_file: "001-1.70.0.patch"
                  base_path: "source_subfolder/1.70.0"
                  other_field: "whatever"
                - url: "https://fake_url.com/custom.patch"
                  checksum: "sha_custom"
                  base_path: "source_subfolder"
            """)
        save(self, 'conandata.yml', content=conandata)
        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [CONANDATA.YML FORMAT (KB-H017)] Additional entries ['other_field'] not allowed in 'patches':'0.1.0' of conandata.yml" in output

    def test_empty_checksum(self):
        save(self, 'conanfile.py', content=self.conanfile)
        conandata = textwrap.dedent("""
            sources:
              "0.1.0":
                url: "url_0.1.0"
                sha256: ""
            """)
        save(self, 'conandata.yml', content=conandata)
        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [CONANDATA.YML FORMAT (KB-H017)]" in output
        assert "The entry 'sha256' cannot be empty in conandata.yml." in output

    def test_prefer_sha256(self):
        save(self, 'conanfile.py', content=self.conanfile)
        for checksum in ['md5', 'sha1']:
            conandata = textwrap.dedent(f"""
                sources:
                  "0.1.0":
                    url: "url1.69.0"
                    {checksum}: "cf23df2207d99a74fbe169e3eba035e633b65d94"
                """)
            save(self, 'conandata.yml', content=conandata)
            output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
            assert "WARN: [CONANDATA.YML FORMAT (KB-H017)]" in output
            assert "Consider 'sha256' instead of ['md5', 'sha1']. It's considerably more secure than others." in output

            conandata = textwrap.dedent(f"""
                            sources:
                              "0.1.0":
                                url: "url1.69.0"
                                {checksum}: "cf23df2207d99a74fbe169e3eba035e633b65d94"
                              "1.70.0":
                                url: "url1.70.0"
                                {checksum}: "cf23df2207d99a74fbe169e3eba035e633b65d94"
                            """)
            save(self, 'conandata.yml', content=conandata)
            output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
            assert "WARN: [CONANDATA.YML FORMAT (KB-H017)]" in output
            assert "Consider 'sha256' instead of ['md5', 'sha1']. It's considerably more secure than others." in output

    def test_missing_checksum(self):
        save(self, 'conanfile.py', content=self.conanfile)
        conandata = textwrap.dedent(f"""
            sources:
                "0.1.0":
                    url: "url1.69.0"
            """)
        save(self, 'conandata.yml', content=conandata)
        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [CONANDATA.YML FORMAT (KB-H017)]" in output
        assert "The checksum key 'sha256' must be declared and can not be empty." in output

        conandata = textwrap.dedent("""
                    sources:
                      "1.69.0":
                        url: "url1.69.0"
                        sha256: "sha1.69.0"
                      "0.1.0":
                        url: "url1.70.0"
                    patches:
                      "1.70.0":
                        - patch_file: "001-1.70.0.patch"
                          base_path: "source_subfolder/1.70.0"
                    """)
        save(self, 'conandata.yml', content=conandata)
        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [CONANDATA.YML FORMAT (KB-H017)]" in output
        assert "The checksum key 'sha256' must be declared and can not be empty." in output

    def test_zulu_openjdk(self):
        save(self, 'conanfile.py', content=self.conanfile)
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
        save(self, 'conandata.yml', content=conandata)
        output = self.conan(['export', '--name=zulu-openjdk', '--version=11.0.12', 'conanfile.py'])
        assert "[CONANDATA.YML FORMAT (KB-H017)] OK" in output

    def test_google_source(self):
        conandata = textwrap.dedent("""
                    sources:
                      "1.69.0":
                            url: "https://chromium.googlesource.com/chromium/tools/depot_tools/+archive/48c5c9c50455c625c58dab2fbb0904cac467168c.tar.gz"
                    patches:
                      "1.69.0":
                            patch_file: "001-1.69.0.patch"
                            base_path: "source_subfolder/1.69.0"
                          """)
        self._check_conandata(conandata)

    def test_blend2d_empty_checksum(self):
        conandata = textwrap.dedent("""sources:
  "0.1.0":
    url: "https://blend2d.com/download/blend2d-beta18.zip"
    sha256: ""
  "0.0.17":
    url: "https://blend2d.com/download/blend2d-beta17.zip"
    sha256: "06ee8fb0bea281d09291e498900093139426501a1a7f09dba0ec801dd340635e"

patches:
  "0.1.0":
    - base_path: "source_subfolder"
      patch_file: "patches/0.0.17-0001-disable-embed-asmjit.patch"
  "0.0.17":
    - base_path: "source_subfolder"
      patch_file: "patches/0.0.17-0001-disable-embed-asmjit.patch"
""")
        save(self, 'conandata.yml', content=conandata)
        save(self, 'conanfile.py', content=self.conanfile)
        output = self.conan(['export', '--name=name', '--version=0.1.0', 'conanfile.py'])
        assert "ERROR: [CONANDATA.YML FORMAT (KB-H017)] The entry 'sha256' cannot be empty in conandata.yml." in output