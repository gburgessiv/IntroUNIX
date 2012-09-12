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
    parser = argparse.ArgumentParser(description = 'Multiply sets of 2 floats taken '
                                     'from stdin; puts result to stdout.')

    parser.add_argument('--ignore-blank', action='store_true', default=False)
    parser.add_argument('--ignore-non-numeric', action='store_true', default=False)
    parser.add_argument('files', nargs='*')
    args = parser.parse_args(sys.argv[1:])

    if args.files is None or len(args.files) == 0:
        success = multLoop(sys.stdin, args.ignore_blank, args.ignore_non_numeric)
    else:
        for i in args.files:
            with open(i, 'r') as f:
                success = multLoop(f, args.ignore_blank, args.ignore_non_numeric)
            if not success:
                break

    sys.exit(0 if success else 1)

