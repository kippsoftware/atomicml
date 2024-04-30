"""AtomicML Test"""

from atomicml import Node, Indent, SameDent, Dedent, Blank
from atomicml import tokenize, parse_node, parse_nodes
from atomicml import AtomicStyle, XmlParser

# pylint: disable=missing-class-docstring, missing-function-docstring, unused-argument


def test_node():
    """Node, init, str"""
    node = Node("one")
    node_string = str(node)
    assert node_string == "one"
    node.children.append(Node("two"))
    node_string = str(node)
    assert node_string == "one\n  two"

def test_tokenize():
    """Indent, SameDent, Dedent, Blank"""
    source = "one\n  two\n\n  three\nfour"
    tokens = []
    for token in tokenize(source):
        print(token)
        tokens.append(token)
    assert len(tokens) == 6
    assert isinstance(tokens[0], Indent)
    assert isinstance(tokens[1], Indent)
    assert isinstance(tokens[2], Blank)
    assert isinstance(tokens[3], SameDent)
    assert isinstance(tokens[4], Dedent)
    assert isinstance(tokens[5], SameDent)


def test_parse_node():
    """Parse nodes"""
    source = "one\n  two\n\n  three\nfour"
    nodes = [ node for node in parse_node(source) ]
    assert len(nodes) == 2
    assert nodes[0].data == "one"
    assert len(nodes[0].children) == 2
    assert nodes[1].data == "four"

def test_parse_node_next():
    gen = parse_node("one\ntwo\nthree")
    assert next(gen).data == "one"
    assert next(gen).data == "two"
    assert next(gen).data == "three"

class MyStyle(AtomicStyle):
    def __init__(self):
        super().__init__()
        self.pre = "g_"
        self.map["*"] = "li"
        self.map["."] = "text"
        self.out = []

    def g_root(self, node):
        _, value = node.data.split(None, 1)
        self.out.append(f"<h1>{value}</h1>")
        self.style(node.children)

    def g_li(self, node):
        _, value = node.data.split(None, 1)
        self.out.append(f"<li>{value}</li>")

    def g_text(self, node):
        _, value = node.data.split(None, 1)
        self.out.append(f"<span>{value}</span>")
        self.style(node.children)

ATOMIC_SOURCE = """\
root label
  . two
    * three
    * four
    * five
"""

def test_style_node():
    nodes = parse_nodes(ATOMIC_SOURCE)
    assert len(nodes) == 1
    style = MyStyle()
    style.style(nodes)
    assert len(style.out) == 5
    assert "<h1>" in style.out[0]
    assert "<span>" in style.out[1]
    assert "<li>" in style.out[2]
    assert "<li>" in style.out[3]
    assert "<li>" in style.out[4]

class MyStyleArgs(AtomicStyle):
    def __init__(self):
        super().__init__()
        self.map["*"] = "li"
        self.map["."] = "text"

    def f_root(self, node, out):
        _, value = node.data.split(None, 1)
        out.append(f"<h1>{value}</h1>")
        self.style(node.children, out=out)

    def f_li(self, node, out):
        _, value = node.data.split(None, 1)
        out.append(f"<li>{value}</li>")

    def f_text(self, node, out):
        _, value = node.data.split(None, 1)
        out.append(f"<span>{value}</span>")
        self.style(node.children, out=out)

def test_style_node_args():
    nodes = parse_nodes(ATOMIC_SOURCE)
    assert len(nodes) == 1
    style = MyStyleArgs()
    out = []
    style.style(nodes, out = out)
    assert len(out) == 5
    assert "<h1>" in out[0]
    assert "<span>" in out[1]
    assert "<li>" in out[2]
    assert "<li>" in out[3]
    assert "<li>" in out[4]

XML_SOURCE = """\
<?xml version="1.0"?>
<root name="zero">
<ul>
<li>one</li>
<li>two</li>
</ul>
</root>
"""

def test_xml():
    root = XmlParser().parse(XML_SOURCE)
    assert len(root.children) == 1
    print(str(root))
