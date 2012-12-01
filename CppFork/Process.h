#ifndef _PROCESS_H_
#define _PROCESS_H_

#include <unistd.h>
#include <sys/wait.h>

#include <string>
#include <vector>

namespace pipes
{
    enum pipeno
    {
        READ_PIPE,
        WRITE_PIPE,
        SUB_READ_PIPE,
        SUB_WRITE_PIPE,
        ERR_READ_PIPE,
        ERR_WRITE_PIPE
    };
}

class Process
{
public:
    /* Initialize the process, create input/output pipes */
    Process(const std::vector<std::string> &args);
    
    /* Close any open file streams or file descriptors,
       insure that the child has terminated */
    virtual ~Process();
    
    /* write a string to the child process */
    void write(const std::string&);

    /* read a full line from child process, 
       if no line is available, block until one becomes available */
    std::string readline();
    
    pid_t pid() const { return m_pid; };

private:
    /* yay */
    void exec();

    /* reads a line. we have input buffering for efficiency, 
     * so we have a subset of functions to deal with it. 
     * returns false if a line was not read, true if it was.
     * returns as an -addition- to into. also preserves newline. */
    bool readbufferedline(std::string& into);

    /* reads a chunk of data from stdin into our buffer. return 0 if EOF,
     * otherwise the number of chars read. */
    ssize_t readchunk();

    /* initializes the pipes for our process */
    bool pipecreate();

    void closeallpipes();

    /* gives us a pipe ref back in response to which pipe we want. this
     * was created because doing read(readpipe[1], ...) is too ambiguous
     * for my tastes. also 
     * close(readpipe[1]);
     * close(writepipe[0]);
     * ^ tell me what that does, at a high level [i.e. what pipes exactly are closed
     * in relation to the ones that remain open] without looking at how they were 
     * initialized.] */
    int& selectpipe(pipes::pipeno pipe);
    
    /* meh. */
    std::vector<const char*> m_args;
    /* buffer for process output */
    std::string m_outbuffer;
    /* added a third pipe for exec fail r/w. */
    int readpipe[3];    
    int writepipe[3];

    pid_t m_pid;
};

#endif // _PROCESS_H_
