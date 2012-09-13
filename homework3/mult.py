#!/usr/bin/python

import argparse
import string
import sys

def multLoop(handle, ignoreBlanks = False, ignoreInvalid = False):
    accum = None

    for line in handle:
        if line.endswith("\n"):
            line = line[:-1]
        if len(line) == 0:
            if not ignoreBlanks:
                if accum is not None:
                    print(str(accum))
                    accum = None
                else:
                    print("No values entered!")
            continue

        cur = None
        try:
            cur = float(line)
        except ValueError:
            if not ignoreInvalid:
                sys.stderr.write("Could not convert " + line + " to float.\n")
                return False
            continue

        # Keep this an int as long as possible
        if int(cur) == cur:
            cur = int(cur)

        if accum is None:
            accum = cur
        else:
            accum *= cur

    if accum is not None:
        print(str(accum))
    else:
        print("No values entered!")
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Multiply sets of floats taken '
                                     'from stdin; puts result to stdout.')

    parser.parse_args(sys.argv[1:])

    success = multLoop(sys.stdin)

    sys.exit(0 if success else 1)

