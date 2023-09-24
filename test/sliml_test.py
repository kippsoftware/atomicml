import sliml

source = """\
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

-- lcr
head   head   head
left   center   right
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
"""


def test_sliml():
    out = []
    s = sliml.SliML()
    s.parse(source, out)
    print("\n".join(out))
