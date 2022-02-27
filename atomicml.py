"""
  Atomic - Atomic parser; AtomicStyle base class; XmlParser interface (SAX)

  version: 2.0.0
  author: Neill A. Kipp

  Copyright (C) 2000, 2003, 2008, 2021 Kipp Software Corporation

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

  ////////////////

  Atomic usage - events:
    import atomicml
    for event in atomicml.getEvent(file("data.at")) :
      handleEvent(event)

  Atomic usage - single node:
    import atomicml
    for node in atomicml.getNode(file("data.at")) :
      doNode(node)

  Atomic usage - slurp nodes:
    import atomicml
    for node in atomicml.getNodes(file("data.at")) :
      handleNode(node)

  XmlParser usage:
    import atomicml
    doNode(atomicml.XmlParser(file("data.xml")).getRoot())

  AtomicStyle - base class for implementing an "f_" style class usage:
    import atomicml
    class MyStyle(atomicml.AtomicStyle) :
      def __init__(self) :
        AtomicStyle.__init__(self)
        self.setPrefix("g_")
        self.setMap("*", "li")
        self.setMap(".", "text")
      def g_book(self, node, args) :
        print node.getName(), node.getValue()
        self.style(children)
      def g_li(self, node, args) :
        print node.getName(), node.getValue()
        self.style(children)
      def g_text(self, node, args) :
        print node.getValue()
    MyStyle().style(Atomic.getNodes(file("data.at")))

"""
import StringIO

# ////////////////////////////////////////////////////////////////
# Helper functions

def split(data, count) :
  """ Splits data into list of exactly count+1 items, some possibly empty strings """
  out = data.split(None, count)
  while len(out) < count + 1:
    out.append("")
  return out

def getName(data) :
  """ Returns the first token of the string """
  return split(data, 1)[ 0]

def getValue(data) :
  """ Returns the remainder of the string after removing the first token """
  return split(data, 1)[ 1]

# ////////////////////////////////////////////////////////////////
# Atomic Parser

import re

INDENT = 1
DEDENT = 2
SAMEDENT = 3
BLANK = 4

class Node :
  """ Atomic nodes have an extremely simple structure (cf, DOM) """
  def __init__(self, data = "", blanks = 0, lineno = 0) :
    self.data = data
    self.children = []
    self.blanks = blanks
    self.lineno = lineno
  def split(self, count) :
    return split(self.data, count)
  def getName(self) :
    return getName(self.data)
  def getValue(self) :
    return getValue(self.data)
  def str(self, indent = 0) :
    out = []
    for line in range(self.blanks) :
      out.append("")
    out.append('  ' * indent + self.data)
    for child in self.children :
      out.append(child.str(indent + 1))
    return '\n'.join(out)
  def __str__(self) :
    return self.str()

def getEvent(source) :
  if type(source) == type("") or type(source) == type(u""):
    source = StringIO.StringIO(source)
  LINE = re.compile(r"([ \t]*)(.*)")
  stack = [ -1]
  lineno = 0
  for line in source :
    lineno += 1
    indent, data = LINE.match(line.decode('UTF8')).groups()
    indent = len(indent.expandtabs())
    if not data :
      yield (BLANK,)
      continue
    while indent < stack[ -1] :
      if indent > stack[ -2] :
        stack[ -1] = indent
      else :
        stack.pop()
        yield (DEDENT,)
    if indent == stack[ -1] :
      yield (SAMEDENT, data, lineno)
    else :
      stack.append(indent)
      yield (INDENT, data, lineno)

def getNode(source) :
  """ Given input buffer, yield nodes (cf, DOM parser)"""
  stack = [ Node() ]
  blanks = 0
  lineno = 1
  for event in getEvent(source) :
    if event[ 0] == INDENT :
      node = Node(event[ 1], blanks, event[ 2])
      blanks = 0
      stack[ -1].children.append(node)
      stack.append(node)
    elif event[ 0] == DEDENT :
      stack.pop()
    elif event[ 0] == SAMEDENT :
      if len(stack) == 2 :
        yield stack[ 0].children[ -1]
      node = Node(event[ 1], blanks, event[ 2])
      blanks = 0
      stack[ -2].children.append(node)
      stack[ -1] = node
    else :
      blanks += 1
  yield stack[ 0].children and stack[ 0].children[ -1] or stack[ 0]

def getNodes(source) :
  """ Slurp the whole Atomic file """
  nodes = []
  for node in getNode(source) :
    nodes.append(node)
  return nodes

# ////////////////////////////////////////////////////////////////
# AtomicStyle

class AtomicStyle :
  """ Inherit from this class; override 'any' """
  def __init__(self) :
    self.map = {}
    self.prefix = "f_"
  def setPrefix(self, prefix) :
    self.prefix = prefix
  def setMap(self, key, value) :
    self.map[ key] = value
  def style(self, children, args = None) :
    if type(children) != type([]) :
      children = [ children]
    out = []
    for child in children :
      out.append(self.styleNode(child, args))
    return out
  def styleNode(self, node, args = None) :
    gi = node.getName()
    func = "%s%s" % (self.prefix, self.map.get(gi, gi))
    if func in dir(self) :
      return eval("self.%s( node, args)" % func)
    else :
      return self.any(node, args)
  def any(self, node, args = None) :
    pass

# ////////////////////////////////////////////////////////////////
# XML Parser Interface

import xml.sax, xml.sax.handler

class XmlParser(xml.sax.ContentHandler, xml.sax.handler.DTDHandler) :
  def __init__(self, buffer) :
    self.buffer = buffer
    self.nodeStack = [ Node("!xml")]
    self.root = self.nodeStack[ 0]
  def getRoot(self) :
    parser = xml.sax.make_parser()
    parser.setContentHandler(self)
    parser.setDTDHandler(self)
    parser.setErrorHandler(xml.sax.handler.ErrorHandler())
    parser.parse(self.buffer)
    return self.root
  def filter(self, data) :
    data = data.replace('\n', r'\n')
    data = data.replace('\\', r'\\')
    return data
  def startElement(self, name, atts) :
    node = Node(name)
    keys = atts.keys()
    keys.sort()
    for att in keys :
      node.children.append(Node("@ %s %s" % (att, self.filter(atts[ att]))))
    if self.nodeStack :
      self.nodeStack[ -1].children.append(node)
    else :
      self.root = node
    self.nodeStack.append(node)
  def endElement(self, name) :
    del self.nodeStack[ -1]
  def characters(self, data) :
    data = data.strip()
    if data :
      node = Node(". %s" % self.filter(data))
      self.nodeStack[ -1].children.append(node)
  def notationDecl(self, name, publicId, systemId) :
    node = Node("!notation %s" % name)
    node.children.append(Node("publicId %s" % self.filter(publicId or "")))
    node.children.append(Node("systemId %s" % self.filter(systemId or "")))
    self.nodeStack[ -1].children.append(node)
  def unparsedEntityDecl(self, name, publicId, systemId, ndata) :
    node = Node("!entity %s" % name)
    node.children.append(Node("publicId %s" % self.filter(publicId or "")))
    node.children.append(Node("systemId %s" % self.filter(systemId or "")))
    node.children.append(Node("ndata %s" % self.filter(ndata or "")))
    self.nodeStack[ -1].children.append(node)

