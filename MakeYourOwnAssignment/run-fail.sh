#!/bin/bash

# This is made to see that failure
# happens with 0 required user interaction
# and an exception is thrown (hence grep for what())

rm /tmp/pstest
rm makeres

killall -9 process-test 2>/dev/null

make -j5 > makeres

if [ $? -ne 0 ]; then
    echo "Make failed! See makeres"
    exit 1
fi

./process-test 2> /tmp/pstest 1>&2 & 

sleep 1

# if the process is still running
if [ ! -z "`pidof process-test`" ]; then
    kill -SIGKILL $!
    wait 2>/dev/null 1>&2 
    echo "process-test didn't terminate in 1s"
    exit 1
fi

# cleanup
wait 2>/dev/null 1>&2 

if [ -e /tmp/pstest ]; then
    # If what() exists
    if [ ! -z "`grep 'what()' /tmp/pstest`" ]; then
        echo "Success!"
    else
        echo "Fail! Exception not thrown"
        exit 1
    fi
else
    echo "/tmp/pstest not created"
    exit 1
fi

