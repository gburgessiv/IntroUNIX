RESULT := exprtest
O_FILES := exprtest.o driver.o parser.tab.o scanner.o 
AUTO_FILES := parser.tab.cpp parser.tab.hpp stack.hh position.hh lex.Example.cc location.hh scanner.cpp

all: $(RESULT)

$(RESULT): $(O_FILES)
	$(CXX) $(LDFLAGS) $(LOADLIBES) $(LDLIBS) -o $@ $^

driver.o: driver.cpp scanner.hpp parser.tab.hpp driver.hpp 
	$(CXX) $(CPPFLAGS) -c -o $@ $<

parser.tab.o: parser.tab.cpp
	$(CXX) $(CPPFLAGS) -c -o $@ $<

exprtest.o: exprtest.cpp
	$(CXX) $(CPPFLAGS) -c -o $@ $<
	
scanner.o: scanner.cpp scanner.hpp
	$(CXX) $(CPPFLAGS) -c -o $@ $<

scanner.cpp: scanner.ll 
	flex -t $< > $@

parser.tab.hpp: parser.ypp 
	bison $<

parser.tab.cpp: parser.ypp expression.hpp scanner.hpp driver.hpp parser.tab.hpp
	bison $<

clean:
	@rm -f $(O_FILES) $(AUTO_FILES) $(RESULT)
