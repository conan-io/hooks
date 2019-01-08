[![Build Status](https://travis-ci.org/conan-io/hooks.svg?branch=master)](https://travis-ci.org/conan-io/hooks)
[![Build status](https://ci.appveyor.com/api/projects/status/s0k4n197ko1iyoml/branch/master?svg=true)](https://ci.appveyor.com/project/ConanCIintegration/hooks/branch/master)


# Conan Hooks

Repository to develop **experimental** [Conan](https://conan.io) hooks for Conan >= 1.8.

**WARNING**: Hooks were originally named "Plugins"

## Hook setup

Place your hook Python files under *~/.conan/hooks*. The name of the hook would be the same one as the file name.

```
*~/.conan/hook/conan-center.py
```

Only copying plugin files will not activate them.

## Conan config as installer

To install all plugins from Conan plugins:

``$ conan config install https://github.com/conan-io/plugins``

Conan config install does not activate any hook.

## Hook activation

You can activate any hook with:

``$ conan config set hooks.conan-center``

If you handle multiple dependencies in your project is better to add a *conan.conf*:

```
    [hooks]
    attribute_checker
    conan-center
```

## Supported hooks

- [Conan Center](hooks/conan-center.py): Conan recipe linter
- [Bintray Update](plugins/bintray-update.py): Update Bintray package info

## License

[MIT License](LICENSE)
