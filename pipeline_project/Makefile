TARGETS = generator consumer dispatcher

all: $(TARGETS)

dispatcher: dispatcher.cpp generator consumer 
	$(CXX) $(LDFLAGS) $(CXXFLAGS) -o $@ $<

generator: generator.cpp
	$(CXX) $(LDFLAGS) $(CXXFLAGS) -o $@ $<

consumer: consumer.cpp
	$(CXX) $(LDFLAGS) $(CXXFLAGS) -o $@ $<

clean:
	@rm -rf $(TARGETS)
