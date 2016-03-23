"""
Library for enable relative pathes in django template tags 'extends' and 'include' 
(C) 2016 by Vitaly Bogomolov mail@vitaly-bogomolov.ru
Origin: https://github.com/vb64/django.templates.relative.path

The problem: http://stackoverflow.com/questions/671369/django-specifying-a-base-template-by-directory
{% extends "./../base.html" %} won't work with extends.
It causes a lot of inconvenience, if you have an extensive hierarchy of django templates.

This library allows relative paths in argument of 'extends' and 'include' template tags. Relative path must start from "./"

Just write in your templates as follows:

{% load relative_path %}
{% extends "./base.html" %}

this will extend template "base.html", located in the same folder, where your template placed

{% load relative_path %}
{% extends "./../../base.html" %}

extend template "base.html", located at two levels higher

same things works with 'include' tag.

{% load relative_path %}
{% include "./base.html" %}

include base.html, located near of your template.

Warning: 
The rule 'extends tag must be first tag into template' is disabled by this library. 
Write your template with caution.

Compatibility:
Code was tested with Django versions from 1.4 to 1.9
"""

"""
Installation.

Installation is differs for Django version 1.9 and previous versions, because 1.9 brings many changes into template's mechanizm.

Django 1.9
----------

Plug reference to library code in 'TEMPLATES' key of settings.py or django.settings.configure()

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [os.path.join(ROOT_PROJECT, 'tpl').replace('\\', '/')],
    'OPTIONS': {

        'loaders': [
            'dotted_path_to_relative_path_file.FileSystem_1_9',
            'dotted_path_to_relative_path_file.AppDirectories_1_9',
        ],

        'libraries': {
            'relative_path': 'dotted_path_to_relative_path_file',
        },
    },
}]


Django 1.4/1.8
--------------

Put 'relative_path.py' file to the 'templatetags' folders of your app. (app must be included into INSTALLED_APPS tuple)

In settings.py or django.settings.configure(), replace standard django template loaders by loaders from this library

TEMPLATE_LOADERS = (
#    'django.template.loaders.filesystem.Loader',
#    'django.template.loaders.app_directories.Loader',
    'dotted_path_to_relative_path_file.FileSystem',
    'dotted_path_to_relative_path_file.AppDirectories',
)
"""

# The MIT License (MIT)
# 
# Copyright (c) 2016 Vitaly Bogomolov

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os

from django.conf import settings
from django.template.loaders import filesystem as fs, app_directories as ad
from django.template.loader_tags import IncludeNode, ExtendsNode as ExtendsNodeParent
from django.template.base import TemplateSyntaxError, TemplateEncodingError, StringOrigin, Lexer, Parser, Template as TemplateParent
from django.utils.encoding import smart_unicode

# django 1.9
try:
    from django.template import Origin, Template as Template_1_9_parent, TemplateDoesNotExist
    from django.utils.inspect import func_supports_parameter
    from django.template.base import DebugLexer as DebugLexer_1_9
    from django.template.utils import get_app_template_dirs
except:
    pass

################################################
# template loaders
################################################


def compile_string(template_string, origin, name):
    if settings.TEMPLATE_DEBUG:
        from django.template.debug import DebugLexer, DebugParser
        lexer_class, parser_class = DebugLexer, DebugParser
    else:
        lexer_class, parser_class = Lexer, Parser
    lexer = lexer_class(template_string, origin)
    parser = parser_class(lexer.tokenize())
    parser.template_name = name
    return parser.parse()


class Template(TemplateParent):

    def __init__(self, template_string, origin=None, name=None, engine=None):
        try:
            template_string = smart_unicode(template_string)
        except UnicodeDecodeError:
            raise TemplateEncodingError("Templates can only be constructed "
                                        "from unicode or UTF-8 strings.")
        if settings.TEMPLATE_DEBUG and origin is None:
            origin = StringOrigin(template_string)
        self.nodelist = compile_string(template_string, origin, name)
        self.name = name
        self.origin = origin

        # !!! ATTENTION !!!
        # always use default engine for render
        try:
            from django.template.engine import Engine
            self.engine = Engine.get_default()
        except:
            self.engine = None

class FileSystem(fs.Loader):
    is_usable = True

    def load_template(self, template_name, template_dirs=None):
        source, origin = self.load_template_source(template_name, template_dirs)
        template = Template(source, name=template_name)
        return template, origin


class AppDirectories(ad.Loader):
    is_usable = True

    def load_template(self, template_name, template_dirs=None):
        source, origin = self.load_template_source(template_name, template_dirs)
        template = Template(source, name=template_name)
        return template, origin


class Template_1_9(Template_1_9_parent):

    def compile_nodelist(self):

        if self.engine.debug:
            lexer = DebugLexer_1_9(self.source)
        else:
            lexer = Lexer(self.source)

        tokens = lexer.tokenize()
        parser = Parser(
            tokens, self.engine.template_libraries, self.engine.template_builtins,
        )

        parser.template_name = self.origin.template_name

        try:
            return parser.parse()
        except Exception as e:
            if self.engine.debug:
                e.template_debug = self.get_exception_info(e, e.token)
            raise


class FileSystem_1_9(fs.Loader):

    def get_template(self, template_name, template_dirs=None, skip=None):
        tried = []

        args = [template_name]
        if func_supports_parameter(self.get_template_sources, 'template_dirs'):
            args.append(template_dirs)

        for origin in self.get_template_sources(*args):
            if skip is not None and origin in skip:
                tried.append((origin, 'Skipped'))
                continue

            try:
                contents = self.get_contents(origin)
            except TemplateDoesNotExist:
                tried.append((origin, 'Source does not exist'))
                continue
            else:
                return Template_1_9(
                    contents, origin, origin.template_name, self.engine,
                )

        raise TemplateDoesNotExist(template_name, tried=tried)


class AppDirectories_1_9(FileSystem_1_9):

    def get_dirs(self):
        return get_app_template_dirs('templates')

################################################
# template tags 'extends' and 'include'
################################################

from django import template
register = template.Library()


# !!! ATTENTION !!!
# it disable rule, that 'extends' must be first tag in template
# this need for first {% load relative_path %} tag
class ExtendsNode(ExtendsNodeParent):
    must_be_first = False


def construct_relative_path(name, relative_name):
    """
    Construct absolute template name based on two chains of folders:
    into 'relative_name' and 'name'
    """
    if not relative_name.startswith('"./'):
        # argument is variable or literal, that not contain relative path
        return relative_name

    chain = relative_name.split('/')
    result_template_name = chain[-1].rstrip('"')
    folders_relative = chain[1:-1]
    folders_template = name.split('/')[:-1]

    for folder in folders_relative:

        if folder == "..":
            if folders_template:
                folders_template = folders_template[:-1]
            else:
                raise TemplateSyntaxError(
                    "Relative name '%s' have more parent folders, then given template name '%s'"
                    % (relative_name, name)
                )

        elif folder == ".":
            pass

        else:
            folders_template.append(folder)

    folders_template.append(result_template_name)
    result_template_name = '/'.join(folders_template)

    if name == result_template_name:
        raise TemplateSyntaxError(
            "Circular dependencies: relative path '%s' was translated to template name '%s'"
            % (relative_name, name)
        )

    return '"%s"' % result_template_name


@register.tag('extends')
def do_extends(parser, token):
    bits = token.split_contents()
    if len(bits) != 2:
        raise TemplateSyntaxError("'%s' takes one argument" % bits[0])

    bits[1] = construct_relative_path(parser.template_name, bits[1])
    parent_name = parser.compile_filter(bits[1])
    nodelist = parser.parse()
    if nodelist.get_nodes_by_type(ExtendsNode):
        raise TemplateSyntaxError("'%s' cannot appear more than once in the same template" % bits[0])
    return ExtendsNode(nodelist, parent_name)


@register.tag('include')
def do_include(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("%r tag takes at least one argument: the name of the template to be included." % bits[0])
    options = {}
    remaining_bits = bits[2:]
    while remaining_bits:
        option = remaining_bits.pop(0)
        if option in options:
            raise TemplateSyntaxError('The %r option was specified more '
                                      'than once.' % option)
        if option == 'with':
            value = token_kwargs(remaining_bits, parser, support_legacy=False)
            if not value:
                raise TemplateSyntaxError('"with" in %r tag needs at least '
                                          'one keyword argument.' % bits[0])
        elif option == 'only':
            value = True
        else:
            raise TemplateSyntaxError('Unknown argument for %r tag: %r.' %
                                      (bits[0], option))
        options[option] = value
    isolated_context = options.get('only', False)
    namemap = options.get('with', {})
    bits[1] = construct_relative_path(parser.template_name, bits[1])

    return IncludeNode(parser.compile_filter(bits[1]), extra_context=namemap,
                       isolated_context=isolated_context)
