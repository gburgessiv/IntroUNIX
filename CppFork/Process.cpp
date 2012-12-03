#include "Process.h"

#include <stdexcept>
#include <memory>
#include <algorithm>
#include <iostream>

#include <assert.h>
#include <unistd.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <sys/select.h>
#include <signal.h>

unsigned int Process::m_runningProcesses = 0;

///
/// Utility functions
///
static std::vector<const char*> strListToChars(const std::vector<std::string>& str)
{
    std::vector<const char*> result;

    std::transform(str.begin(), 
                   str.end(), 
                   std::back_inserter(result), 
                   [] (const std::string st) { 
                       return st.c_str();
                   });

    return result;
}

static void raiseError(const std::string& err, int num = errno)
{
    char* errbuf = nullptr;
    char fullbuf[256];

    errbuf = strerror(num);

    snprintf(fullbuf, 256, "%s: %s (%d)", err.c_str(), errbuf, num);

    throw std::runtime_error(fullbuf);
}

static void pipeClose(int& p)
{
    if (p >= 0)
    {
        close(p);
        p = -1;
    }
}

static bool createpipepair(int arr[])
{
    constexpr decltype(O_CLOEXEC) CREATE_FLAGS = 0;

    if (pipe2(arr, CREATE_FLAGS) == -1)
    {
        return false;
    }

    return true;
}

/* reads an fd nonblocking. restores state to blocking/nonblocking
 * afterward */
bool quickread(int fd, char* buf, size_t bufsize)
{
    if (buf == nullptr)
    {
        throw std::runtime_error("Invalid buffer sent to quickread");
    }

    // Saving old state, setting nonblocking ops
    auto old = fcntl(fd, F_GETFL);
    bool result = true;
    fcntl(fd, F_SETFL, old | O_NONBLOCK);

    if (read(fd, buf, bufsize) == -1)
    {
        // EAGAIN and EWOULDBLOCK are synonymous for sockets
        // otherwise, EAGAIN will be given for any pipe/etc
        if (errno == EAGAIN || errno == EWOULDBLOCK)
        {
            errno = 0;
            result = false;
        }
        else
        {
            raiseError("Read error from quickread");
        }
    }

    // Ensuring old flags are reset
    fcntl(fd, F_SETFL, old);

    return result;
}

///
/// Signal handler functions
///
namespace sighandlers
{
    // in retrospect, this probably could have been better implemented as a singleton. but at the same time, maybe not.
    // meh. it works.

    int errpipes[2] = {-1, -1};
    int execerror = 0;

    static int& errorReadPipe()
    {
        return errpipes[0];
    }
    
    static int& errorWritePipe()
    {
        return errpipes[1];
    }

    static bool execFailed()
    {
        return execerror != 0;
    }

    static int execErrno()
    {
        return execerror;
    }

    static void destroy()
    {
        pipeClose(errpipes[0]);
        pipeClose(errpipes[1]);
    }

    void sigchldHandler(int)
    {
        if (errorReadPipe() == -1)
        {
            return;
        }

        if (read(errorReadPipe(), &execerror, sizeof(execerror)) == -1)
        {
            // if there was no message
            if (errno == EAGAIN)
            {
                execerror = 0;
            }
        }
    }

    void init()
    {
        execerror = 0;
        pipeClose(errpipes[0]);
        pipeClose(errpipes[1]);

        if (pipe(errpipes) == -1)
        {
            raiseError("Failed to init pipes for sig handler");
        }

        // set the read pipe to nonblocking communications
        if (fcntl(errorReadPipe(), F_SETFL, fcntl(errorReadPipe(), F_GETFL) | O_NONBLOCK) == -1)
        {
            raiseError("Couldn't set pipes to nonblocking");
        }

        struct sigaction sa;

        sa.sa_handler = &sigchldHandler;

        if (sigaction(SIGCHLD, &sa, nullptr) == -1)
        {
            raiseError("Failed to set sig handler");
        }

        if (signal(SIGPIPE, SIG_IGN) == SIG_ERR)
        {
            raiseError("Failed to set SIGPIPE");
        }
    }
}


///
/// Class functions
///
Process::Process(const std::vector<std::string> &args):
    m_args(strListToChars(args)),
    readpipe {-1, -1},
    writepipe {-1, -1},
    m_pid(0)
{
    // if the sighandlers have been disposed of/not initialized yet...
    if (m_runningProcesses == 0)
    {
        sighandlers::init();
    }

    ++m_runningProcesses;

    exec();

    if (sighandlers::execFailed())
    {
        raiseError("Exec failed", sighandlers::execErrno());
    }
}

Process::~Process()
{
    closeallpipes();

    // If we have a child, guarantee that it is waited on/cleaned up...
    if (m_pid != 0)
    {
        int status;
        waitpid(m_pid, &status, 0);
    }

    if (--m_runningProcesses == 0)
    {
        sighandlers::destroy();
    }
}

void Process::write(const std::string& s)
{
    ssize_t amt = 0;

    assert(selectpipe(pipes::WRITE_PIPE) != -1);

    amt = ::write(selectpipe(pipes::WRITE_PIPE), s.c_str(), s.size());

    // If we failed to write
    if (!(amt > 0 || (amt == 0 && s.empty())))
    {
        raiseError("Failed to write");
    }
}
std::string Process::readline() {
    std::string result;

    while (!readbufferedline(result))
    {
        ssize_t size = readchunk();

        if (size == 0)
        {
            break;
        }
    }

    return result;
}

bool Process::readbufferedline(std::string& into)
{
    if (m_outbuffer.empty())
    {
        return false;
    }

    int at = m_outbuffer.find('\n');

    if (at == -1)
    {
        into += std::move(m_outbuffer);

        return false;
    }
    else
    {
        // include newline in result
        at += 1;
        into += m_outbuffer.substr(0, at);
        m_outbuffer.erase(0, at);
    }

    return true;
}

ssize_t Process::readchunk()
{
    char buf[255];
    ssize_t result = 0;

    assert(selectpipe(pipes::READ_PIPE) != -1);

    result = read(selectpipe(pipes::READ_PIPE), buf, sizeof(char) * 255);

    if (result == -1)
    {
        raiseError("Failed to read");
    }

    m_outbuffer.append(buf, result);

    return result;
}

bool Process::pipecreate()
{
    constexpr int READ = 0;
    constexpr int WRITE = 1;

    int pipebuf[2];

    if (!createpipepair(pipebuf))
    {
        return false;
    }

    selectpipe(pipes::READ_PIPE) = pipebuf[READ];
    selectpipe(pipes::SUB_WRITE_PIPE) = pipebuf[WRITE];

    if (!createpipepair(pipebuf))
    {
        return false;
    }

    selectpipe(pipes::SUB_READ_PIPE) = pipebuf[READ];
    selectpipe(pipes::WRITE_PIPE) = pipebuf[WRITE];

    return true;
}

int& Process::selectpipe(pipes::pipeno pipe)
{
    switch(pipe)
    {
    case pipes::READ_PIPE: return readpipe[0];
    case pipes::WRITE_PIPE: return writepipe[0];
    case pipes::SUB_READ_PIPE: return readpipe[1];
    case pipes::SUB_WRITE_PIPE: return writepipe[1];
    }

    assert(false);
}

void Process::exec()
{
    if (m_args.empty())
    {
        throw std::runtime_error("Need at least one argument for the filename");
    }

    if (!pipecreate())
    {
        raiseError("Failed to create pipes");
    }

    auto forkres = fork();

    switch(forkres)
    {
    case -1:
        closeallpipes();

        raiseError("Forking went poorly");
        // intentional no break -- exception takes care of it
    case 0:
    {
        pipeClose(selectpipe(pipes::READ_PIPE));
        pipeClose(selectpipe(pipes::WRITE_PIPE));
        pipeClose(sighandlers::errorReadPipe());

        assert(selectpipe(pipes::SUB_READ_PIPE) != -1);
        assert(selectpipe(pipes::SUB_WRITE_PIPE) != -1);

        if (dup2(selectpipe(pipes::SUB_READ_PIPE), fileno(stdin)) == -1)
        {
            raiseError("Duplicating read pipe went poorly.");
        }

        if (dup2(selectpipe(pipes::SUB_WRITE_PIPE), fileno(stdout)) == -1)
        {
            raiseError("Duplicating write pipe went poorly");
        }

        const char* filename = m_args[0];

        char** args = const_cast<char**>((m_args.size() > 1) ? &m_args[1] : nullptr);

        char okc = (char)0;

        // tell other program we've started. if that fails then go directly to saying "failed"
        if (::write(fileno(stdout), &okc, sizeof(char)) != -1)
        {
            execvp(filename, args);
        }

        // if exec fails, report error, close file descriptors, and get out.
        if (sighandlers::errorWritePipe() >= 0)
        {
            ::write(sighandlers::errorWritePipe(), &errno, sizeof(decltype(errno)));
        }

        _exit(1);
    }
    default:
    {
        m_pid = forkres;

        pipeClose(selectpipe(pipes::SUB_READ_PIPE));
        pipeClose(selectpipe(pipes::SUB_WRITE_PIPE));

        assert(selectpipe(pipes::READ_PIPE) != -1);
        assert(selectpipe(pipes::WRITE_PIPE) != -1);

        // wait for the program to output (char)0, which means it is running.
        // then wait 50ms for the program to fail/pass exec(). 
        char inbuf = '\0';
        struct timeval maxtime;
        fd_set rdfds;

        FD_ZERO(&rdfds);
        FD_SET(selectpipe(pipes::READ_PIPE), &rdfds);

        maxtime.tv_sec = 1;
        if (select(selectpipe(pipes::READ_PIPE) + 1, &rdfds, nullptr, nullptr, &maxtime) == -1)
        {
            raiseError("Select failed in waiting for new process to spawn");
        }

        // clearing out initial byte
        ::read(selectpipe(pipes::READ_PIPE), &inbuf, sizeof(char));
        
        // wait a max of 50ms for program to report failure
        usleep(50 * 1000);
    }
    }
}

void Process::closeallpipes()
{
    for (int i = 0; i < 2; ++i)
    {
        pipeClose(readpipe[i]);
        pipeClose(writepipe[i]);
    }
}

