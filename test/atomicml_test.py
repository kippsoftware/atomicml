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
    nodes = []
    for node in parse_node(source):
        nodes.append(node)
    assert len(nodes) == 2
    assert nodes[0].data == "one"
    assert len(nodes[0].children) == 2
    assert nodes[1].data == "four"


class MyStyle(AtomicStyle):
    def __init__(self):
        super().__init__()
        self.pre = "g_"
        self.map["*"] = "li"
        self.map["."] = "text"

    def g_root(self, value, children, args, out):
        out.append(f"<h1>{value}</h1>")
        self.style(children, args, out)

    def g_li(self, value, children, args, out):
        out.append(f"<li>{value}</li>")

    def g_text(self, value, children, args, out):
        out.append(f"<span>{value}</span>")
        self.style(children, args, out)


def test_style_node():
    source = """\
root
  . two
    * three
    * four
    * five
"""
    args = None
    out = []
    nodes = parse_nodes(source)
    assert len(nodes) == 1
    MyStyle().style(nodes, args, out)
    assert len(out) == 5
    assert "<h1>" in out[0]
    assert "<span>" in out[1]
    assert "<li>" in out[2]
    assert "<li>" in out[3]
    assert "<li>" in out[4]


def test_xml():
    source = """\
<?xml version="1.0"?>
<root name="zero">
<ul>
<li>one</li>
<li>two</li>
</ul>
</root>
"""
    root = XmlParser().parse(source)
    assert len(root.children) == 1
    print(str(root))
