"""
sliml.py - new SliML parser for Python

usage:
    import sliml
    # 0 is start state that expects title
    html = sliml.SliML().getHtml(0, slimlData)

author: Neill A. Kipp
created: March 15, 2004
modified: April 6, 2004 - NK - now shows trailing single line
modified: Sept 15, 2005 - NK - now allows *bulletline
modified: June 20, 2005 - NK - fixed missing first indented line bug
modified: Sept 22, 2023 - NK - refactor and upgrade to python3

"""

import re
import io
import atomicml


class Token:
    def __init__(self, name, pattern):
        self.name = name
        self.pattern = pattern

    def __str__(self):
        return f"{self.name} {self.pattern}"


class Action:
    def __init__(self, see, funcs, goto):
        self.see = see
        self.funcs = funcs
        self.goto = goto

    def __str__(self):
        return f"{self.see} {' '.join(self.funcs)} {self.goto}"


class State:
    def __init__(self, name):
        self.name = name
        self.actions = {}

    def __str__(self):
        out = [f"state {self.name}"]
        for action in self.actions.values():
            out.append(str(action))
        return "\n  ".join(out)


class SliML(atomicml.AtomicStyle):
    grammar = r"""
tokens
  blank     \s*$
  break     //
  subhead   \+
  table     --
  colStart  <col
  colEnd    </col
  preStart  <pre
  preEnd    </pre
  comment   #
  item      \s*[\*\-]
  indent    \s+
  line      .?
state start
  blank ignore start
  break ignore start
  colEnd ignore start
  colStart startColumn columnHead
  comment comment start
  indent title body
  item title body
  line title body
  preEnd ignore start
  preStart startPre pre
  subhead title body
  table startTable tableHead
state body
  blank ignore body
  break ignore slideHead
  colEnd endColumns body
  colStart startColumn columnHead
  comment comment body
  indent startIndent indent indent
  item startList list
  line hold hold
  preEnd ignore body
  preStart startPre pre
  subhead subhead body
  table startTable tableHead
state hold
  blank startPara endPara body
  break startPara endPara slideHead
  colEnd startPara endPara endColumns body
  colStart startPara endPara startColumn columnHead
  comment comment hold
  indent startIndent holdIndent indent indent
  item startPara endPara startList list
  line startPara paraLine para
  preEnd ignore hold
  preStart startPara endPara startPre pre
  subhead startPara endPara subhead body
  table startPara endPara startTable tableHead
state para
  blank endPara body
  break endPara slideHead
  colEnd endPara endColumns body
  colStart endPara startColumn columnHead
  comment comment para
  indent endPara hold hold
  item endPara startList list
  line paraLine para
  preEnd ignore para
  preStart endPara startPre pre
  subhead endPara subhead body
  table endPara startTable tableHead
state indent
  blank endIndent body
  break endIndent slideHead
  colEnd endIndent endColumns body
  colStart endIndent startColumn columnHead
  comment comment indent
  indent indent indent
  item indent indent
  line endIndent hold hold
  preEnd ignore indent
  preStart endIndent startPre pre
  subhead endIndent subhead body
  table endIndent startTable tableHead
state list
  blank endList body
  break endList slideHead
  colEnd endList endColumns body
  colStart endList startColumn columnHead
  comment comment list
  indent continueItem list
  item item list
  line endList hold hold
  preEnd ignore list
  preStart endList startPre pre
  subhead endList subhead body
  table endList startTable tableHead
state tableHead
  blank ignore table
  break endTable slideHead
  colEnd endTable endColumns body
  colStart endTable startColumn columnHead
  comment comment tableHead
  indent tableHead table
  item tableHead table
  line tableHead table
  preEnd ignore table
  preStart endTable startPre pre
  subhead tableHead table
  table endTable body
state table
  blank blankRow table
  break endTable slideHead
  colEnd endTable endColumns body
  colStart endTable startColumn columnHead
  comment comment table
  indent tableRow table
  item tableRow table
  line tableRow table
  preEnd ignore table
  preStart endTable startPre pre
  subhead tableRow table
  table endTable body
state columnHead
  blank ignore body
  break endColumns slideHead
  colEnd endColumns body
  colStart startColumn columnHead
  comment comment columnHead
  indent columnHead body
  item startList list
  line columnHead body
  preEnd ignore body
  preStart startPre pre
  subhead subhead body
  table startTable tableHead
state pre
  blank preLine pre
  break preLine pre
  colEnd preLine pre
  colStart preLine pre
  comment preLine pre
  indent preLine pre
  item preLine pre
  line preLine pre
  preEnd endPre body
  preStart preLine pre
  subhead preLine pre
  table preLine pre
state slideHead
  blank emptySlideHead body
  break emptySlideHead slideHead
  colEnd ignore body
  colStart emptySlideHead columnHead
  comment comment slideHead
  indent slideHead body
  item emptySlideHead startList list
  line slideHead body
  preEnd emptySlideHead body
  preStart emptySlideHead pre
  subhead subhead body
  table emptySlideHead tableHead
"""

    def __init__(self):
        super().__init__()
        self.tokens = []
        self.states = {}
        self.style(atomicml.parse_nodes(self.grammar))
        self.stack = []
        self.inColumns = 0
        self.holdLine = ""

    def f_tokens(self, node):
        for child in node.children:
            token_name, pattern = child.data.split(None, 1)
            self.tokens.append(Token(token_name, re.compile(pattern)))

    def f_state(self, node):
        state_name = node.data.split(None, 1)[1]
        state = self.states[state_name] = State(state_name)
        for child in node.children:
            fields = child.data.split()
            see = fields[0]
            funcs = fields[1:-1]
            goto = fields[-1]
            state.actions[see] = Action(see, funcs, goto)

    def __str__(self):
        out = ["tokens"]
        for token in self.tokens:
            out.append(f"  {token}")
        for state in self.states.values():
            out.append(str(state))
        return "\n".join(out)

    def parse(self, source, out):
        source = io.StringIO(source) if isinstance(source, str) else source
        self.stack = [-1]
        state = self.states["start"]
        for line in source:
            for token in self.tokens:
                if token.pattern.match(line):
                    action = state.actions[token.name]
                    for func in action.funcs:
                        getattr(self, func)(line.rstrip(), out)
                    state = self.states[action.goto]
                    break
        if self.holdLine:
            self.startPara("", out)

    def ignore(self, line, out):
        pass

    def title(self, line, out):
        out.append(f"<h1>{self.cook(line)}</h1>\n<div>")

    def hold(self, line, out):
        self.holdLine = line

    def startPara(self, line, out):
        out.append(f"<p>{self.cook(self.holdLine)}")
        self.holdLine = ""

    def paraLine(self, line, out):
        out.append(f"{self.cook(line)}")

    def endPara(self, line, out):
        out.append("</p>")

    INDENT = re.compile(r"([\t ]*)(.*)")

    def startList(self, line, out):
        indent, line = self.INDENT.match(line).groups()
        indent = len(indent.expandtabs())
        line = line[1:]
        self.stack.append(indent)
        out.append(f"<ul>\n<li>{self.cook(line)}")

    def item(self, line, out):
        indent, line = self.INDENT.match(line).groups()
        indent = len(indent.expandtabs())
        line = line[1:]
        while indent < self.stack[-1]:
            if indent > self.stack[-2]:
                self.stack[-1] = indent
            else:
                self.stack.pop()
                out.append("</ul>")
        if indent == self.stack[-1]:
            out.append(f"<li>{self.cook(line)}")
        else:
            self.stack.append(indent)
            out.append(f"<ul>\n<li>{self.cook(line)}")

    def continueItem(self, line, out):
        out.append(self.cook(line))

    def endList(self, line, out):
        while self.stack[-1] > -1:
            out.append("</ul>")
            self.stack.pop()

    def startIndent(self, line, out):
        out.append("<pre>")

    def holdIndent(self, line, out):
        self.indent(self.holdLine, out)
        self.holdLine = ""

    def indent(self, line, out):
        indent, data = self.INDENT.match(line).groups()
        indent = "&nbsp;" * len(indent.expandtabs())
        out.append(f"{indent}{data}")

    def endIndent(self, line, out):
        out.append("</pre>")

    def startTable(self, line, out):
        out.append("<table>")
        _, line = line.split(None, 1)
        for align in line:
            if align == "l":
                align = "left"
            elif align == "c":
                align = "center"
            elif align == "r":
                align = "right"
            out.append(f'<col align="{align}">')

    CELL = re.compile(r"\t|(?:  +)")

    def tableHead(self, line, out):
        out.append("<tr>")
        for cell in self.CELL.split(line):
            out.append(f"<th>{cell}</th>")
        out.append("</tr>")

    def tableRow(self, line, out):
        out.append("<tr>")
        for cell in self.CELL.split(line):
            out.append(f"<td>{cell}</td>")
        out.append("</tr>")

    def blankRow(self, line, out):
        out.append("<tr><td></td></tr>")

    def endTable(self, line, out):
        out.append("</table>")

    def startColumn(self, line, out):
        if not self.inColumns:
            out.append("<table><tr><td>")
            self.inColumns = 1
        else:
            out.append("</td><td>")

    def columnHead(self, line, out):
        out.append(f'<div class="colhead">{line}</div>')

    def endColumns(self, line, out):
        out.append("</td></tr></table>")
        self.inColumns = 0

    def startPre(self, line, out):
        out.append("<pre>")

    def preLine(self, line, out):
        line = line.replace("&", "&amp;")
        line = line.replace("<", "&lt;")
        out.append(line)

    def endPre(self, line, out):
        out.append("</pre>")

    def slideHead(self, line, out):
        out.append(f"<h2>{line}</h2>")

    def emptySlideHead(self, line, out):
        out.append("<h1></h1>")

    def subhead(self, line, out):
        out.append(f"<h3>{line[1:]}</h3>")

    MDASH = re.compile(r"--")
    LDQUOT = re.compile(r'"(?=\w)')
    RDQUOT = re.compile(r'"')
    LQUOT = re.compile(r"`")
    RQUOT = re.compile(r"'")

    def cook(self, line):
        line = self.MDASH.sub("&mdash;", line)
        line = self.LDQUOT.sub("&ldquo;", line)
        line = self.RDQUOT.sub("&rdquo;", line)
        line = self.LQUOT.sub("&lsquo;", line)
        line = self.RQUOT.sub("&rsquo;", line)
        return line


# ////////////////////////////////////////////////////////////////

if __name__ == "__main__":
    import sys

    html = []
    source = open(sys.argv[-1], encoding="utf-8")
    SliML().parse(source, html)
    for line in html:
        print(line)
