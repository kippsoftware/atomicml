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

The SliML Document Formatter, Copyright 1995-2004, Neill A. Kipp.
Permission is granted to use and modify this program without
restriction, as long as the copyright notice and this permission
notice are included in all copies and modifications. This software is
provided "as is," without warranty of any kind, and Neill A. Kipp will
not be liable for any claim, damages, or liability in connection with
the use or modification of this software.

See http://sliml.kippsoftware.com/ for license information.

"""

# Twelve tokens
tokens = """\
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
line      .?""".split("\n")

# Eleven states
# 0 title
# 1 body
# 2 hold
# 3 para
# 4 indent
# 5 list 
# 6 tableHead
# 7 table
# 8 columnHead
# 9 pre
# 10 slideHead

grammar = """\
0 blank ignore 0
0 break ignore 0
0 colEnd ignore 0
0 colStart startColumn 8
0 comment comment 0
0 indent title 1
0 item title 1
0 line title 1
0 preEnd ignore 0
0 preStart startPre 9
0 subhead title 1
0 table startTable 6
1 blank ignore 1
1 break ignore 10
1 colEnd endColumns 1
1 colStart startColumn 8
1 comment comment 1
1 indent startIndent indent 4
1 item startList 5
1 line hold 2
1 preEnd ignore 1
1 preStart startPre 9
1 subhead subhead 1 
1 table startTable 6
2 blank startPara endPara 1
2 break startPara endPara 10
2 colEnd startPara endPara endColumns 1
2 colStart startPara endPara startColumn 8
2 comment comment 2
2 indent startIndent holdIndent indent 4
2 item startPara endPara startList 5
2 line startPara paraLine 3
2 preEnd ignore 2
2 preStart startPara endPara startPre 9
2 subhead startPara endPara subhead 1
2 table startPara endPara startTable 6
3 blank endPara 1
3 break endPara 10
3 colEnd endPara endColumns 1
3 colStart endPara startColumn 8
3 comment comment 3
3 indent endPara hold 2
3 item endPara startList 5
3 line paraLine 3
3 preEnd ignore 3
3 preStart endPara startPre 9
3 subhead endPara subhead 1
3 table endPara startTable 6
4 blank endIndent 1
4 break endIndent 10
4 colEnd endIndent endColumns 1
4 colStart endIndent startColumn 8
4 comment comment 4
4 indent indent 4
4 item indent 4
4 line endIndent hold 2
4 preEnd ignore 4
4 preStart endIndent startPre 9
4 subhead endIndent subhead 1
4 table endIndent startTable 6
5 blank endList 1
5 break endList 10
5 colEnd endList endColumns 1
5 colStart endList startColumn 8
5 comment comment 5
5 indent continueItem 5
5 item item 5
5 line endList hold 2
5 preEnd ignore 5
5 preStart endList startPre 9
5 subhead endList subhead 1
5 table endList startTable 6
6 blank ignore 7
6 break endTable 10
6 colEnd endTable endColumns 1
6 colStart endTable startColumn 8
6 comment comment 6
6 indent tableHead 7
6 item tableHead 7
6 line tableHead 7
6 preEnd ignore 7
6 preStart endTable startPre 9
6 subhead tableHead 7
6 table endTable 1
7 blank blankRow 7
7 break endTable 10
7 colEnd endTable endColumns 1
7 colStart endTable startColumn 8
7 comment comment 7
7 indent tableRow 7
7 item tableRow 7
7 line tableRow 7
7 preEnd ignore 7
7 preStart endTable startPre 9
7 subhead tableRow 7
7 table endTable 1
8 blank ignore 1
8 break endColumns 10
8 colEnd endColumns 1
8 colStart startColumn 8
8 comment comment 8
8 indent columnHead 1
8 item startList 5
8 line columnHead 1
8 preEnd ignore 1
8 preStart startPre 9
8 subhead subhead 1
8 table startTable 6
9 blank preLine 9
9 break preLine 9
9 colEnd preLine 9
9 colStart preLine 9
9 comment preLine 9
9 indent preLine 9
9 item preLine 9
9 line preLine 9
9 preEnd endPre 1
9 preStart preLine 9
9 subhead preLine 9
9 table preLine 9
10 blank emptySlideHead 1
10 break emptySlideHead 10
10 colEnd ignore 1
10 colStart emptySlideHead 8
10 comment comment 10
10 indent slideHead 1
10 item emptySlideHead startList 5
10 line slideHead 1
10 preEnd emptySlideHead 1
10 preStart emptySlideHead 9
10 subhead subhead 1
10 table emptySlideHead 6
""".split("\n")

import re

class SliML :
  def __init__ (self) :
    out = []
    self.patterns = []
    self.names = []
    for token in tokens :
      (name, pattern) = token.split()
      self.patterns.append(re.compile(pattern))
      self.names.append(name)
    self.INDENT = re.compile(r"([\t ]*)(.*)")
    self.CELL = re.compile(r"\t|(?:  +)")
    self.funcs = {}
    self.goto = {}
    for line in grammar :
      if not line.strip() :
        continue
      fields = line.split()
      state = fields.pop(0)
      see = fields.pop(0)
      goto = fields.pop(-1)
      self.funcs["%s %s" % (state, see)] = ' '.join(fields)
      self.goto["%s %s" % (state, see)] = goto
    self.inColumns = 0
    self.holdLine = ""
    self.state = 0

  def __str__(self) :
    out = []
    out.append("patterns")
    for pattern in self.patterns :
      out.append("  %s" % pattern.pattern)
    out.append("states")
    for whichState in range(11) :
      for whichToken in self.names :
        whichFunc = self.funcs["%s %s" % (whichState, whichToken)]
        whichGoto = self.goto["%s %s" % (whichState, whichToken)]
        out.append("  %s %s %s %s" % (whichState, whichToken, whichFunc or "None", whichGoto))
    return '\n'.join(out)

  def setState(self, state) :
    self.state = state
    return self

  def getHtml(self, state, data) :
    self.setState(state)
    return self.parse(data)

  def parse(self, data) :
    state = self.state
    self.out = []
    self.stack = [-1]
    for line in data.split('\n') :
      whichPattern = 0
      for pattern in self.patterns :
        if pattern.match(line) :
          token = self.names[whichPattern]
          goto = self.goto["%s %s" % (state, token)]
          for func in self.funcs["%s %s" % (state, token)].split() :
            eval("self.%s(line)" % func)
          state = self.goto["%s %s" % (state, token)]
          break
        whichPattern += 1
    if self.holdLine :
      self.startPara("")
    return "".join(self.out)

  def ignore(self, line) :
    self.out.append("")

  MDASH = re.compile(r"--")
  LDQUOT = re.compile(r'"(?=\w)');
  RDQUOT = re.compile(r'"');
  LQUOT = re.compile(r"`");
  RQUOT = re.compile(r"'");

  def cook(self, line) :
    line = self.MDASH.sub("&mdash;", line)
    line = self.LDQUOT.sub("&ldquo;", line)
    line = self.RDQUOT.sub("&rdquo;", line)
    line = self.LQUOT.sub("&lsquo;", line)
    line = self.RQUOT.sub("&rsquo;", line)
    return line

  def title(self, line) :
    self.out.append('<h1>%s</h1>\n<div>\n' % line)

  def hold(self, line) :
    self.holdLine = line

  def startPara(self, line) :
    self.out.append('<p>%s\n' % self.cook(self.holdLine))
    self.holdLine = ""

  def paraLine(self, line) :
    self.out.append('%s\n' % self.cook(line))

  def endPara(self, line) :
    self.out.append('</p>\n\n')

  def startList(self, line) :
    indent, line = self.INDENT.match(line).groups()
    indent = len(indent.expandtabs())
    line = line[1:]
    self.stack.append(indent)
    self.out.append('<ul>\n')
    self.out.append('<li>%s\n' % self.cook(line))

  def item(self, line) :
    indent, line = self.INDENT.match(line).groups()
    indent = len(indent.expandtabs())
    line = line[1:]
    while (indent < self.stack[-1]) :
      if (indent > self.stack[-2]) :
        self.stack[-1] = indent
      else :
        del self.stack[-1]
        self.out.append('</ul>\n')
    if (indent == self.stack[-1]) :
      self.out.append('<li>%s\n' % self.cook(line))
    else :
      self.stack.append(indent)
      self.out.append('<ul>\n')
      self.out.append('<li>%s\n' % self.cook(line))

  def continueItem(self, line) :
    self.out.append('%s\n' % self.cook(line))

  def endList(self, line) :
    while (self.stack[-1] > -1) :
      self.out.append('</ul>\n')
      del self.stack[-1]
    self.out.append('\n')

  def startIndent(self, line) :
    self.out.append('<pre>\n')

  def holdIndent(self, line) :
    self.indent(self.holdLine)
    self.holdLine = ""

  def indent(self, line) :
    indent, data = self.INDENT.match(line).groups()
    indent = "&nbsp;" * len(indent.expandtabs())
    self.out.append('%s%s\n' % (indent, data))

  def endIndent(self, line) :
    self.out.append('</pre>\n\n')

  def startTable(self, line) :
    self.out.append('<table>\n')
    x, line = line.split(None, 1)
    for align in line :
      if align == "l" : align = "left"
      elif align == "c" : align = "center"
      elif align == "r" : align = "right"
      self.out.append('<col align="%s">\n' % align)

  def tableHead(self, line) :
    self.out.append('<tr>')
    for cell in self.CELL.split(line) :
      self.out.append('<th>%s</th>' % cell)
    self.out.append('</tr>\n')

  def tableRow(self, line) :
    self.out.append('<tr>')
    for cell in self.CELL.split(line) :
      self.out.append('<td>%s</td>' % cell)
    self.out.append('</tr>\n')

  def blankRow(self, line) :
    self.out.append('<tr><td></td></tr>\n')

  def endTable(self, line) :
    self.out.append('</table>\n\n')

  def startColumn(self, line) :
    if (not self.inColumns) :
      self.out.append('<table><tr><td>\n')
      self.inColumns = 1
    else :
      self.out.append('</td><td>\n')

  def columnHead(self, line) :
    self.out.append('<div class="colhead">%s</div>\n' % line)

  def endColumns(self, line) :
    self.out.append('</td></tr></table>\n\n')
    self.inColumns = 0

  def startPre(self, line) :
    self.out.append('<pre>\n')

  def preLine(self, line) :
    line = line.replace('&', '&amp;')
    line = line.replace('<', '&lt;')
    self.out.append('%s\n' % line)

  def endPre(self, line) :
    self.out.append('</pre>\n\n')

  def slideHead(self, line) :
    self.out.append('<h2>%s</h2>\n\n' % line)

  def emptySlideHead(self, line) :
    self.out.append('<h1></h1>\n\n')

  def subhead(self, line) :
    self.out.append('<h3>%s</h3>\n\n' % line[1:].strip())

# ////////////////////////////////////////////////////////////////

if __name__ == '__main__' :
  sliml = SliML()
  # print sliml
  sliml.setState(0)
  test = sliml.parse("""\
Head

Paragraph 1.
This is still paragraph 1.
Still P1.

* Bullet1
* Bullet2
* Bullet3
  - Bullet3-1
    - Bullet 4-2
  - Back one level
- Back another level

-- lll
table   table   table
c   c   c 
--

////////////////

indent1
  indent2
    indent3

para

  already indent 1
  already indent 2
  already indent 3

////////////////
</pre>

////////////////
* HI
////////////////

////////////////
Section

more paragraphs1
more paragraphs2
more paragraphs3.

+ Subhead

<pre>Hi
</pre>

<col>
H1
column body1
<col>
H2
column body2, first line
column body2, last line.
</col>
""")

  print sliml
  print test
