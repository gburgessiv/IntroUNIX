# ECE 2524 Homework 2 Problem 2 George Burgess

import re
import sys
import string

# Yay regexes! :)
MATCH_STR = r"\A(?P<fname>\w+)\s*(?P<lname>\w+)\s*(?P<money>\d+\.\d{2})\s*(?P<city>\w+)\s*(?P<phone>\d{3}-\d{4})\s*\Z"
MATCH_REGEX = re.compile(MATCH_STR)

def printInfo(field):
    printStrs = [field["phone"], field["lname"], field["fname"], field["money"]]
    print(str.join(", ", printStrs))

def includeResident(field):
    if field is not None and "city" in field:
        return field["city"].lower() == "blacksburg"
    return False

def getFields(line):
    global MATCH_REGEX

    result = MATCH_REGEX.match(line)

    if result is not None:
        return result.groupdict()
    else:
        return None

def getFileInfo(fileName):
    try:
        with open(fileName, "r") as f:
            return f.readlines()
    except:
        return None

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Need to input target file!")
        sys.exit(1)

    info = getFileInfo(sys.argv[1])

    if info is None:
        print("Error in retrieving file data.")
        sys.exit(2)

    db = []

    for i in info:
        dict_ = getFields(i.rstrip())

        if dict_ is not None:
            if includeResident(dict_):
                db.append(dict_)
        else:
            print("The following line seems to be malformed: \"" + i + "\"")
    
    if len(db) > 0:
        print("ACCOUNT INFORMATION FOR BLACKSBURG RESIDENTS")
        for i in db:
            printInfo(i)
    else:
        print("Seems like there are no parsable entries for Blacksburg...")
