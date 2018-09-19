# Conan Plugins

Repository to develop **experimental** [Conan](https://conan.io) plugins for Conan >= 1.8.

## Plugin setup

Place your plugin python files under *~/.conan/plugins*. The name of the plugin would be the same one as the file name.

```
*~/.conan/plugins/conan-center.py
```

## Plugin activation

You can activate any plugin with:

``$ conan config set plugins.conan-center``

If you handle multiple dependencies in your project is better to add a *conan.conf*:

```
    [plugin]
    attribute_checker
    conan-center
```

## License

[MIT License](LICENSE)