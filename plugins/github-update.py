#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

from conans import tools
from conans.client import conan_api
import os
import requests
import subprocess
import re
import json


def pre_export(output, conanfile, conanfile_path, reference, **kwargs):
    workdir = os.path.dirname(conanfile_path)
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        output.info('no GITHUB_TOKEN environment variable is set, skipping GitHub updater')
        return

    conan_instance, _, _ = conan_api.Conan.factory()
    recipe_info = conan_instance.inspect(path=conanfile_path, attributes=None)
    description = recipe_info['description']
    url = recipe_info['url']

    pattern_https = re.compile(r'https://github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)(\.git)?')
    pattern_git = re.compile(r'git@github\.com:([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)(\.git)?')
    match = pattern_https.match(url) or pattern_git.match(url)
    if not match:
        output.info('not a GitHub repository %s, skipping GitHub updater' % url)
        return
    owner, repository = match.groups(0)[0], match.groups(0)[1]

    # TODO : conan 1.9
    # tags = recipe_info['tags']
    # homepage = recipe_info['homepage']

    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': 'token %s' % github_token
    }

    request = dict()
    request['name'] = repository
    request['description'] = description
    url = 'https://api.github.com/repos/{owner}/{repository}'.format(owner=owner, repository=repository)
    response = requests.patch(url, headers=headers, data=json.dumps(request))
    if response.status_code != 200:
        output.error('GitHub PATCH request failed with %s %s' % (response.status_code, response.content))
