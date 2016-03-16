import os

from django.conf import settings
from django.template.loaders import filesystem as fs, app_directories as ad
from django.template.loader_tags import IncludeNode, ExtendsNode as ExtendsNodeParent
from django.template.base import TemplateSyntaxError, TemplateEncodingError, StringOrigin, Lexer, Parser, Template as TemplateParent
from django.utils.encoding import smart_unicode

def compile_string(template_string, origin, name):
    "Compiles template_string into NodeList ready for rendering"
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
        # for django.VERSION > 1.4
        # always use default engine for render
        try:
            from django.template.engine import Engine
            self.engine = Engine.get_default()
        except:
            pass

class filesystem(fs.Loader):
    is_usable = True

    def load_template(self, template_name, template_dirs=None):
        source, origin = self.load_template_source(template_name, template_dirs)
        template = Template(source, name=template_name)
        return template, origin

class app_directories(ad.Loader):
    is_usable = True

    def load_template(self, template_name, template_dirs=None):
        source, origin = self.load_template_source(template_name, template_dirs)
        template = Template(source, name=template_name)
        return template, origin

from django import template
register = template.Library()

# !!! ATTENTION !!!
# it disable rule, that 'extends' must be first tag in template
# this need for first {% load %} tag
class ExtendsNode(ExtendsNodeParent):
    must_be_first = False

def construct_relative_path (name, relative_name):
    if not relative_name.startswith('"'):
        # argument is variable
        return relative_name

    levels = -1
    for ch in relative_name[1:]:
        if ch == '.':
            levels += 1
        else:
            break

    if (not name) or (levels < 0):
        # relative_name not starts with '.'
        return relative_name

    folders = os.path.dirname(name).split('/')
    if levels > len(folders):
        raise TemplateSyntaxError("Relative name '%s' have more parent folders, then given name '%s'" % (relative_name, name))

    result = folders[:len(folders) - levels]
    result.append(relative_name[levels+2:-1])
    return '"%s"' % '/'.join(result)

@register.tag('extends')
def do_extends(parser, token):
    bits = token.split_contents()
    if len(bits) != 2:
        raise TemplateSyntaxError("'%s' takes one argument" % bits[0])

    parent_name = parser.compile_filter(construct_relative_path(parser.template_name, bits[1]))
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
    return IncludeNode(parser.compile_filter(construct_relative_path(parser.template_name, bits[1])), extra_context=namemap,
                       isolated_context=isolated_context)
