from conans import tools
try:
    from conans import Settings
    v2 = False
except ImportError:
    from conans.model.settings import Settings
    v2 = True


def save(filename, content):
    if hasattr(tools, "save"):
        tools.save(filename, content)
    else:
        with open(filename, "w") as f:
            f.write(content)
