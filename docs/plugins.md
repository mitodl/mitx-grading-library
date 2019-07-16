# Plugins

Plugins are an advanced feature of the library that allows users to construct their own custom-built graders, built on top of the infrastructure of the library. They can also be used to allow for straightforward code re-use, and to override library defaults on a course-wide basis.

Any `.py` file stored in the `mitxgraders/plugins` folder will be automatically loaded. All variables in the `__all__` list will be made available when doing `from mitxgraders import *`. See `template.py` for an example.

You can define custom grading classes in your plugin. To learn how this works, we recommend copying the code from `stringgrader.py`, renaming the class, and building a simple plugin based on `StringGrader`.

We are happy to include user-contributed plugins in the repository for this library. If you have built a plugin that you would like to see combined into this library, please contact the authors through [github](https://github.com/mitodl/mitx-grading-library). We are also willing to consider incorporating good plugins into the library itself.


## Overriding Library Defaults

Library defaults for any grading class can be specified by constructing the desired dictionary of defaults, and calling `register_defaults(dict)` on the class. For example, to specify that all `StringGrader`s should be case-insensitive by default, you can do the following.

```pycon
StringGrader.register_defaults({
    'case_sensitive': False
})
```

When this code is included in a file in the plugins folder, it automatically runs every time the library is loaded, leading to course-wide defaults. If for some reason you need to reset to the library defaults for a specific problem, you can call `clear_registered_defaults()` on the class in that problem.

An example plugin has been provided for you in `defaults_sample.py`. The code in this plugin is commented out so that it doesn't change anything by default. If you are interested in overriding library defaults on a course-wide basis, we recommend copying this file to `defaults.py` and setting the desired defaults using the code templates provided. This is particularly useful if you wish to use attempt-based partial credit throughout your course.


## Inserting Plugins into the Library

To use a plugin, you will need to download the `python_lib.zip` file, unzip it, put the plugin in the plugins directory, and rezip everything. Your new zip file should unzip to have the `mitxgraders` and `voluptuous` directories.
