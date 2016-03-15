from django.conf import settings
from django.template.loaders import filesystem as fs, app_directories as ad
from django.template.loader_tags import ExtendsNode
from django.template.base import Template, TemplateSyntaxError

class filesystem(fs.Loader):
    is_usable = True

    def load_template(self, template_name, template_dirs=None):
        source, origin = self.load_template_source(template_name, template_dirs)
        logging.info("filesystem source: '%s' origin: '%s'" % (source, origin))

        template = Template(source)
        return template, origin

class app_directories(ad.Loader):
    is_usable = True

    def load_template(self, template_name, template_dirs=None):
        source, origin = self.load_template_source(template_name, template_dirs)
        logging.info("app_directories source: '%s' origin: '%s'" % (source, origin))

        template = Template(source)
        return template, origin

from django import template
register = template.Library()

@register.tag('extends')
def do_extends(parser, token):
    bits = token.split_contents()
    if len(bits) != 2:
        raise TemplateSyntaxError("'%s' takes one argument" % bits[0])
    parent_name = parser.compile_filter(bits[1])
    nodelist = parser.parse()
    if nodelist.get_nodes_by_type(ExtendsNode):
        raise TemplateSyntaxError("'%s' cannot appear more than once in the same template" % bits[0])
    return ExtendsNode(nodelist, parent_name)
