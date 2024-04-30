#include "atomicml.h"
#include <iostream>
#include <sstream>

using namespace std;

class AtomicMLTest {

  void testNode() {
    cout << "testNode\n";
    Node *one = new Node("one");
    Node *two = new Node("two");
    one->addChild(two);
    cout << one->toString("");
    cout << "\n";
    delete one;
  }

  void testConstructor() {
    cout << "testConstructor\n";
    stringstream source("one\n  two");
    AtomicML atomic(source);
  }

  void testTokenize() {
    cout << "testTokenize\n";
    stringstream source("\none\n  two\nthree");
    AtomicML atomic(source);
    string data;
    AtomicML::Token token = AtomicML::BLANK;
    while (token != AtomicML::END) {
      token = atomic.nextToken(data);
      cout << "  token " << token << " " << data << "\n";
    }
  }

  void testBackdent() {
    cout << "testBackdent\n";
    stringstream source("  one\n two\nthree");
    AtomicML atomic(source);
    string data;
    AtomicML::Token token = AtomicML::BLANK;
    while (token != AtomicML::END) {
      token = atomic.nextToken(data);
      cout << "  token " << token << " " << data << "\n";
    }
  }

  void testParse(string input) {
    cout << "testParse\n";
    stringstream source(input);
    AtomicML atomic(source);
    Node *node;
    while ((node = atomic.parseNode()) != NULL) {
      cout << node->toString(".") << "\n";
    }
  }

public:
  AtomicMLTest() {
    testNode();
    testConstructor();
    testTokenize();
    testBackdent();
    testParse("one");
    testParse("one\ntwo");
    testParse("one\n  two\n  three\nfour");
    testParse("");
  }
};

int main(int argc, char **argv) {
  AtomicMLTest test;
  return 0;
}
