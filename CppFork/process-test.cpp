#include <cstdlib>

#include <iostream>
#include <string>

#include "Process.h"

int main(int, char*[])
{
    Process::initHandlers();

    { //begin scope
	Process p({"./consumer"});

	std::string line;

	while(getline(std::cin, line)) {
	    p.write(line+"\n");
	    std::string pread = p.readline();
	    std::cout << "Line from process[" << p.pid() << "]: " << pread;
	}

    } //end scope
    std::cout << "Process object has gone out of scope.\n"
"Check that the child process has been cleaned up and "
"all unused file descriptors for this process [" << getpid() << "] are closed.\n"
"Press Ctrl+C to exit" << std::endl;
    while(1)
    {
	sleep(1);
    }
    return EXIT_SUCCESS;
}
