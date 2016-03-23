"""
Library for enable relative pathes in django template tags
'extends' and 'include'

(C) 2016 by Vitaly Bogomolov mail@vitaly-bogomolov.ru
Origin: https://github.com/vb64/django.templates.relative.path
"""

from django import template
from django.conf import settings
from django.template.base import Template as TemplateParent
from django.template.base import (Lexer, Parser, StringOrigin,
                                  TemplateEncodingError, TemplateSyntaxError,
                                  token_kwargs)
from django.template.loader_tags import ExtendsNode as ExtendsNodeParent
from django.template.loader_tags import IncludeNode
from django.template.loaders import app_directories as ad
from django.template.loaders import filesystem as fs
from django.utils.encoding import smart_unicode

# django 1.9
try:
    from django.template import (
        TemplateDoesNotExist,
        Template as Template19parent,
    )
    from django.utils.inspect import func_supports_parameter
    from django.template.base import DebugLexer as DebugLexer19
    from django.template.utils import get_app_template_dirs
except:
    pass

################################################
# template loaders
################################################


def compile_string(template_string, origin, name):
    """
    Set template name to Parser instance
    """
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
    """
    Pass template name to Parser
    """

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
        except Exception:
            self.engine = None


class FileSystem(fs.Loader):
    """
    Use modified Template class
    """
    is_usable = True

    def load_template(self, template_name, template_dirs=None):
        """
        Use modified Template class and pass template name
        """
        source, origin = self.load_template_source(
            template_name,
            template_dirs
        )

        template = Template(
            source,
            name=template_name
        )

        return template, origin


class AppDirectories(ad.Loader):
    """
    Use modified Template class
    """
    is_usable = True

    def load_template(self, template_name, template_dirs=None):
        """
        Use modified Template class and pass template name
        """
        source, origin = self.load_template_source(
            template_name, template_dirs
        )
        template = Template(source, name=template_name)
        return template, origin


class Template19(Template19parent):
    """
    Pass template name to Parser into Django 1.9
    """

    def compile_nodelist(self):
        """
        Pass template name to parser instance
        """

        if self.engine.debug:
            lexer = DebugLexer19(self.source)
        else:
            lexer = Lexer(self.source)

        tokens = lexer.tokenize()
        parser = Parser(
            tokens,
            self.engine.template_libraries,
            self.engine.template_builtins,
        )

        parser.template_name = self.origin.template_name

        try:
            return parser.parse()
        except Exception as e:
            if self.engine.debug:
                e.template_debug = self.get_exception_info(e, e.token)
            raise


class FileSystem19(fs.Loader):
    """
    Use modified Template19 class
    """

    def get_template(self, template_name, template_dirs=None, skip=None):
        """
        Use modified Template19 class and
        pass template name to instance
        """
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
                return Template19(
                    contents, origin, origin.template_name, self.engine,
                )

        raise TemplateDoesNotExist(template_name, tried=tried)


class AppDirectories19(FileSystem19):
    """
    Use modified Template19 class
    """

    def get_dirs(self):
        """
        Same as core function
        """
        return get_app_template_dirs('templates')

################################################
# template tags 'extends' and 'include'
################################################

register = template.Library()


class ExtendsNode(ExtendsNodeParent):
    """
    !!! ATTENTION !!!
    it disable rule, that 'extends' must be first tag in template
    this need for first {% load relative_path %} tag
    """
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
                    "Relative name '%s' have more parent folders, "
                    "then given template name '%s'"
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
            "Circular dependencies: relative path '%s'"
            " was translated to template name '%s'"
            % (relative_name, name)
        )

    return '"%s"' % result_template_name


@register.tag('extends')
def do_extends(parser, token):
    """
    Same as core function, with construct_relative_path call
    """
    bits = token.split_contents()
    if len(bits) != 2:
        raise TemplateSyntaxError("'%s' takes one argument" % bits[0])

    bits[1] = construct_relative_path(parser.template_name, bits[1])
    parent_name = parser.compile_filter(bits[1])
    nodelist = parser.parse()
    if nodelist.get_nodes_by_type(ExtendsNode):
        raise TemplateSyntaxError(
            "'%s' cannot appear more than once in the same template"
            % bits[0]
            )
    return ExtendsNode(nodelist, parent_name)


@register.tag('include')
def do_include(parser, token):
    """
    Same as core function, with construct_relative_path call
    """
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError(
            "%r tag takes at least one argument: "
            "the name of the template to be included."
            % bits[0]
        )
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
