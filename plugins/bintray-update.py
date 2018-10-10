#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import requests
from requests.auth import HTTPBasicAuth
from conans.client import conan_api


__version__ = '0.1.0'


BINTRAY_API_URL = 'https://bintray.com/api/v1'


def post_upload_recipe(output, conanfile_path, reference, remote, **kwargs):
    try:
        output.info("[BINTRAY UPDATE]")
        package_url = _get_bintray_package_url(remote=remote, reference=reference)
        output.info("Reading package info form Bintray...")
        remote_info = _get_package_info_from_bintray(package_url=package_url)
        output.info("Inspecting recipe info ...")
        recipe_info = _get_package_info_from_recipe(conanfile_path=conanfile_path)
        updated_info = _update_package_info(recipe_info=recipe_info, remote_info=remote_info)
        if updated_info:
            output.info("Bintray is outdated. Updating Bintray package info ...")
            _patch_bintray_package_info(package_url=package_url, package_info=updated_info)
        else:
            output.info("Bintray package info is up-to-date.")
    except Exception as error:
        output.error(str(error))


def _extract_user_repo(remote):
    """
    Extract username and repository name from remote URL
    :param remote: Conan remote object
    :return: username, repository name
    """
    pattern = r'https?:\/\/api.bintray.com\/conan\/(.*)\/(.*)'
    match = re.match(pattern=pattern, string=remote.url)
    if not match:
        raise Exception("Could not extract subject and repo from %s" % remote.url)
    return match.group(1), match.group(2)


def _get_bintray_package_url(remote, reference):
    """
    Retrieve Bintray package repository URL
    :param remote: Conan remote object
    :param reference: Conan reference object
    :return: Bintray URL
    """
    user, repo = _extract_user_repo(remote)
    package = "{}%3A{}".format(reference.name, reference.user)
    return "{}/packages/{}/{}/{}".format(BINTRAY_API_URL, user, repo, package)


def _get_package_info_from_bintray(package_url):
    """
    Read package info from Bintray repository
    :param package_url: Bintray package URL
    :return: Package data from Bintray
    """
    response = requests.get(url=package_url)
    if not response.ok:
        raise Exception("Could not request package info: {}".format(response.text))
    return response.json()


def _get_package_info_from_recipe(conanfile_path):
    """
    Inspect Conan recipe using Conan API
    :param conanfile_path: Conan recipe path
    :return: All attributes from the recipe
    """
    conan_instance, _, _ = conan_api.Conan.factory()
    return conan_instance.inspect(path=conanfile_path, attributes=None)


def _update_package_info(recipe_info, remote_info):
    """
    Merge recipe data info remote data
    :param recipe_info: Data collected from Conan recipe
    :param remote_info: Data collected from Bintray repository
    :return: is it outdated, updated bintray info
    """
    updated_info = {}
    description = recipe_info['description']
    if description:
        if remote_info['desc'] != description:
            updated_info['desc'] = description

    # TODO (uilian): Add when available on Conan 1.9.0
    # tags = recipe_info['tags']
    # if tags:
    #     if remote_info['labels'] != tags:
    #         updated_info['labels'] = tags

    licenses = recipe_info['license']
    if licenses:
        if isinstance(licenses, str):
            licenses = [licenses]
        if not bool(set(licenses).intersection(remote_info['licenses'])):
            updated_info['licenses'] = licenses

    url = recipe_info['url']
    if url:
        if remote_info['vcs_url'] != url:
            updated_info['vcs_url'] = url

    issue_tracker_url = "{}/community/issues".format(url[:url.rfind('/')]) if url else ""
    issue_tracker_url = os.getenv("BINTRAY_ISSUE_TRACKER_URL", issue_tracker_url)

    if issue_tracker_url:
        if remote_info['issue_tracker_url'] != issue_tracker_url:
            updated_info['issue_tracker_url'] = issue_tracker_url

    if 'maturity' not in remote_info or remote_info['maturity'] != "Stable":
        updated_info['maturity'] = "Stable"

    # TODO (uilian): Add when available on Conan 1.9.0
    # homepage = recipe_info['homepage']
    # if homepage:
    #     if remote_info['website_url'] != homepage:
    #         updated_info['website_url'] = homepage

    return updated_info


def _patch_bintray_package_info(package_url, package_info):
    username, password = _get_credentials()
    response = requests.patch(
        url=package_url, json=package_info, auth=HTTPBasicAuth(username, password))
    if not response.ok:
        raise Exception("Could not request package info: {}".format(response.text))
    return response.json()


def _get_credentials():
    """
    Get Bintray user name and password from environment variables
    :return: username, password
    """
    username = os.getenv("CONAN_LOGIN_USERNAME", os.getenv("CONAN_USERNAME"))
    if not username:
        raise Exception("Could not update Bintray info: username not found")
    password = os.getenv("CONAN_PASSWORD")
    if not password:
        raise Exception("Could not update Bintray info: password not found")
    return username, password
