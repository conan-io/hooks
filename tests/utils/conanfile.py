from conans import ConanFile
from tests.utils.output import MockOutput


class MockSettings(object):

    def __init__(self, values):
        self.values = values

    def get_safe(self, value):
        return self.values.get(value, None)


MockOptions = MockSettings


class MockDepsCppInfo(object):

    def __init__(self):
        self.include_paths = []
        self.lib_paths = []
        self.libs = []
        self.defines = []
        self.cflags = []
        self.cppflags = []
        self.sharedlinkflags = []
        self.exelinkflags = []
        self.sysroot = ""


class MockConanfile(ConanFile):

    def __init__(self, settings, options=None, runner=None):
        self.deps_cpp_info = MockDepsCppInfo()
        self.settings = settings
        self.runner = runner
        self.options = options or MockOptions({})
        self.generators = []
        self.output = MockOutput()

        self.should_configure = True
        self.should_build = True
        self.should_install = True
        self.should_test = True

        self.package_folder = None

    def run(self, *args, **kwargs):
        if self.runner:
            kwargs["output"] = None
            self.runner(*args, **kwargs)
