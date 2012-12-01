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

static bool createsockpair(int arr[])
{
    constexpr decltype(O_CLOEXEC) CREATE_FLAGS = 0;

    if (pipe2(arr, CREATE_FLAGS) == -1)
    {
        return false;
    }

    return true;
}

///
/// Class functions
///
/* Initialize the process, create input/output pipes 
 * --> Creating IO is deferred to exec because yes.
 */
Process::Process(const std::vector<std::string> &args):
    m_args(strListToChars(args)),
    readpipe {-1, -1},
    writepipe {-1, -1},
    m_pid(0)
{
    exec();
}

/* Close any open file streams or file descriptors,
   ensure that the child has terminated */
Process::~Process()
{
    closeallpipes();

    // If we have a child, guarantee that it is waited on/cleaned up...
    if (m_pid != 0)
    {
        int status;
        waitpid(m_pid, &status, 0);
    }
}

/* write a string to the child process */
void Process::write(const std::string& s)
{
    ssize_t amt = 0;

    assert(selectpipe(pipes::WRITE_PIPE) != -1);
    amt = ::write(selectpipe(pipes::WRITE_PIPE), s.c_str(), s.size());

    // If we failed to write
    if(!(amt > 0 || (amt == 0 && s.empty())))
    {
        raiseError("Failed to write");
    }
}

/* read a full line from child process, 
   if no line is available, block until one becomes available */
std::string Process::readline()
{
    std::string result;

    while(!readbufferedline(result))
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

    

    if (result != 0)
    {
        m_outbuffer += std::string(buf, result);
    }

    return result;
}

// #define SAY_FD(n, t) std::cout << "FD " << n << " CREATED AS " #t << std::endl
#define SAY_FD(n, t)

bool Process::pipecreate()
{
    constexpr int READ = 0;
    constexpr int WRITE = 1;

    int pipebuf[2];

    if (!createsockpair(pipebuf))
    {
        return false;
    }

    selectpipe(pipes::READ_PIPE) = pipebuf[READ];
    selectpipe(pipes::SUB_WRITE_PIPE) = pipebuf[WRITE];

    if (!createsockpair(pipebuf))
    {
        return false;
    }

    selectpipe(pipes::SUB_READ_PIPE) = pipebuf[READ];
    selectpipe(pipes::WRITE_PIPE) = pipebuf[WRITE];

    if (!createsockpair(pipebuf))
    {
        return false;
    }
    
    selectpipe(pipes::ERR_READ_PIPE) = pipebuf[READ];
    selectpipe(pipes::ERR_WRITE_PIPE) = pipebuf[WRITE];

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
    case pipes::ERR_READ_PIPE: return readpipe[2];
    case pipes::ERR_WRITE_PIPE: return writepipe[2];
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
        pipeClose(selectpipe(pipes::ERR_READ_PIPE));

        assert(selectpipe(pipes::SUB_READ_PIPE) != -1);
        assert(selectpipe(pipes::SUB_WRITE_PIPE) != -1);
        assert(selectpipe(pipes::ERR_WRITE_PIPE) != -1);

        if (dup2(selectpipe(pipes::SUB_READ_PIPE), fileno(stdin)) == -1)
        {
            raiseError("Duplicating read pipe went poorly.");
        }

        if (dup2(selectpipe(pipes::SUB_WRITE_PIPE), fileno(stdout)) == -1)
        {
            raiseError("Duplicating write pipe went poorly");
        }

        const char* filename = m_args[0];

        // i hate const_cast. :(
        char** args = const_cast<char**>((m_args.size() > 1) ? &m_args[1] : nullptr);

        execvp(filename, args);

        //
        // if exec fails, report error, close file descriptors, and get out.
        //

        // nonblocking because yes.
        fcntl(selectpipe(pipes::ERR_WRITE_PIPE), F_SETFL, O_NONBLOCK);

        ::write(selectpipe(pipes::ERR_WRITE_PIPE), &errno, sizeof(decltype(errno)));

        _exit(0);
        // _exit means we don't need to break
    }
    default:
        m_pid = forkres;

        pipeClose(selectpipe(pipes::SUB_READ_PIPE));
        pipeClose(selectpipe(pipes::SUB_WRITE_PIPE));
        pipeClose(selectpipe(pipes::ERR_WRITE_PIPE));

        assert(selectpipe(pipes::READ_PIPE) != -1);
        assert(selectpipe(pipes::WRITE_PIPE) != -1);
        assert(selectpipe(pipes::ERR_READ_PIPE) != -1);
    }
}

void Process::closeallpipes()
{
    for (int i = 0; i < 3; ++i)
    {
        pipeClose(readpipe[i]);
        pipeClose(writepipe[i]);
    }
}

