#!/bin/bash

# test to see if cppfork returns success.
# assumes a process is created, so just checks for file
# descriptors, etc.

function cleanup {
    kill -SIGKILL $! 2>/dev/null
    wait 2> /dev/null
    exit $1
}

killall -9 process-test 2>/dev/null

rm makeres

make -j5 > makeres

if [ $? -ne 0 ]; then
    echo "Make failed! check makeres"
    exit 1
fi

echo "1 2 3 4 5" | ./process-test 2>/dev/null 1>&2 & 

sleep 1

# if the process exited
if [ -z "`pidof process-test`" ]; then
    echo "Process exited prematurely"
    cleanup 1
fi

nfd=`ls /proc/${!}/fd | wc --words` 

if [ $nfd -ne 3 ]; then
    echo "$nfd file descriptors open. should be 3."
    cleanup 1
fi

echo "Success!"
cleanup 0
