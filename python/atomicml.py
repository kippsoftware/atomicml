"""AtomicML - parse indented lines into a tree of nodes

version: 3.0.0
author: Neill A. Kipp

Copyright (C) 2000-2023 Kipp Software Corporation

////////////////
AtomicML usage

Iterate over Atomic tokens (Indent, Dedent, SameDent, Blank)
  import atomicml
  for token in atomicml.tokenize(open('data.at')):
      print(token)

Iterate to parse a single Atomic node
  import atomicml
  for node in atomicml.parse_node(open('data.at')):
      print(node)

Parse XML into Atomic nodes for easy styling
  import atomicml
  node = atomicml.XmlParser().parse(open('data.xml'))
  print(node)

////////////////
AtomicStyle

Implement your dispatching subclass.

  import atomicml
  class MyStyle(atomicml.AtomicStyle):
    def __init__(self):
      super().__init__()
      self.prefix = 'g_'
      self.setMap('*', 'li')
      self.setMap('.', 'text')
    def g_book(self, node, args):
      print(node.data)
      self.style(children)
    def g_li(self, node, args):
      print(node.data)
      self.style(children)
    def g_text(self, node, args):
      print(node.data)
  MyStyle().style(parse_nodes(open('data.at')))

"""
import io
import re
import xml.sax
import xml.sax.handler

# pylint: disable=too-few-public-methods


class Node:
    """Encapsulate data and children of a tree node"""

    def __init__(self, data="", blanks=0, lineno=0):
        self.data = data
        self.blanks = blanks
        self.lineno = lineno
        self.children = []

    indent = "  "

    def __str__(self, indent=""):
        out = ["" for _ in range(self.blanks)]
        out.append(indent + self.data)
        out.extend(child.__str__(self.indent + indent) for child in self.children)
        return "\n".join(out)


class Token:
    """Base class for the four Atomic token types"""

    def __init__(self, lineno=0, data=""):
        self.lineno = lineno
        self.data = data

    def __str__(self):
        return f"{self.__class__.__name__} {self.lineno} {self.data}"


class Indent(Token):
    """Atomic Indent"""


class SameDent(Token):
    """Atomic SameDent"""


class Dedent(Token):
    """Atomic Dedent"""


class Blank(Token):
    """Atomic Blank"""


def tokenize(source):
    """Iterate over source lines and yield a token for each"""
    atomic_line = re.compile(r"([ \t]*)(.*)")
    stack = [-1]
    lineno = 0
    source = io.StringIO(source) if isinstance(source, str) else source
    for line in source:
        lineno += 1
        indent, data = atomic_line.match(line).groups()
        indent = len(indent.expandtabs())
        if not data:
            yield Blank(lineno)
            continue
        while indent < stack[-1]:
            if indent > stack[-2]:
                stack[-1] = indent
            else:
                stack.pop()
                yield Dedent(lineno)
        if indent == stack[-1]:
            yield SameDent(lineno, data)
        else:
            stack.append(indent)
            yield Indent(lineno, data)


def parse_node(source):
    """Iterate over source lines and yield non-indented nodes"""
    stack = [Node()]
    blanks = 0
    for token in tokenize(source):
        if isinstance(token, Indent):
            node = Node(token.data, blanks, token.lineno)
            blanks = 0
            stack[-1].children.append(node)
            stack.append(node)
        elif isinstance(token, Dedent):
            stack.pop()
        elif isinstance(token, SameDent):
            if len(stack) == 2:
                yield stack[0].children[-1]
            node = Node(token.data, blanks, token.lineno)
            blanks = 0
            stack[-2].children.append(node)
            stack[-1] = node
        else:
            blanks += 1
    yield stack[0].children[-1] if stack[0].children else stack[0]


def parse_nodes(source):
    """Parse the entire AtomicML file into nodes"""
    return [node for node in parse_node(source)]

# ////////////////////////////////////////////////////////////////
# AtomicStyle


class AtomicStyle:
    """Recur through the node tree, match node names, call handlers"""

    def __init__(self):
        self.map = {}
        self.pre = "f_"

    def style(self, children, **kwargs):
        """Recur through children and style"""
        children = children if isinstance(children, list) else [children]
        for node in children:
            name = node.data.split(None, 1)[0]
            style = getattr(self, f"{self.pre}{self.map.get(name, name)}", None)
            if style:
                style(node, **kwargs)
            else:
                self.style(node.children, **kwargs)


# ////////////////////////////////////////////////////////////////
# XML Parser


class XmlParser(xml.sax.ContentHandler, xml.sax.handler.DTDHandler):
    """XmlParser creates Atomic nodes from XML files"""

    def __init__(self):
        super().__init__()
        self.node_stack = []

    def parse(self, source):
        """Parse XML into Atomic Nodes"""
        root = Node("!xml")
        self.node_stack.append(root)
        parser = xml.sax.make_parser()
        parser.setContentHandler(self)
        parser.setDTDHandler(self)
        parser.setErrorHandler(xml.sax.handler.ErrorHandler())
        source = io.StringIO(source) if isinstance(source, str) else source
        parser.parse(source)
        return root

    def filter(self, data):
        """Escape newlines and escapes"""
        return data.replace("\n", r"\n").replace("\\", r"\\")

    def startElement(self, name, attrs):
        node = Node(name)
        for att in sorted(attrs.getNames()):
            node.children.append(Node(f"@{att} {self.filter(attrs.getValue(att))}"))
        self.node_stack[-1].children.append(node)
        self.node_stack.append(node)

    def endElement(self, name):
        self.node_stack.pop()

    def characters(self, content):
        content = content.strip()
        if content:
            node = Node(f". {self.filter(content)}")
            self.node_stack[-1].children.append(node)

    def notationDecl(self, name, publicId, systemId):
        node = Node(f"!notation {name}")
        if publicId:
            node.children.append(Node(f"@public {self.filter(publicId)}"))
        if systemId:
            node.children.append(Node(f"@system {self.filter(systemId)}"))
        self.node_stack[-1].children.append(node)

    def unparsedEntityDecl(self, name, publicId, systemId, ndata):
        node = Node(f"!entity {name}")
        if publicId:
            node.children.append(Node(f"@public {self.filter(publicId)}"))
        if systemId:
            node.children.append(Node(f"@system {self.filter(systemId)}"))
        if ndata:
            node.children.append(Node(f"@ndata {ndata}"))
        self.node_stack[-1].children.append(node)
