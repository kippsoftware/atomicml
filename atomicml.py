"""AtomicML - parse indented lines into a tree of nodes

version: 3.0.0
author: Neill A. Kipp

Copyright (C) 2000, 2003, 2008, 2021, 2022 Kipp Software Corporation

Licensed under the Apache License, Version 2.0 (the "License"); you
may not use this file except in compliance with the License.  You may
obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.  See the License for the specific language governing
permissions and limitations under the License.

////////////////
AtomicML usage

Iterate over Atomic tokens (INDENT, DEDENT, SAMEDENT, BLANK)
  import atomicml
  for event in atomicml.events(open("data.at")):
    handleEvent(event)

Iterate to parse a single Atomic node
  import atomicml
  for node in atomicml.node(open("data.at")):
    handleNode(node)

Iterate to parse each XML node in the tree
  import atomicml
  root = atomicml.XmlParser(open("data.xml")).getRoot()

////////////////
AtomicStyle

Implement your dispatching subclass.

  import atomicml
  class MyStyle(atomicml.AtomicStyle):
    def __init__(self):
      AtomicStyle.__init__(self)
      self.prefix = "g_"
      self.setMap("*", "li")
      self.setMap(".", "text")
    def g_book(self, node, args):
      print node.getName(), node.getValue()
      self.style(children)
    def g_li(self, node, args):
      print node.getName(), node.getValue()
      self.style(children)
    def g_text(self, node, args):
      print node.getValue()
  MyStyle().style(Atomic.getNodes(file("data.at")))

"""
import re

INDENT = 1
DEDENT = 2
SAMEDENT = 3
BLANK = 4
LINE = re.compile(r"([ \t]*)(.*)")

class Node:
  """Encapsulate data and children of a tree node"""
  def __init__(self, data="", blanks=0, lineno=0):
    self.data = data
    self.children = []
    self.blanks = blanks
    self.lineno = lineno
  def __str__(self, indent = 0):
    out = []
    for line in range(self.blanks):
      out.append('')
    out.append('  ' * indent + self.data)
    for child in self.children:
      out.append(child.__str__(indent + 1))
    return '\n'.join(out)

def tokenize_line(source):
  """Iterate over source lines and yield a token for each"""
  stack = [-1]
  lineno = 0
  for line in source:
    lineno += 1
    indent, data = LINE.match(line).groups()
    indent = len(indent.expandtabs())
    if not data:
      yield (BLANK,)
      continue
    while indent < stack[-1]:
      if indent > stack[-2]:
        stack[-1] = indent
      else:
        stack.pop()
        yield (DEDENT,)
    if indent == stack[-1]:
      yield (SAMEDENT, data, lineno)
    else:
      stack.append(indent)
      yield (INDENT, data, lineno)

def parse_node(source):
  """Iterate over source lines and yield non-indented nodes"""
  stack = [Node()]
  blanks = 0
  lineno = 1
  for token in tokenize_line(source):
    if token[0] == INDENT:
      node = Node(token[1], blanks, token[2])
      blanks = 0
      stack[-1].children.append(node)
      stack.append(node)
    elif token[0] == DEDENT:
      stack.pop()
    elif token[0] == SAMEDENT:
      if len(stack) == 2:
        yield stack[0].children[-1]
      node = Node(token[1], blanks, token[2])
      blanks = 0
      stack[-2].children.append(node)
      stack[-1] = node
    else:
      blanks += 1
  yield stack[0].children[-1] if stack[0].children else stack[0]

def parse_nodes(source, nodes=[]):
  """Parse the entire AtomicML file into nodes"""
  for node in parse_node(source):
    nodes.append(node)
  return nodes

# ////////////////////////////////////////////////////////////////
# AtomicStyle

class AtomicStyle:
  """Recur through the node tree, match node names, and dispatch to handlers"""
  def __init__(self):
    self.dispatch = {}
    self.prefix = "f_"
  def style(self, children, args=None, out=None):
    if type(children) != type([]):
      children = [children]
    for node in children:
      name = node.data.split(None, 1)[0] if node.data else ""
      func = f"{self.prefix}{self.dispatch.get(name, name)}"
      if func in dir(self):
        eval(f"self.{func}(node, args, out)")
      else:
        self.style(node.children, args, out)

# ////////////////////////////////////////////////////////////////
# XML Parser

import xml.sax, xml.sax.handler

class XmlParser(xml.sax.ContentHandler, xml.sax.handler.DTDHandler):
  """Parse XML into Atomic Nodes"""
  def parse(self, buffer):
    root = Node("!xml")
    self.nodeStack = [root]
    parser = xml.sax.make_parser()
    parser.setContentHandler(self)
    parser.setDTDHandler(self)
    parser.setErrorHandler(xml.sax.handler.ErrorHandler())
    parser.parse(buffer)
    return root
  def filter(self, data):
    return data.replace('\n', r'\n').replace('\\', r'\\')
  def startElement(self, name, atts):
    node = Node(name)
    for att in sorted(atts):
      node.children.append(Node(f"@{att} {self.filter(atts[att])}"))
    self.nodeStack[-1].children.append(node)
    self.nodeStack.append(node)
  def endElement(self, name):
    self.nodeStack.pop()
  def characters(self, data):
    data = data.strip()
    if data:
      node = Node(f". {self.filter(data)}")
      self.nodeStack[-1].children.append(node)
  def notationDecl(self, name, publicId, systemId):
    node = Node(f"!notation {name}")
    if publicId:
      node.children.append(Node(f"@public {self.filter(publicId)}"))
    if systemId:
      node.children.append(Node(f"@system {self.filter(systemId)}"))
    self.nodeStack[-1].children.append(node)
  def unparsedEntityDecl(self, name, publicId, systemId, ndata):
    node = Node(f"!entity {name}")
    if publicId:
      node.children.append(Node(f"@public {self.filter(publicId)}"))
    if systemId:
      node.children.append(Node(f"@system {self.filter(systemId)}"))
    if ndata :
      node.children.append(Node(f"@ndata {ndata}"))
    self.nodeStack[-1].children.append(node)
