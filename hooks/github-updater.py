#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import tools
import os
import requests
import re
import json


def pre_export(output, conanfile, conanfile_path, reference, **kwargs):
    del conanfile_path, reference, kwargs

    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        output.info('no GITHUB_TOKEN environment variable is set, skipping GitHub updater')
        return

    url = conanfile.url
    if not url:
        output.info('no url attribute was specified withing recipe, skipping GitHub updater')
        return

    pattern_https = re.compile(r'https?://github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)(\.git)?')
    pattern_git = re.compile(r'git@github\.com:([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)(\.git)?')
    match = pattern_https.match(url) or pattern_git.match(url)
    if not match:
        output.info('not a GitHub repository %s, skipping GitHub updater' % url)
        return

    owner, repository = match.groups(0)[0], match.groups(0)[1]

    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': 'token %s' % github_token
    }

    # https://developer.github.com/v3/repos/#edit
    url = 'https://api.github.com/repos/{owner}/{repository}'.format(owner=owner,
                                                                     repository=repository)

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        output.error('GitHub GET request failed with %s %s' % (response.status_code,
                                                               response.content))

    content = json.loads(response.content)
    default_branch = content["default_branch"]
    reference = "%s/%s" % (conanfile.channel, conanfile.version)
    if reference != default_branch:
        output.info('default "%s" branch doesn\'t match conanfile reference "%s"' % (default_branch,
                                                                                     reference))
        return

    request = dict()

    if conanfile.description:
        request['description'] = conanfile.description
    if conanfile.homepage:
        request['homepage'] = conanfile.homepage

    if not request:
        output.info('not attributes to update')
    else:
        request['name'] = repository

        response = requests.patch(url, headers=headers, data=json.dumps(request))
        if response.status_code != 200:
            output.error('GitHub PATCH request failed with %s %s' % (response.status_code,
                                                                     response.content))

    topics = conanfile.topics
    if not topics or not isinstance(topics, tuple):
        output.info('no topics to update')
    else:
        if "conan" not in topics:
            topics += ("conan",)

        # https://developer.github.com/v3/repos/#replace-all-topics-for-a-repository
        url += '/topics'
        request = {"names": topics}
        headers["Accept"] = "application/vnd.github.mercy-preview+json"

        response = requests.put(url, headers=headers, data=json.dumps(request))
        if response.status_code != 200:
            output.error('GitHub PUT request failed with %s %s' % (response.status_code,
                                                                   response.content))
