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
    if(buf == nullptr)
    {
        throw std::runtime_error("Invalid buffer sent to quickread");
    }

    // Saving old state, setting nonblocking ops
    auto old = fcntl(fd, F_GETFL);
    bool result = true;
    fcntl(fd, F_SETFL, old | O_NONBLOCK);

    if(read(fd, buf, bufsize) == -1)
    {
        // EAGAIN and EWOULDBLOCK are synonymous for sockets
        // otherwise, EAGAIN will be given for any pipe/etc
        if(errno == EAGAIN || errno == EWOULDBLOCK)
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
/// Class functions
///
Process::Process(const std::vector<std::string> &args):
    m_args(strListToChars(args)),
    readpipe {-1, -1},
    writepipe {-1, -1},
    m_pid(0)
{
    exec();
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
}

void Process::write(const std::string& s)
{
    ssize_t amt = 0;

    assert(selectpipe(pipes::WRITE_PIPE) != -1);

    amt = ::write(selectpipe(pipes::WRITE_PIPE), s.c_str(), s.size());

    // If we failed to write
    if(!(amt > 0 || (amt == 0 && s.empty())))
    {
        int buf;

        // If the subprocess left us a message on ERR_READ_PIPE, then exec
        // failed. Report that instead of generic write error.
        if(quickread(selectpipe(pipes::ERR_READ_PIPE), (char*)&buf, sizeof(buf)))
        {
            raiseError("Subprocess exec fail", buf);
        }
        raiseError("Failed to write");
    }
}

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
    fd_set readfds;

    assert(selectpipe(pipes::READ_PIPE) != -1);

    FD_ZERO(&readfds);
    FD_SET(selectpipe(pipes::READ_PIPE), &readfds);
    FD_SET(selectpipe(pipes::ERR_READ_PIPE), &readfds);

    int maxfd = std::max(selectpipe(pipes::READ_PIPE), 
                         selectpipe(pipes::ERR_READ_PIPE));


    auto sresult = select(maxfd + 1, &readfds, nullptr, nullptr, nullptr);

    // no timeout == it can't be 0. just verifying though!
    assert(sresult != 0);

    if(sresult == -1)
    {
        raiseError("Select call failed");
    }

    // if ERR_READ_PIPE is ready to be read from, then exec failed.
    if(FD_ISSET(selectpipe(pipes::ERR_READ_PIPE), &readfds))
    {
        int ebuf;

        // we only pass an int for errno
        sresult = read(selectpipe(pipes::ERR_READ_PIPE), &ebuf, sizeof(decltype(errno)));
        raiseError("Process failed to exec", ebuf);
    }

    // otherwise READ_PIPE must be ready. if not, we'll block anyway.
    result = read(selectpipe(pipes::READ_PIPE), buf, sizeof(char) * 255);

    if(result == -1)
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

    if (!createpipepair(pipebuf))
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

        _exit(1);
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

