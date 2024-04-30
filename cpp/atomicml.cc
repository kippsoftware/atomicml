#include "atomicml.h"
#include <iostream>

AtomicML::AtomicML(std::istream &source) : source(source) {
  stack.push_back(-1);
  state = INDENTING;
}

AtomicML::~AtomicML() {
  if (nodes.size() > 1) {
    delete nodes[1];
  }
}

// Split line into data and indent count
int splitLine(string &line, string &data) {
  int indent = 0;
  data = "";
  for (int whichChar = 0; whichChar < line.size(); whichChar++) {
    char c = line[whichChar];
    if (c == ' ') {
      indent++;
    } else if (c == '\t') {
      indent += 8 - indent % 8;
    } else {
      data = line.substr(whichChar);
      break;
    }
  }
  return indent;
}

AtomicML::Token AtomicML::nextToken(string &out) {
  string line;
  out.clear();
  if (state == INDENTING) {
    if (!getline(source, line)) {
      return END;
    }
    indent = splitLine(line, data);
  }
  if (data.size() == 0) {
    return BLANK;
  }
  if (indent < stack.back()) {
    if (indent > stack[stack.size() - 2]) {
      stack[stack.size() - 1] = indent;
    } else {
      state = DEDENTING;
      stack.pop_back();
      return DEDENT;
    }
  }
  state = INDENTING;
  out = data;
  if (indent == stack.back()) {
    return SAMEDENT;
  }
  stack.push_back(indent);
  return INDENT;
}

Node::~Node() {
  Node *child = first;
  while (child) {
    Node *p = child;
    child = child->next;
    delete p;
  }
}

void Node::addChild(Node *child) {
  if (last == NULL) {
    first = last = child;
  } else {
    last = last->next = child;
  }
}

string Node::toString(string prefix) {
  string out(prefix + data);
  for (Node *child = first; child; child = child->next) {
    out += "\n" + child->toString(prefix + "  ");
  }
  return out;
}

Node *AtomicML::parseNode() {
  string data;
  Token token = BLANK;
  Node *node = NULL;
  Node *out = NULL;
  while (token != END) {
    token = nextToken(data);
    cout << "nextToken " << token << " " << data << "\n";
    switch (token) {
    case BLANK:
      break;
    case INDENT:
      node = new Node(data);
      if (nodes.size()) {
        nodes.back()->addChild(node);
      }
      nodes.push_back(node);
      break;
    case DEDENT:
      nodes.pop_back();
      break;
    case SAMEDENT:
      node = new Node(data);
      if (nodes.size() == 1) {
        out = nodes.back();
        nodes.pop_back();
      } else {
        nodes[nodes.size() - 1]->addChild(node);
        nodes.pop_back();
      }
      nodes.push_back(node);
      if (out) {
        return out;
      }
      break;
    case END:
      if (nodes.size()) {
        out = nodes[0];
        nodes.pop_back();
      }
      return out;
    }
  }
  return NULL;
}
