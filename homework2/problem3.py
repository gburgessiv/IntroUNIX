# ECE 2524 Homework 2 Problem 3 George Burgess

import re
import sys
import string

# Yay regexes! :)
MATCH_STR = r"\A(?P<fname>\w+)\s*(?P<lname>\w+)\s*(?P<money>\d+\.\d{2})\s*(?P<city>\w+)\s*(?P<phone>\d{3}-\d{4})\s*\Z"
MATCH_REGEX = re.compile(MATCH_STR)

def includeResident(field):
    return True

def getStatistics(residents):
    if residents is None or len(residents) == 0:
        return None

    total = 0.0
    maximum = float("-inf") 
    minimum = float("inf")
    maxName = None
    minName = None

    for r in residents:
        if "money" in r:
            money = float(r["money"])
            total += money
            
            if money > maximum:
                maxName = r["lname"]
                maximum = money

            # Special case: no elif because if there's only one resident
            # then the maximum will be the only one set.
            if money < minimum:
                minName = r["lname"]
                minimum = money
        else:
            raise RuntimeError("Expected money to be in r")

    return {"total": total, 
            "average": total / len(residents), 
            "max": (maximum, maxName), 
            "min": (minimum, minName)}

def printStats(stats):
    print("ACCOUNT SUMMARY")
    print("Total amount owed = %2.2f" % stats["total"])
    print("Average amount owed = %2.2f" % stats["average"])
    print("Maximum amount owed = %2.2f by %s" % (stats["max"][0], stats["max"][1]))
    print("Minimum amount owed = %2.2f by %s" % (stats["min"][0], stats["min"][1]))

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
    

    if len(db) == 0:
        print("No parsable entries. :(")
        sys.exit(3)

    stats = getStatistics(db)

    assert stats is not None

    printStats(stats)
