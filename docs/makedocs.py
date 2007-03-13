#!/usr/bin/env python

import os
from os import path
from docutils.parsers.rst import directives
from docutils.core import publish_file, publish_string, publish_doctree
from docutils.parsers import rst
from docutils.nodes import SparseNodeVisitor
from docutils.readers.standalone import Reader
from docutils.writers.html4css1 import HTMLTranslator, Writer
from docutils import nodes

## kill me?

# class IndexWriter(Writer):
#     def __init__(self):
#         super(IndexWriter, self).__init__()
#         self.translator_class = IndexTranslator
#         
# class IndexTranslator(HTMLTranslator):    
#     def visit_bullet_list(self, node):
#         self.list_depth += 1
#         self.list_item_prefix = (' ' * self.list_depth) + '* '
# 
#     def depart_bullet_list(self, node):
#         self.list_depth -= 1
#         if self.list_depth == 0:
#             self.list_item_prefix = None
#         else:
#             (' ' * self.list_depth) + '* '
#         self.output.append('\n\n')
#                            
#     def visit_list_item(self, node):
#         self.old_indent = self.indent
#         self.indent = self.list_item_prefix
# 
#     def depart_list_item(self, node):
#         self.indent = self.old_indent

def children_from_contents_of(  
        name, arguments, options, content, lineno,
        content_offset, block_text, state, state_machine):
        
    # bulletlist = nodes.bullet_list()
    # self.parent += bulletlist
    # bulletlist['bullet'] = match.string[0]
    # i, blank_finish = self.list_item(match.end())
    # bulletlist += i
    # offset = self.state_machine.line_offset + 1   # next line
    # new_line_offset, blank_finish = self.nested_list_parse(
    #       self.state_machine.input_lines[offset:],
    #       input_offset=self.state_machine.abs_line_offset() + 1,
    #       node=bulletlist, initial_state='BulletList',
    #       blank_finish=blank_finish)
    # self.goto_line(new_line_offset)
    # if not blank_finish:
    #     self.parent += self.unindent_warning('Bullet list')
    # return [], next_state, []
    
    # state_machine.run(block, input_offset, memo=self.memo,
    #                       node=bulletlist, match_titles=match_titles)
    
    pos = arguments[0].find(u' ')
    modpath = arguments[0][:pos]
    title = arguments[0][pos+1:]
    
    print (modpath, title)
    
    #, nodes.bullet_list()
    return [nodes.paragraph(title)]

children_from_contents_of.arguments = (1, 0, 1)
children_from_contents_of.options = {}
children_from_contents_of.content = 0

directives.register_directive(
    'children_from_contents_of', children_from_contents_of)

def main():
    heredir = path.dirname(__file__)
    srcdir = heredir
    builddir = path.join(heredir, '..', 'build')
    docsdir = path.join(builddir, 'docs')
    
    if not path.exists(builddir):
        os.mkdir(builddir)
    if not path.exists(docsdir):
        os.mkdir(docsdir)
    
    basename = 'index'
    # tree = publish_doctree(
    #             open(path.join(srcdir, basename + '.rst'), 'r').read())
    # # print dir(tree)
    # print tree
    
    body = publish_file(open(path.join(srcdir, basename + '.rst'), 'r'),
                destination=open(path.join(docsdir, basename + '.html'), 'w'),
                writer_name='html',
                settings_overrides={'halt_level':2,
                                    'report_level':5})
    

if __name__ == '__main__':
    main()