#include <iostream>
#include <unistd.h>
#include <stdio.h>
#include <sys/types.h>
#include <signal.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <fcntl.h>
#include <sys/stat.h>

int main()
{
    int fds[2];

    // -- For readability. Compiler should generally
    // optimize these out.
    int* fd_read = &fds[0];
    int* fd_write = &fds[1];

    int genpid = 0;

    pipe2(fds, O_CLOEXEC);

    genpid = fork();

    if(genpid == 0)
    {
        dup2(*fd_write, fileno(stdout));
        execv("generator", NULL);
    }
    else if(genpid > 0)
    {
        close(*fd_write);
    }
    else
    {
        std::cerr << "can't spawn generator process" << std::endl;
        exit(1);
    }

    int conspid = 0;

    conspid = fork();

    if(conspid == 0)
    {
        dup2(*fd_read, fileno(stdin));
        execv("consumer", NULL);
    }
    else if(genpid > 0)
    {
        close(*fd_read);
    }
    else
    {
        std::cerr << "can't spawn consumer process" << std::endl;
        exit(2);
    }

    sleep(1);

    pid_t exitstat = 0;

    kill(genpid, SIGTERM);

    waitpid(genpid, &exitstat, 0);

    if(!WIFEXITED(exitstat))
    {
        std::cerr << "generator didn't exit normally" << std::endl;
        exit(3);
    }

    std::cerr << "child[" << genpid << "] has exited with status "
              << WEXITSTATUS(exitstat) 
              << std::endl;

    // flushing cerr because the other function's stdout would klobber this stderr
    std::cerr.flush();

    waitpid(conspid, &exitstat, 0);

    if(!WIFEXITED(exitstat))
    {
        std::cerr << "consumer didn't exit normally" << std::endl;
        exit(4);
    }

    
    std::cerr << "child[" << conspid << "] has exited with status "
              << WEXITSTATUS(exitstat) 
              << std::endl;
    std::cerr.flush();

    return 0;
}

