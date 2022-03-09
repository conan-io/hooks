#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import textwrap
import responses

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase
from tests.utils.compat import save


_GITHUB_REPO_DATA = {
  "full_name": "foobar/conan-dummy",
  "html_url": "https://github.com/foobar/conan-dummy",
  "description": "Dummny Conan recipe",
  "homepage": "https://foobar.org",
}


_GITHUB_REPO_DATA_UPDATED = {
  "name": "conan-dummy",
  "homepage": "https://dummy.org",
  "description": "This a dummy library",
}


_GITHUB_TOPICS_DATA = {
  "names": [
    "conan",
    "barbarian",
    "atlantea-sword",
    "hyborian-age"
  ]
}

_GITHUB_TOPICS_DATA_UPDATED = {
  "names": [
    "conan",
    "dummy",
    "qux",
    "baz"
  ]
}


class GithubUpdaterEnvironmentTest(ConanClientTestCase):
    conanfile_base = textwrap.dedent("""\
        from conans import ConanFile
        class DummyConan(ConanFile):
            pass
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(GithubUpdaterEnvironmentTest, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', 'hooks', 'github_updater')})
        return kwargs

    def test_unset_github_token(self):
        save('conanfile.py', content=self.conanfile_base)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/testing'])
        self.assertIn("pre_export(): ERROR: No GITHUB_TOKEN environment variable is set, skipping GitHub updater", output)


class GithubUpdaterTest(ConanClientTestCase):
    conanfile_base = textwrap.dedent("""\
        from conans import ConanFile

        class DummyConan(ConanFile):
            {placeholder}
        """)
    conanfile_basic = conanfile_base.format(placeholder='pass')
    conanfile_url = conanfile_base.format(placeholder='url = "https://github.com/foobar/conan-dummy"')
    conanfile_invalid_url = conanfile_base.format(placeholder='url = "https://gitlab.com/foobar/conan-dummy"')
    conanfile_complete = conanfile_base.format(placeholder="""url = "https://github.com/foobar/conan-dummy"
    description = "This a dummy library"
    homepage = "https://dummy.org"
    topics = ("conan", "dummy", "qux", "baz")
    """)
    conanfile_no_topics = conanfile_base.format(placeholder="""url = "https://github.com/foobar/conan-dummy"
    description = "This a dummy library"
    homepage = "https://dummy.org"
    """)

    def _get_environ(self, **kwargs):
        kwargs = super(GithubUpdaterTest, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', 'hooks', 'github_updater'),
                       'GITHUB_TOKEN': "a5719b5cef0214351c6767bd4f7c1ee14a7d23c5"})
        return kwargs

    @responses.activate
    def test_complete_attributes(self):
        responses.add(responses.GET, 'https://api.github.com/repos/foobar/conan-dummy', json=_GITHUB_REPO_DATA)
        responses.add(responses.GET, 'https://api.github.com/repos/foobar/conan-dummy/topics', json=_GITHUB_TOPICS_DATA)
        responses.add(responses.PATCH, 'https://api.github.com/repos/foobar/conan-dummy')
        responses.add(responses.PUT, 'https://api.github.com/repos/foobar/conan-dummy/topics')
        save('conanfile.py', content=self.conanfile_complete)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/stable'])
        self.assertIn('pre_export(): WARN: The attributes description, homepage, name are outdated and they will be updated.', output)
        self.assertIn('pre_export(): The attributes have been updated with success.', output)
        self.assertIn('pre_export(): WARN: The topics are outdated and they will be updated to conan, dummy, qux, baz.', output)
        self.assertIn('pre_export(): The topics have been updated with success.', output)

    @responses.activate
    def test_updated_project(self):
        responses.add(responses.GET, 'https://api.github.com/repos/foobar/conan-dummy', json=_GITHUB_REPO_DATA_UPDATED)
        responses.add(responses.GET, 'https://api.github.com/repos/foobar/conan-dummy/topics', json=_GITHUB_TOPICS_DATA_UPDATED)
        responses.add(responses.PATCH, 'https://api.github.com/repos/foobar/conan-dummy')
        responses.add(responses.PUT, 'https://api.github.com/repos/foobar/conan-dummy/topics')
        save('conanfile.py', content=self.conanfile_complete)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/stable'])
        self.assertIn('pre_export(): The attributes are up-to-date.', output)
        self.assertIn('pre_export(): The topics are up-to-date.', output)

    @responses.activate
    def test_unauthorized(self):
        responses.add(responses.GET, 'https://api.github.com/repos/foobar/conan-dummy', json={"message": "401 Unauthorized"}, status=401)
        save('conanfile.py', content=self.conanfile_complete)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/stable'])
        self.assertIn('pre_export(): ERROR: GitHub GET request failed (401): {"message": "401 Unauthorized"}', output)

    @responses.activate
    def test_no_url_attribute(self):
        save('conanfile.py', content=self.conanfile_basic)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/testing'])
        self.assertIn("ERROR: No url attribute was specified withing recipe, skipping GitHub updater.", output)

    @responses.activate
    def test_no_homepage_attribute(self):
        responses.add(responses.GET, 'https://api.github.com/repos/foobar/conan-dummy', json=_GITHUB_REPO_DATA)
        save('conanfile.py', content=self.conanfile_url)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/testing'])
        self.assertIn('ERROR: The attributes description and homepage are not configured in the recipe.', output)

    @responses.activate
    def test_invalid_url(self):
        save('conanfile.py', content=self.conanfile_invalid_url)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/testing'])
        self.assertIn('ERROR: Not a GitHub repository: "https://gitlab.com/foobar/conan-dummy", skipping GitHub updater.', output)

    @responses.activate
    def test_failed_attribute_update(self):
        responses.add(responses.GET, 'https://api.github.com/repos/foobar/conan-dummy', json=_GITHUB_REPO_DATA)
        responses.add(responses.PATCH, 'https://api.github.com/repos/foobar/conan-dummy', status=500, json={"message": "Internal Server Error"})
        save('conanfile.py', content=self.conanfile_complete)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/stable'])
        self.assertIn('pre_export(): WARN: The attributes description, homepage, name are outdated and they will be updated.', output)
        self.assertIn('pre_export(): ERROR: GitHub PATCH request failed with (500): {"message": "Internal Server Error"}.', output)

    @responses.activate
    def test_no_topics(self):
        responses.add(responses.GET, 'https://api.github.com/repos/foobar/conan-dummy', json=_GITHUB_REPO_DATA)
        responses.add(responses.PATCH, 'https://api.github.com/repos/foobar/conan-dummy')
        save('conanfile.py', content=self.conanfile_no_topics)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/stable'])
        self.assertIn('pre_export(): WARN: The attributes description, homepage, name are outdated and they will be updated.', output)
        self.assertIn('pre_export(): The attributes have been updated with success.', output)
        self.assertIn('pre_export(): ERROR: No topics were found in conan recipe.', output)

    @responses.activate
    def test_failed_topics_get(self):
        responses.add(responses.GET, 'https://api.github.com/repos/foobar/conan-dummy', json=_GITHUB_REPO_DATA)
        responses.add(responses.PATCH, 'https://api.github.com/repos/foobar/conan-dummy')
        responses.add(responses.GET, 'https://api.github.com/repos/foobar/conan-dummy/topics', status=500, json={"message": "Internal Server Error"})
        save('conanfile.py', content=self.conanfile_complete)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/stable'])
        self.assertIn('pre_export(): WARN: The attributes description, homepage, name are outdated and they will be updated.', output)
        self.assertIn('pre_export(): The attributes have been updated with success.', output)
        self.assertIn('pre_export(): ERROR: GitHub GET request failed with (500): {"message": "Internal Server Error"}', output)

    @responses.activate
    def test_failed_topics_put(self):
        responses.add(responses.GET, 'https://api.github.com/repos/foobar/conan-dummy', json=_GITHUB_REPO_DATA)
        responses.add(responses.GET, 'https://api.github.com/repos/foobar/conan-dummy/topics', json=_GITHUB_TOPICS_DATA)
        responses.add(responses.PATCH, 'https://api.github.com/repos/foobar/conan-dummy')
        responses.add(responses.PUT, 'https://api.github.com/repos/foobar/conan-dummy/topics', status=500, json={"message": "Internal Server Error"})
        save('conanfile.py', content=self.conanfile_complete)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/stable'])
        self.assertIn('pre_export(): WARN: The attributes description, homepage, name are outdated and they will be updated.', output)
        self.assertIn('pre_export(): The attributes have been updated with success.', output)
        self.assertIn('pre_export(): ERROR: GitHub PUT request failed with (500): {"message": "Internal Server Error"}.', output)
        self.assertIn('pre_export(): WARN: The topics are outdated and they will be updated to conan, dummy, qux, baz.', output)
