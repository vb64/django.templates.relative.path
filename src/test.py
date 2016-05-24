"""
Test script for django relative_path module
(C) 2016 by Vitaly Bogomolov mail@vitaly-bogomolov.ru

>>> rend('subdir/sub2.html')
u'Base1. sub2 content'
>>> rend('subdir/sub3.html')
u'Base1. sub33 content'
>>> rend('subdir/sub4.html')
Traceback (most recent call last):
...
TemplateSyntaxError: Relative name '"./../../base1.html"' have more parent folders, then given template name 'subdir/sub4.html'
>>> rend('subdir/subdir2/sub3.html')
u'Base1. sub3 content'
>>> rend('subdir/subdir2/sub4.html')
u'Base2. sub4 content'
>>> rend('subdir/subdir2/sub5.html')
u'Base2. include content'

>>> construct_relative_path ('dir1/dir2/index.html', '"./template.html"')
'"dir1/dir2/template.html"'

>>> construct_relative_path ('dir1/dir2/schedule.html', '"template.html"')
'"template.html"'

>>> construct_relative_path ('dir1/dir2/schedule.html', '"./../template.html"')
'"dir1/template.html"'
"""
import os

import django
from django.conf import settings
from django import template
from django.template.loader import get_template

ROOT_PROJECT = os.path.dirname(os.path.abspath(__file__))

ver_major, ver_minor = django.VERSION[:2]

if ver_major == 1:

    if ver_minor > 8:
        settings.configure(

          DEBUG=True,

          TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [os.path.join(ROOT_PROJECT, 'tpl').replace('\\', '/')],
            'OPTIONS': {

              'loaders': [
                'template_relative_path.templatetags.relative_path.FileSystem19',  # noqa
                'template_relative_path.templatetags.relative_path.AppDirectories19',  # noqa
              ],

              'libraries': {
                'relative_path': 'template_relative_path.templatetags.relative_path',  # noqa
              },
            },
          }],
        )

        c = {}

    else:

        settings.configure(

          DEBUG=True,
          TEMPLATE_DEBUG=True,

          TEMPLATE_DIRS=(
            os.path.join(ROOT_PROJECT, 'tpl').replace('\\', '/'),
          ),

          TEMPLATE_LOADERS=(
            'template_relative_path.templatetags.relative_path.FileSystem',
            'template_relative_path.templatetags.relative_path.AppDirectories',
          ),

          INSTALLED_APPS=(
            'template_relative_path',
          ),

        )

        c = template.Context({})

    if ver_minor > 6:
        django.setup()


def rend(template):
    return get_template(template).render(c)


from template_relative_path.templatetags.relative_path import construct_relative_path  # noqa

if __name__ == "__main__":
    import doctest
    doctest.testmod()
