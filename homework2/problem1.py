#
# George Burgess
# Problem 1 for Homework 2 - Intro/UNIX
# Parse /etc/passwd, output each user's name and default shell.
#

import string
import sys

def getPasswdContents():
    try:
        with open("/etc/passwd", "r") as f:
            return f.readlines()
    except:
        pass

def parsePasswd(lines):
    result = {}

    for line in lines:
        splitLine = line.split(':')

        # If it was a valid line...
        if len(splitLine) > 1:
            result[splitLine[0]] = splitLine[-1].rstrip()

    return result

if __name__ == "__main__":
    pc = getPasswdContents();

    if pc is None:
        print("Failed to open /etc/passwd");
        sys.exit(1);
    else:
        pwdict = parsePasswd(pc)

        if len(pwdict) > 0:
            print("Name\tShell")
            for i in pwdict:
                print(i + "\t" + pwdict[i]);
        else:
            print("Something went wrong parsing /etc/passwd")
