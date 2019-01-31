# coding=utf-8

from conans import tools
from conans.errors import ConanException


def svn(min_req_version=None):
    try:
        v = tools.SVN.get_version()
    except ConanException:
        return False
    else:
        if min_req_version:
            return v >= min_req_version
        return True
