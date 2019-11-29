# coding=utf-8

import os
import textwrap

import six
from parameterized import parameterized

from conans import tools
from conans.client.command import ERROR_GENERAL, SUCCESS
from conans.tools import environment_append
from tests.utils.test_cases.conan_client import ConanClientTestCase


class RecipeLinterTests(ConanClientTestCase):
    conanfile = textwrap.dedent("""\
        from conans import ConanFile, tools
        
        class TestConan(ConanFile):
            name = "name"
            version = "version"
            
            def build(self):
                print("Hello world")    
                for k, v in {}.iteritems():
                    pass
                tools.msvc_build_command(self.settings, "path")
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(RecipeLinterTests, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(
            __file__), '..', '..', 'hooks', 'recipe_linter')})
        return kwargs

    @parameterized.expand([(False, ), (True, )])
    def test_basic(self, pylint_werr):
        tools.save('conanfile.py', content=self.conanfile)
        pylint_werr_value = "1" if pylint_werr else None
        with environment_append({"CONAN_PYLINT_WERR": pylint_werr_value}):
            return_code = ERROR_GENERAL if pylint_werr else SUCCESS
            output = self.conan(['export', '.', 'name/version@'], expected_return_code=return_code)

            if pylint_werr:
                self.assertIn("pre_export(): Package recipe has linter errors."
                              " Please fix them.", output)

            if six.PY2:
                self.assertIn("pre_export(): conanfile.py:8:8:"
                              " E1601: print statement used (print-statement)", output)
                self.assertIn("pre_export(): conanfile.py:9:20:"
                              " W1620: Calling a dict.iter*() method (dict-iter-method)", output)

            self.assertIn("pre_export(): conanfile.py:9:20:"
                          " W1620: Calling a dict.iter*() method (dict-iter-method)", output)
            self.assertIn("pre_export(): conanfile.py:9:20:"
                          " E1101: Instance of 'dict' has no 'iteritems' member (no-member)", output)
            self.assertIn("pre_export(): conanfile.py:9:12:"
                          " W0612: Unused variable 'k' (unused-variable)", output)
            self.assertIn("pre_export(): conanfile.py:9:15:"
                          " W0612: Unused variable 'v' (unused-variable)", output)

    def test_custom_rcfile(self):
        tools.save('conanfile.py', content=self.conanfile)
        tools.save('pylintrc', content="[FORMAT]\nindent-string='  '")

        with environment_append({"CONAN_PYLINTRC": os.path.join(os.getcwd(), "pylintrc")}):
            output = self.conan(['export', '.', 'name/version@'])

        self.assertIn("pre_export(): conanfile.py:4:0: "
                      "W0311: Bad indentation. Found 4 spaces, expected 2 (bad-indentation)", output)

    def test_custom_plugin(self):
        conanfile = textwrap.dedent("""
            from conans import ConanFile

            class Recipe(ConanFile):
                def build(self):
                    self.output.info(self.source_folder)
        """)
        tools.save('conanfile.py', content=conanfile)
        with environment_append({"CONAN_PYLINT_WERR": "1"}):
            # With the default 'python_plugin' it doesn't raise
            with environment_append({"CONAN_PYLINT_RECIPE_PLUGINS": None}):
                output = self.conan(['export', '.', 'consumer/version@'])
                self.assertIn("pre_export(): Lint recipe", output)  # Hook run without errors

            # With a custom one, it should fail
            tools.save("plugin_empty.py", content="def register(_):\n\tpass")
            with environment_append({"CONAN_PYLINT_RECIPE_PLUGINS": "plugin_empty"}):
                output = self.conan(['export', '.', 'consumer/other@'], expected_return_code=ERROR_GENERAL)
                self.assertIn("pre_export(): Package recipe has linter errors."
                              " Please fix them.", output)

    def test_dynamic_fields(self):
        conanfile = textwrap.dedent("""
            from conans import ConanFile, python_requires
            
            base = python_requires("name/version")
            
            class TestConan(ConanFile):
                name = "consumer"
                version = "version"
                
                def build(self):
                    self.output.info(self.source_folder)
                    self.output.info(self.package_folder)
                    self.output.info(self.build_folder)
                    self.output.info(self.install_folder)
                    
                def package(self):
                    self.copy("*")
                    
                def package_id(self):
                    self.info.header_only()
                    
                def build_id(self):
                    self.output.info(str(self.info_build))
                    
                def build_requirements(self):
                    self.build_requires("name/version")
                    
                def requirements(self):
                    self.requires("name/version")
                    
                def deploy(self):
                    self.copy_deps("*.dll")
            """)
        tools.save('require.py', self.conanfile)
        self.conan(['export', 'require.py', 'name/version@'])

        tools.save('consumer.py', content=conanfile)
        with environment_append({"CONAN_PYLINT_WERR": "1"}):
            output = self.conan(['export', 'consumer.py', 'consumer/version@'])
            self.assertIn("pre_export(): Lint recipe", output)  # Hook run without errors
            self.assertNotIn("(no-member)", output)

    def test_catch_them_all(self):
        conanfile = textwrap.dedent("""
            from conans import ConanFile
            class BaseConan(ConanFile):

                def source(self):
                    try:
                        raise Exception("Pikaaaaa!!")
                    except:
                        print("I got pikachu!!")
                    try:
                        raise Exception("Pikaaaaa!!")
                    except Exception:
                        print("I got pikachu!!")
            """)

        tools.save('conanfile.py', content=conanfile)
        with environment_append({"CONAN_PYLINT_WERR": "1"}):
            output = self.conan(['export', '.', 'consumer/version@'])
            self.assertIn("pre_export(): Lint recipe", output)  # Hook run without errors
            self.assertNotIn("no-member", output)
            self.assertNotIn("bare-except", output)
            self.assertNotIn("broad-except", output)

    def test_conan_data(self):
        conanfile = textwrap.dedent("""
            from conans import ConanFile
        
            class ExampleConan(ConanFile):
    
                def build(self):
                    print(self.conan_data["sources"][float(self.version)])
            """)
        tools.save('conanfile.py', content=conanfile)
        with environment_append({"CONAN_PYLINT_WERR": "1"}):
            output = self.conan(['export', '.', 'consumer/version@'])
            self.assertIn("pre_export(): Lint recipe", output)  # Hook run without errors
            self.assertNotIn("no-member", output)
