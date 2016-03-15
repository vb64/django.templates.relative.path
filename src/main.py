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

)

django.setup()
#print django.VERSION

from django import template
from django.template.loader import get_template

tpl_file = 'subdir/sub2.html'
t = get_template(tpl_file)
c = template.Context({})

print t.render(c)
