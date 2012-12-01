RESULTS = process-test consumer
PT_CPP_FILES = Process.cpp process-test.cpp
CO_CPP_FILES = consumer.cpp
CPP_FILES = ${PT_CPP_FILES} ${CO_CPP_FILES}
PT_OBJ_FILES = ${PT_CPP_FILES:.cpp=.o}
CO_OBJ_FILES = ${CO_CPP_FILES:.cpp=.o}
OBJ_FILES = ${CPP_FILES:.cpp=.o}

CXXFLAGS = -std=c++11 -ggdb -Wall -Wextra

all: ${RESULTS}

process-test: ${PT_OBJ_FILES}
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $+

consumer: ${CO_OBJ_FILES}
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $+

clean:
	rm -f ${RESULTS} ${OBJ_FILES}
