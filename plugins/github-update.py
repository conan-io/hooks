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
    if not os.path.isdir(os.path.join(workdir, '.git')):
        output.info('directory "%s" is not a git repository, skipping GitHub updater')
        return
    if not tools.which('git'):
        output.info('no git executable was found in PATH, skipping GitHub updater')
        return
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        output.info('no GITHUB_TOKEN environment variable is set, skipping GitHub updater')
        return
    try:
        command = ['git', 'remote', 'get-url', 'origin']
        remote_url = subprocess.check_output(command, cwd=workdir).decode().strip()
    except subprocess.CalledProcessError as e:
        output.error('command "%s" failed with error %s' % (' '.join(command), e))
        return
    pattern_https = re.compile(r'https://github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)\.git')
    pattern_git = re.compile(r'git@github\.com:([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)\.git')
    match = pattern_https.match(remote_url) or pattern_git.match(remote_url)
    if not match:
        output.info('not a GitHub repository %s, skipping GitHub updater' % remote_url)
        return
    owner, repository = match.groups(0)

    conan_instance, _, _ = conan_api.Conan.factory()
    recipe_info = conan_instance.inspect(path=conanfile_path, attributes=None)
    description = recipe_info['description']
    # TODO : conan 1.9
    # tags = recipe_info['tags']
    # homepage = recipe_info['homepage']
    print(description)

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
