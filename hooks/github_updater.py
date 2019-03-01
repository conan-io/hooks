#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Github project updater

This Conan hook reads your recipe and updates its Github project info using the attributes.

It's necessary pass Github API Token by environment variables:
  - GITHUB_TOKEN: Github API Token

The token can be obtained by https://github.com/settings/tokens

The hook is automatically called when export command is executed:

    $ conan export . package/0.1.0@user/channel
    [HOOK - github_updater.py] pre_export(): The attributes are up-to-date.
    [HOOK - github_updater.py] pre_export(): The topics are up-to-date.
    Exporting package recipe
"""
import os
import re
from collections import namedtuple
import requests
from conans.errors import ConanException

# Github repository metadata
GithubRepo = namedtuple("GithubRepo", "owner repository")
# Github repository URL
GithubAddress = namedtuple("GithubAddress", "url headers")


def _create_github_address(github_repo, token):
    """ Retrieve Github's repo URL and headed needed
        https://developer.github.com/v3/repos/#edit
    :param github_repo: GithubRepo instance
    :param token: Github API Token
    :return: GithubAddress instance with headers and URL
    """
    headers = {'Accept': 'application/vnd.github.v3+json', 'Authorization': 'token %s' % token}
    url = 'https://api.github.com/repos/{}/{}'.format(github_repo.owner, github_repo.repository)
    return GithubAddress(url, headers)


def _create_githubrepo(conanfile):
    """ Extract the owner and repository name based on URL present in the recipe
    :param conanfile: Conan recipe instance
    :return: GithubRepo with repository information. Otherwise, None.
    """
    url = conanfile.url
    if not url:
        raise ConanException(
            'No url attribute was specified withing recipe, skipping GitHub updater.')

    pattern_https = re.compile(r'https?://github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)(\.git)?')
    pattern_git = re.compile(r'git@github\.com:([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)(\.git)?')
    match = pattern_https.match(url) or pattern_git.match(url)
    if not match:
        raise ConanException('Not a GitHub repository: "%s", skipping GitHub updater.' % url)

    return GithubRepo(match.groups(0)[0], match.groups(0)[1])


def _update_attribute(output, conanfile, github_repo, github_address):
    """ Update outdated attributes on Github.
        Both homepage and description are extracted from Conan recipe and comparated
        to Github information.
    :param output: Conan output instance
    :param conanfile: Conan recipe instance
    :param github_repo: GithubRepo instance
    :param github_address: GithubAddress instance
    """
    if conanfile.description is None or conanfile.homepage is None:
        raise ConanException("The attributes description and homepage are not configured in the recipe.")

    response = requests.get(github_address.url, headers=github_address.headers)
    if not response.ok:
        raise ConanException('GitHub GET request failed ({}): {}.'.format(response.status_code, response.text))

    metadata = response.json()
    attributes = ["homepage", "description"]
    request = {}

    for attribute in attributes:
        recipe_attr_value = getattr(conanfile, attribute)
        if recipe_attr_value != metadata[attribute]:
            request[attribute] = recipe_attr_value

    if request:
        request['name'] = github_repo.repository
        output.warn("The attributes {} are outdated and they will be updated.".format(
            ", ".join(sorted(request))))
        response = requests.patch(github_address.url, headers=github_address.headers, json=request)
        if not response.ok:
            raise ConanException("GitHub PATCH request failed with ({}): {}.".format(
                response.status_code, response.text))
        output.info("The attributes have been updated with success.")
    else:
        output.info("The attributes are up-to-date.")


def _update_topics(output, conanfile, github_address):
    """ Update outdated topics on Github.
        The topics are extracted from Conan recipe and comparated against to Github.
        https://developer.github.com/v3/repos/#replace-all-topics-for-a-repository
    :param output: Conan output instance
    :param conanfile: Conan recipe instance
    :param headers: HTTP Header needed to request data
    :param url: Github project URL
    """
    topics = conanfile.topics
    if not topics or not isinstance(topics, tuple):
        raise ConanException('No topics were found in conan recipe.')

    url = github_address.url + '/topics'
    headers = github_address.headers
    headers["Accept"] = "application/vnd.github.mercy-preview+json"

    response = requests.get(url=url, headers=headers)
    if not response.ok:
        raise ConanException("GitHub GET request failed with ({}): {}.".format(
            response.status_code, response.text))
    metadata = response.json()

    if set(metadata["names"]) != set(topics):
        metadata["names"] = topics
        output.warn("The topics are outdated and they will be updated to {}.".format(", ".join(
            metadata["names"])))
        response = requests.put(url, headers=headers, json=metadata)
        if not response.ok:
            raise ConanException("GitHub PUT request failed with ({}): {}.".format(
                response.status_code, response.text))
        output.info("The topics have been updated with success.")
    else:
        output.info("The topics are up-to-date.")


def _get_github_token():
    """ Retrieve the Github API Token environment variable
        To obtain a token, please visit: https://github.com/settings/tokens
    :return: Github Token content
    """
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        raise ConanException(
            'No GITHUB_TOKEN environment variable is set, skipping GitHub updater.')
    return github_token


def pre_export(output, conanfile, conanfile_path, reference, **kwargs):
    """ Update Github project metadata based on conanfile
    :param output: Conan output instance
    :param conanfile: Conan recipe instance
    :param conanfile_path: Conan recipe path
    :param reference: Conan package reference
    :param Kwargs: Extra arguments
    """
    del conanfile_path, reference, kwargs

    try:
        github_token = _get_github_token()
        github_repo = _create_githubrepo(conanfile)
        github_address = _create_github_address(github_repo, github_token)
        _update_attribute(output, conanfile, github_repo, github_address)
        _update_topics(output, conanfile, github_address)
    except Exception as error:
        output.error(str(error))
