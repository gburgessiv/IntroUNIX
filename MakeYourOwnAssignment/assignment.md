This assignment is to create a script (shell script, Python script, whatever you wish to use) to automate:
    - The compilation of a program (If applicable)
    - The running of a program 
    - The effects of a program (its output, its side-effects, etc)

If the target program is interactive (you need to give it input), you may have the script feed it test values for extra credit.

The target program must be a program you have written (preferrably for this class).

Upon something failing (compilation, program running, side-effects/output not being what was expected), your test program should fail and say what went wrong (to a resonable extent).

Your test program should need minimal input/arguments; the goal is not to write a flexible masterpiece. Rather, the goal is to hack something together that will get the job done. (Note: This is not saying to make something ugly/unreadable. It is saying that this script will likely be used for a narrow set of cases. Tailor it to those.) 

The program being tested must be relatively complex, and require a fair amount of effort to build/run. The following test program will not receive a high mark:

#!/bin/bash

if [[ "Hello, World!" == "`python helloworld.py`" ]]; then
    echo "Success!"
else
    echo "Failed!"
    exit 1
fi

Programs will be graded on
    - All potential failures (i.e. build fail, running fail, etc.) are accounted for (10pts)
    - Each failure has an accompanying error message (5pts)
    - Most external effects of the program are checked for correct operation (10pts)
    - Each reasonable success condition has an accompanying success message (2pts bonus)
    - Code is readable, but style is not overdone (5pts)
