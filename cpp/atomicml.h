#include <istream>
#include <string>
#include <vector>

using namespace std;

class Node {
public:
  string data;
  Node *first;
  Node *last;
  Node *next;
  Node(string data) : data(data), first(NULL), last(NULL), next(NULL) {}
  ~Node();
  void addChild(Node *child);
  string toString(string prefix);
};

class AtomicML {
  friend class AtomicMLTest;

  // Four token types
  enum Token { BLANK, INDENT, DEDENT, SAMEDENT, END };

  // Tokenizing state types
  enum State { INDENTING, DEDENTING };

  // Push and pop indent levels
  vector<int> stack;

  // State of the parse
  State state;

  // Recent indent level found during parse
  int indent;

  // Recent data from the most recent line parsed
  string data;

  // Source of input for the duration of the parse
  istream &source;

  // Report one of four token types with its associated data
  Token nextToken(string &data);

  // Maintain parentage during parse
  vector<Node *> nodes;

public:
  AtomicML(istream &source);
  ~AtomicML();

  // Caller deletes parsed nodes
  Node *parseNode();
};
