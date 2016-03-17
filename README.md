Relative pathes for Django template tags 'extends' and 'include'.
================================================================

[The problem](http://stackoverflow.com/questions/671369/django-specifying-a-base-template-by-directory): {% extends "../base.html" %} won't work with extends.

It causes a lot of inconvenience, if you have an extensive hierarchy of django templates.
This library is implementing standard python rules for relative import (from ...module import something)

Just write in your templates as follows:

```
{% load relative_path %}
{% extends ".base.html" %}
```

this will extend template "base.html", located in the same folder, where your template placed

```
{% load relative_path %}
{% extends "...base.html" %}
```

extend template "base.html", located at two levels higher

same things works with 'include' tag.

```
{% load relative_path %}
{% include ".base.html" %}
```

include base.html, located near of your template.

**Warning!**
The rule 'extends tag must be first tag into template' is disabled by this library. 
Write your template with caution.

**Compatibility**
Code was tested with Django versions from 1.4 to 1.9
