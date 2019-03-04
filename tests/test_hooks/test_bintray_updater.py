#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import textwrap
import responses

from conans import tools
from tests.utils.test_cases.conan_client import ConanClientTestCase


class BintrayUpdaterEnvironmentTest(ConanClientTestCase):
    conanfile_base = textwrap.dedent("""\
        from conans import ConanFile
        class DummyConan(ConanFile):
            pass
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(BintrayUpdaterEnvironmentTest, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', 'hooks', 'bintray_updater')})
        return kwargs

    def test_unset_github_token(self):
        tools.save('conanfile.py', content=self.conanfile_base)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/testing'])
        self.assertIn("pre_export(): ERROR: No GITHUB_TOKEN environment variable is set, skipping GitHub updater", output)


def accept_conan_upload(func):
    def wrapper(*args, **kwargs):
        responses.add(responses.GET, 'https://api.bintray.com/conan/foobar/conan/v1/ping')
        responses.add(responses.GET, 'https://api.bintray.com/conan/foobar/conan/v1/conans/dummy/0.1.0/foobar/stable/digest', json={"conanmanifest.txt":""})
        responses.add(responses.GET, 'https://api.bintray.com/conan/foobar/conan', status=404)
        responses.add(responses.GET, 'https://api.bintray.com/conan/foobar/conan/v1/users/check_credentials')
        responses.add(responses.GET, 'https://api.bintray.com/conan/foobar/conan/v1/conans/dummy/0.1.0/foobar/stable', json={})
        responses.add(responses.POST, 'https://api.bintray.com/conan/foobar/conan/v1/conans/dummy/0.1.0/foobar/stable/upload_urls', json={})
        func(*args, **kwargs)
    return wrapper

class BintrayUpdaterTest(ConanClientTestCase):
    conanfile_base = textwrap.dedent("""\
        from conans import ConanFile

        class DummyConan(ConanFile):
            {placeholder}
        """)
    conanfile_basic = conanfile_base.format(placeholder='pass')
    conanfile_complete = conanfile_base.format(placeholder="""url = "https://github.com/foobar/conan-dummy"
    description = "This a dummy library"
    homepage = "https://dummy.org"
    topics = ("conan", "dummy", "qux", "baz")
    license = "MIT"
    """)

    def _get_environ(self, **kwargs):
        kwargs = super(BintrayUpdaterTest, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', 'hooks', 'bintray_updater'),
                       'BINTRAY_USERNAME': "frogarian",
                       'BINTRAY_PASSWORD': "e91d34eb1c11aafaf44ag2e5194f29690ad6f383"})
        return kwargs


    @responses.activate
    def test_valid_upload(self):
        responses.add(responses.GET, 'https://api.bintray.com/conan/foobar/conan/v1/ping')
        responses.add(responses.GET, 'https://api.bintray.com/conan/foobar/conan/v1/conans/dummy/0.1.0/foobar/stable/digest', json={"conanmanifest.txt":""})
        responses.add(responses.GET, 'https://api.bintray.com/conan/foobar/conan', status=404)
        responses.add(responses.GET, 'https://api.bintray.com/conan/foobar/conan/v1/users/check_credentials')
        responses.add(responses.GET, 'https://api.bintray.com/conan/foobar/conan/v1/conans/dummy/0.1.0/foobar/stable', json={})
        responses.add(responses.POST, 'https://api.bintray.com/conan/foobar/conan/v1/conans/dummy/0.1.0/foobar/stable/upload_urls', json={})


        tools.save('conanfile.py', content=self.conanfile_complete)
        self.conan(['export', '.', 'dummy/0.1.0@foobar/stable'])
        self.conan(['remote', 'add', 'fake', 'https://api.bintray.com/conan/foobar/conan'])
        output = self.conan(['upload', '--remote=fake', 'dummy/0.1.0@foobar/stable'])
        self.assertIn('pre_export(): WARN: The attributes description, homepage, name are outdated and they will be updated.', output)
        self.assertIn('pre_export(): The attributes have been updated with success.', output)
        self.assertIn('pre_export(): WARN: The topics are outdated and they will be updated to conan, dummy, qux, baz.', output)
        self.assertIn('pre_export(): The topics have been updated with success.', output)

    @responses.activate
    def test_updated_project(self):
        responses.add(responses.GET, 'https://api.github.com/repos/foobar/conan-dummy')
        responses.add(responses.GET, 'https://api.github.com/repos/foobar/conan-dummy/topics')
        responses.add(responses.PATCH, 'https://api.github.com/repos/foobar/conan-dummy')
        responses.add(responses.PUT, 'https://api.github.com/repos/foobar/conan-dummy/topics')
        tools.save('conanfile.py', content=self.conanfile_complete)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/stable'])
        self.assertIn('pre_export(): The attributes are up-to-date.', output)
        self.assertIn('pre_export(): The topics are up-to-date.', output)

    @responses.activate
    def test_unauthorized(self):
        responses.add(responses.GET, 'https://api.github.com/repos/foobar/conan-dummy', json={"message": "401 Unauthorized"}, status=401)
        tools.save('conanfile.py', content=self.conanfile_complete)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/stable'])
        self.assertIn('pre_export(): ERROR: GitHub GET request failed (401): {"message": "401 Unauthorized"}', output)

    @responses.activate
    def test_no_url_attribute(self):
        tools.save('conanfile.py', content=self.conanfile_basic)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/testing'])
        self.assertIn("ERROR: No url attribute was specified withing recipe, skipping GitHub updater.", output)

    @responses.activate
    def test_no_homepage_attribute(self):
        responses.add(responses.GET, 'https://api.github.com/repos/foobar/conan-dummy')
        tools.save('conanfile.py', content=self.conanfile_url)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/testing'])
        self.assertIn('ERROR: The attributes description and homepage are not configured in the recipe.', output)

    @responses.activate
    def test_invalid_url(self):
        tools.save('conanfile.py', content=self.conanfile_invalid_url)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/testing'])
        self.assertIn('ERROR: Not a GitHub repository: "https://gitlab.com/foobar/conan-dummy", skipping GitHub updater.', output)

    @responses.activate
    def test_failed_attribute_update(self):
        responses.add(responses.GET, 'https://api.github.com/repos/foobar/conan-dummy')
        responses.add(responses.PATCH, 'https://api.github.com/repos/foobar/conan-dummy', status=500, json={"message": "Internal Server Error"})
        tools.save('conanfile.py', content=self.conanfile_complete)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/stable'])
        self.assertIn('pre_export(): WARN: The attributes description, homepage, name are outdated and they will be updated.', output)
        self.assertIn('pre_export(): ERROR: GitHub PATCH request failed with (500): {"message": "Internal Server Error"}.', output)

    @responses.activate
    def test_no_topics(self):
        responses.add(responses.GET, 'https://api.github.com/repos/foobar/conan-dummy')
        responses.add(responses.PATCH, 'https://api.github.com/repos/foobar/conan-dummy')
        tools.save('conanfile.py', content=self.conanfile_no_topics)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/stable'])
        self.assertIn('pre_export(): WARN: The attributes description, homepage, name are outdated and they will be updated.', output)
        self.assertIn('pre_export(): The attributes have been updated with success.', output)
        self.assertIn('pre_export(): ERROR: No topics were found in conan recipe.', output)

    @responses.activate
    def test_failed_topics_get(self):
        responses.add(responses.GET, 'https://api.github.com/repos/foobar/conan-dummy')
        responses.add(responses.PATCH, 'https://api.github.com/repos/foobar/conan-dummy')
        responses.add(responses.GET, 'https://api.github.com/repos/foobar/conan-dummy/topics', status=500, json={"message": "Internal Server Error"})
        tools.save('conanfile.py', content=self.conanfile_complete)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/stable'])
        self.assertIn('pre_export(): WARN: The attributes description, homepage, name are outdated and they will be updated.', output)
        self.assertIn('pre_export(): The attributes have been updated with success.', output)
        self.assertIn('pre_export(): ERROR: GitHub GET request failed with (500): {"message": "Internal Server Error"}', output)

    @responses.activate
    def test_failed_topics_put(self):
        responses.add(responses.GET, 'https://api.github.com/repos/foobar/conan-dummy')
        responses.add(responses.GET, 'https://api.github.com/repos/foobar/conan-dummy/topics')
        responses.add(responses.PATCH, 'https://api.github.com/repos/foobar/conan-dummy')
        responses.add(responses.PUT, 'https://api.github.com/repos/foobar/conan-dummy/topics', status=500, json={"message": "Internal Server Error"})
        tools.save('conanfile.py', content=self.conanfile_complete)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/stable'])
        self.assertIn('pre_export(): WARN: The attributes description, homepage, name are outdated and they will be updated.', output)
        self.assertIn('pre_export(): The attributes have been updated with success.', output)
        self.assertIn('pre_export(): ERROR: GitHub PUT request failed with (500): {"message": "Internal Server Error"}.', output)
        self.assertIn('pre_export(): WARN: The topics are outdated and they will be updated to conan, dummy, qux, baz.', output)
