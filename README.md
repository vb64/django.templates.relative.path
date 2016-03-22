Relative paths for Django template tags 'extends' and 'include'.
================================================================

[The problem](http://stackoverflow.com/questions/671369/django-specifying-a-base-template-by-directory): {% extends "./../base.html" %} won't work with extends.

It causes a lot of inconvenience, if you have an extensive hierarchy of django templates.
This library allows relative paths in argument of 'extends' and 'include' template tags. Relative path must start from "./"

Just write in your templates as follows:

```
{% load relative_path %}
{% extends "./base.html" %}
```

this will extend template "base.html", located in the same folder, where your template placed

```
{% load relative_path %}
{% extends "./../../base.html" %}
```

extend template "base.html", located at two levels higher

same things works with 'include' tag.

```
{% load relative_path %}
{% include "./base.html" %}
```

include base.html, located near of your template.

**Warning!**
The rule 'extends tag must be first tag into template' is disabled by this library. 
Write your template with caution.

**Compatibility**
Code was tested with Django versions from 1.4 to 1.9

Installation.
-------------

Installation is differs for Django version 1.9 and previous versions, because 1.9 brings many changes into template's mechanizm.

**Django 1.9**

Plug reference to library code in 'TEMPLATES' key of settings.py or django.settings.configure()

```
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [os.path.join(ROOT_PROJECT, 'tpl').replace('\\', '/')],
    'OPTIONS': {

        'loaders': [
            'dotted_path_to_relative_path_file.filesystem_1_9',
            'dotted_path_to_relative_path_file.app_directories_1_9',
        ],

        'libraries': {
            'relative_path': 'dotted_path_to_relative_path_file',
        },
    },
}]
```


**Django 1.4/1.8**

Put 'relative_path.py' file to the 'templatetags' folders of your app. (app must be included into INSTALLED_APPS tuple)

In settings.py or django.settings.configure(), replace standard django template loaders by loaders from this library

```
TEMPLATE_LOADERS = (
#    'django.template.loaders.filesystem.Loader',
#    'django.template.loaders.app_directories.Loader',
    'dotted_path_to_relative_path_file.filesystem',
    'dotted_path_to_relative_path_file.app_directories',
)
```
