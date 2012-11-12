#include <unistd.h>
#include <signal.h>
#include <string.h>
#include <iostream>

volatile sig_atomic_t stop = 0;
void sig_handler(int signum)
{
    stop = signum;
}

int main() {
    size_t counter = 0;
    
    signal(SIGTERM, sig_handler);
    signal(SIGINT, sig_handler);

    while(stop == 0) {
	std::cout << counter++ << std::endl;
	usleep(5000); //Slow things down a bit
    }
    std::cerr << "Generated " << counter << " numbers before receiving " << strsignal(stop) << " signal." << std::endl;
}
