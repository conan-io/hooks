#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import textwrap
import requests_mock

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


_GITHUB_REPO_DATA = {
  "id": 123319426,
  "node_id": "MDEwOlJlcG9zaXRvcnkxMjMzMTk0MjY=",
  "name": "conan-dummy",
  "full_name": "foobar/conan-dummy",
  "private": False,
  "owner": {
    "login": "foobar",
    "id": 30303241,
    "node_id": "MDEyOk9yZ2FuaXphdGlvbjMwMzAzMjQx",
    "avatar_url": "https://avatars3.githubusercontent.com/u/30303241?v=4",
    "gravatar_id": "",
    "url": "https://api.github.com/users/foobar",
    "html_url": "https://github.com/foobar",
    "followers_url": "https://api.github.com/users/foobar/followers",
    "following_url": "https://api.github.com/users/foobar/following{/other_user}",
    "gists_url": "https://api.github.com/users/foobar/gists{/gist_id}",
    "starred_url": "https://api.github.com/users/foobar/starred{/owner}{/repo}",
    "subscriptions_url": "https://api.github.com/users/foobar/subscriptions",
    "organizations_url": "https://api.github.com/users/foobar/orgs",
    "repos_url": "https://api.github.com/users/foobar/repos",
    "events_url": "https://api.github.com/users/foobar/events{/privacy}",
    "received_events_url": "https://api.github.com/users/foobar/received_events",
    "type": "Organization",
    "site_admin": False
  },
  "html_url": "https://github.com/foobar/conan-dummy",
  "description": "Dummny Conan recipe",
  "fork": False,
  "url": "https://api.github.com/repos/foobar/conan-dummy",
  "forks_url": "https://api.github.com/repos/foobar/conan-dummy/forks",
  "keys_url": "https://api.github.com/repos/foobar/conan-dummy/keys{/key_id}",
  "collaborators_url": "https://api.github.com/repos/foobar/conan-dummy/collaborators{/collaborator}",
  "teams_url": "https://api.github.com/repos/foobar/conan-dummy/teams",
  "hooks_url": "https://api.github.com/repos/foobar/conan-dummy/hooks",
  "issue_events_url": "https://api.github.com/repos/foobar/conan-dummy/issues/events{/number}",
  "events_url": "https://api.github.com/repos/foobar/conan-dummy/events",
  "assignees_url": "https://api.github.com/repos/foobar/conan-dummy/assignees{/user}",
  "branches_url": "https://api.github.com/repos/foobar/conan-dummy/branches{/branch}",
  "tags_url": "https://api.github.com/repos/foobar/conan-dummy/tags",
  "blobs_url": "https://api.github.com/repos/foobar/conan-dummy/git/blobs{/sha}",
  "git_tags_url": "https://api.github.com/repos/foobar/conan-dummy/git/tags{/sha}",
  "git_refs_url": "https://api.github.com/repos/foobar/conan-dummy/git/refs{/sha}",
  "trees_url": "https://api.github.com/repos/foobar/conan-dummy/git/trees{/sha}",
  "statuses_url": "https://api.github.com/repos/foobar/conan-dummy/statuses/{sha}",
  "languages_url": "https://api.github.com/repos/foobar/conan-dummy/languages",
  "stargazers_url": "https://api.github.com/repos/foobar/conan-dummy/stargazers",
  "contributors_url": "https://api.github.com/repos/foobar/conan-dummy/contributors",
  "subscribers_url": "https://api.github.com/repos/foobar/conan-dummy/subscribers",
  "subscription_url": "https://api.github.com/repos/foobar/conan-dummy/subscription",
  "commits_url": "https://api.github.com/repos/foobar/conan-dummy/commits{/sha}",
  "git_commits_url": "https://api.github.com/repos/foobar/conan-dummy/git/commits{/sha}",
  "comments_url": "https://api.github.com/repos/foobar/conan-dummy/comments{/number}",
  "issue_comment_url": "https://api.github.com/repos/foobar/conan-dummy/issues/comments{/number}",
  "contents_url": "https://api.github.com/repos/foobar/conan-dummy/contents/{+path}",
  "compare_url": "https://api.github.com/repos/foobar/conan-dummy/compare/{base}...{head}",
  "merges_url": "https://api.github.com/repos/foobar/conan-dummy/merges",
  "archive_url": "https://api.github.com/repos/foobar/conan-dummy/{archive_format}{/ref}",
  "downloads_url": "https://api.github.com/repos/foobar/conan-dummy/downloads",
  "issues_url": "https://api.github.com/repos/foobar/conan-dummy/issues{/number}",
  "pulls_url": "https://api.github.com/repos/foobar/conan-dummy/pulls{/number}",
  "milestones_url": "https://api.github.com/repos/foobar/conan-dummy/milestones{/number}",
  "notifications_url": "https://api.github.com/repos/foobar/conan-dummy/notifications{?since,all,participating}",
  "labels_url": "https://api.github.com/repos/foobar/conan-dummy/labels{/name}",
  "releases_url": "https://api.github.com/repos/foobar/conan-dummy/releases{/id}",
  "deployments_url": "https://api.github.com/repos/foobar/conan-dummy/deployments",
  "created_at": "2018-02-28T17:37:52Z",
  "updated_at": "2018-12-04T20:21:50Z",
  "pushed_at": "2019-02-15T14:26:40Z",
  "git_url": "git://github.com/foobar/conan-dummy.git",
  "ssh_url": "git@github.com:foobar/conan-dummy.git",
  "clone_url": "https://github.com/foobar/conan-dummy.git",
  "svn_url": "https://github.com/foobar/conan-dummy",
  "homepage": "https://foobar.org",
  "size": 29,
  "stargazers_count": 1,
  "watchers_count": 1,
  "language": "Python",
  "has_issues": False,
  "has_projects": False,
  "has_downloads": True,
  "has_wiki": False,
  "has_pages": False,
  "forks_count": 5,
  "mirror_url": None,
  "archived": False,
  "open_issues_count": 1,
  "license": {
    "key": "mit",
    "name": "MIT License",
    "spdx_id": "MIT",
    "url": "https://api.github.com/licenses/mit",
    "node_id": "MDc6TGljZW5zZTEz"
  },
  "forks": 5,
  "open_issues": 1,
  "watchers": 1,
  "default_branch": "release/0.1.0",
  "organization": {
    "login": "foobar",
    "id": 30303241,
    "node_id": "MDEyOk9yZ2FuaXphdGlvbjMwMzAzMjQx",
    "avatar_url": "https://avatars3.githubusercontent.com/u/30303241?v=4",
    "gravatar_id": "",
    "url": "https://api.github.com/users/foobar",
    "html_url": "https://github.com/foobar",
    "followers_url": "https://api.github.com/users/foobar/followers",
    "following_url": "https://api.github.com/users/foobar/following{/other_user}",
    "gists_url": "https://api.github.com/users/foobar/gists{/gist_id}",
    "starred_url": "https://api.github.com/users/foobar/starred{/owner}{/repo}",
    "subscriptions_url": "https://api.github.com/users/foobar/subscriptions",
    "organizations_url": "https://api.github.com/users/foobar/orgs",
    "repos_url": "https://api.github.com/users/foobar/repos",
    "events_url": "https://api.github.com/users/foobar/events{/privacy}",
    "received_events_url": "https://api.github.com/users/foobar/received_events",
    "type": "Organization",
    "site_admin": False
  },
  "network_count": 5,
  "subscribers_count": 5
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
        tools.save('conanfile.py', content=self.conanfile_base)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/testing'])
        self.assertIn("pre_export(): ERROR: No GITHUB_TOKEN environment variable is set, skipping GitHub updater", output)


@requests_mock.Mocker()
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

    def test_complete_attributes(self, mock):
        mock.register_uri('GET', 'https://api.github.com/repos/foobar/conan-dummy', json=_GITHUB_REPO_DATA)
        mock.register_uri('GET', 'https://api.github.com/repos/foobar/conan-dummy/topics', json=_GITHUB_TOPICS_DATA)
        mock.register_uri('PATCH', 'https://api.github.com/repos/foobar/conan-dummy')
        mock.register_uri('PUT', 'https://api.github.com/repos/foobar/conan-dummy/topics')
        tools.save('conanfile.py', content=self.conanfile_complete)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/stable'])
        self.assertIn('WARN: The attributes description, homepage, name are outdated and it will be updated.', output)
        self.assertIn('pre_export(): The attributes have been updated with success.', output)
        self.assertIn('WARN: The topics are outdated and they will be updated to conan, dummy, qux, baz.', output)
        self.assertIn('pre_export(): The topics have been updated with success.', output)

    def test_updated_project(self, mock):
        mock.register_uri('GET', 'https://api.github.com/repos/foobar/conan-dummy', json=_GITHUB_REPO_DATA_UPDATED)
        mock.register_uri('GET', 'https://api.github.com/repos/foobar/conan-dummy/topics', json=_GITHUB_TOPICS_DATA_UPDATED)
        mock.register_uri('PATCH', 'https://api.github.com/repos/foobar/conan-dummy')
        mock.register_uri('PUT', 'https://api.github.com/repos/foobar/conan-dummy/topics')
        tools.save('conanfile.py', content=self.conanfile_complete)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/stable'])
        self.assertIn('pre_export(): The attributes are up-to-date.', output)
        self.assertIn('pre_export(): The topics are up-to-date.', output)

    def test_unauthorized(self, mock):
        mock.register_uri('GET', 'https://api.github.com/repos/foobar/conan-dummy', json={"message": "401 Unauthorized"}, status_code=401)
        tools.save('conanfile.py', content=self.conanfile_complete)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/stable'])
        self.assertIn('pre_export(): ERROR: GitHub GET request failed (401): {"message": "401 Unauthorized"}', output)

    def test_no_url_attribute(self, _):
        tools.save('conanfile.py', content=self.conanfile_basic)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/testing'])
        self.assertIn("ERROR: No url attribute was specified withing recipe, skipping GitHub updater.", output)

    def test_no_homepage_attribute(self, mock):
        mock.register_uri('GET', 'https://api.github.com/repos/foobar/conan-dummy', json=_GITHUB_REPO_DATA)
        tools.save('conanfile.py', content=self.conanfile_url)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/testing'])
        self.assertIn('ERROR: The attributes description, homepage are not configured in the recipe.', output)

    def test_invalid_url(self, mock):
        tools.save('conanfile.py', content=self.conanfile_invalid_url)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/testing'])
        self.assertIn('ERROR: Not a GitHub repository: "https://gitlab.com/foobar/conan-dummy", skipping GitHub updater.', output)

    def test_failed_attribute_update(self, mock):
        mock.register_uri('GET', 'https://api.github.com/repos/foobar/conan-dummy', json=_GITHUB_REPO_DATA)
        mock.register_uri('PATCH', 'https://api.github.com/repos/foobar/conan-dummy', status_code=500, json={"message": "Internal Server Error"})
        tools.save('conanfile.py', content=self.conanfile_complete)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/stable'])
        self.assertIn('WARN: The attributes description, homepage, name are outdated and it will be updated.', output)
        self.assertIn('pre_export(): ERROR: GitHub PATCH request failed with (500): {"message": "Internal Server Error"}.', output)

    def test_no_topics(self, mock):
        mock.register_uri('GET', 'https://api.github.com/repos/foobar/conan-dummy', json=_GITHUB_REPO_DATA)
        mock.register_uri('PATCH', 'https://api.github.com/repos/foobar/conan-dummy')
        tools.save('conanfile.py', content=self.conanfile_no_topics)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/stable'])
        self.assertIn('WARN: The attributes description, homepage, name are outdated and it will be updated.', output)
        self.assertIn('pre_export(): The attributes have been updated with success.', output)
        self.assertIn('pre_export(): ERROR: No topics were found in conan recipe.', output)

    def test_failed_topics_get(self, mock):
        mock.register_uri('GET', 'https://api.github.com/repos/foobar/conan-dummy', json=_GITHUB_REPO_DATA)
        mock.register_uri('PATCH', 'https://api.github.com/repos/foobar/conan-dummy')
        mock.register_uri('GET', 'https://api.github.com/repos/foobar/conan-dummy/topics', status_code=500, json={"message": "Internal Server Error"})
        tools.save('conanfile.py', content=self.conanfile_complete)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/stable'])
        self.assertIn('WARN: The attributes description, homepage, name are outdated and it will be updated.', output)
        self.assertIn('pre_export(): The attributes have been updated with success.', output)
        self.assertIn('pre_export(): ERROR: GitHub GET request failed with (500): {"message": "Internal Server Error"}', output)

    def test_failed_topics_put(self, mock):
        mock.register_uri('GET', 'https://api.github.com/repos/foobar/conan-dummy', json=_GITHUB_REPO_DATA)
        mock.register_uri('GET', 'https://api.github.com/repos/foobar/conan-dummy/topics', json=_GITHUB_TOPICS_DATA)
        mock.register_uri('PATCH', 'https://api.github.com/repos/foobar/conan-dummy')
        mock.register_uri('PUT', 'https://api.github.com/repos/foobar/conan-dummy/topics', status_code=500, json={"message": "Internal Server Error"})
        tools.save('conanfile.py', content=self.conanfile_complete)
        output = self.conan(['export', '.', 'name/0.1.0@foobar/stable'])
        self.assertIn('WARN: The attributes description, homepage, name are outdated and it will be updated.', output)
        self.assertIn('pre_export(): The attributes have been updated with success.', output)
        self.assertIn('pre_export(): ERROR: GitHub PUT request failed with (500): {"message": "Internal Server Error"}.', output)
        self.assertIn('pre_export(): WARN: The topics are outdated and they will be updated to conan, dummy, qux, baz.', output)
