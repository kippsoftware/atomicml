CC=gcc
CXX=g++
RM=rm -f
CPPFLAGS=-g
LDFLAGS=-g

SRCS=atomicml.cc atomicml_test.cc
OBJS=$(subst .cc,.o,$(SRCS))

all: atomicml_test

atomicml_test: $(OBJS)
	$(CXX) $(LDFLAGS) -o atomicml_test $(OBJS)

atomicml_test.o: atomicml.cc atomicml.h

atomicml.o: atomicml.h

clean:
	$(RM) $(OBJS)

distclean: clean
	$(RM) atomicml_test
