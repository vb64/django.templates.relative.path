# Relative pathes for Django template tags 'extends' and 'include'

[The problem](http://stackoverflow.com/questions/671369/django-specifying-a-base-template-by-directory): {% extends "../base.html" %} won't work with extends.

It causes a lot of inconvenience, if you have an extensive hierarchy of django templates.
This library is implementing standard python rules for relative import (from ...module import something)

Just write in your templates as follows:

```
{% load relative_path %}
{% extends ".base.html" %}
```
