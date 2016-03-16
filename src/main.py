"""
Test script for django relative_path module
(C) 2016 by Vitaly Bogomolov mail@vitaly-bogomolov.ru

>>> rend('subdir/sub2.html')
u'Base1. sub2 content'
>>> rend('subdir/sub3.html')
u'Base1. sub33 content'
>>> rend('subdir/subdir2/sub3.html')
u'Base1. sub3 content'
>>> rend('subdir/subdir2/sub4.html')
u'Base2. sub4 content'
"""
import os

import django
from django.conf import settings

ROOT_PROJECT = os.path.dirname(os.path.abspath(__file__))

settings.configure(

    DEBUG = True, 
    TEMPLATE_DEBUG = True,

    TEMPLATE_DIRS = (
        os.path.join(ROOT_PROJECT, 'tpl').replace('\\', '/'),
    ),

    TEMPLATE_LOADERS = (
        'template_relative_path.templatetags.relative_path.filesystem',
        'template_relative_path.templatetags.relative_path.app_directories',
    ),

    INSTALLED_APPS = ( 
        'template_relative_path',
    ),

    # for django version > 1.4
#    TEMPLATES = [{
#        'BACKEND': 'django.template.backends.django.DjangoTemplates',
#        'DIRS': [os.path.join(ROOT_PROJECT, 'tpl').replace('\\', '/')],
#        'OPTIONS': {
#            'loaders': [
#                'template_relative_path.templatetags.relative_path.filesystem',
#                'template_relative_path.templatetags.relative_path.app_directories',
#            ],
#        },
#    }]
)

#print "django version", django.VERSION
django.setup()

from django import template
from django.template.loader import get_template

c = template.Context({})

def rend(template):
    return get_template(template).render(c)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
