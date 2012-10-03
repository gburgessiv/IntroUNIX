#!/usr/bin/python

import parser
import record
import protocol
import attribute
import sys
import os
import argparse

def _toFactory(*attrs, factoryType = None):
    """Converts the name and attributes to a factory.
Each attribute must be in the form (name, type[, default value]),
otherwise this will fail."""
    if attrs is None or len(attrs) == 0:
        raise ValueError("attrs must be len > 0 and not None")

    fact = record.RecordFactory()
    if factoryType is not None:
        fact.setFactoryType(factoryType)

    for i in attrs:
        assert len(i) in [2, 3]
        attr = attribute.Attribute()
        name = None
        if len(i) == 3:
            (name, attrType, attrDefault) = i
            attr.setType(attrType)
            attr.setValue(attrDefault)
        elif len(i) == 2:
            (name, attrType) = i
            attr.setType(attrType)
        if name is None:
            raise ValueError("Can't assign None name to attribute")
        fact.addAttribute(name, attr)
    
    return fact

def readRecords(filePath):
    facts = getFactories()
    assert facts is not None
    with open(filePath, 'r') as fi:
        txt = fi.read()

    if txt is not None and len(txt.rstrip().lstrip()) > 0:
        records = parser.parseTextBlock(txt, facts)
    else:
        return None

    return records['Record']

def commitRecords(filePath, records):
    if records is None:
        records = []
    else:
        records = [x for x in records if x is not None 
                                      and x[0] is not None
                                      and x[1] is not None]

    with open(filePath, 'w') as fi:
        for x in records:
            try:
                fi.write(x[0] + ": " + str(x[1]) + '\n')
            except Exception as e:
                print("Failed to write a record! :( (" + str(e) + ")")

def getFactories():
    "Returns all standard factories for records."
    # Part record
    try:
        cfact = _toFactory(("id", str), 
                           ("description", str), 
                           ("footprint", str), 
                           ("quantity", int))
    except e:
        sys.stderr.write(str(e) + "\n")
        return None
    return {"Part": cfact}

if __name__ == "__main__":
    aparser = argparse.ArgumentParser(description="Show available parts")
    aparser.add_argument('-f', '--file', metavar='file',
                        help="File to read from/write to")
    
    parsed = aparser.parse_args(sys.argv[1:])

    targFile = parsed.file

    if targFile is None or len(targFile) == 0:
        sys.stderr.write("Need to specify a file.\n")
        sys.exit(1)

    if not os.path.exists(targFile):
        sys.stderr.write("File must exist.\n")
        sys.exit(2)

    try:
        recs = readRecords(targFile)
    except Exception as e:
        sys.stderr.write("Error reading file. " + str(e) + "\n")
        sys.exit(3)

    keepGoing = True

    while keepGoing:
        instream = ""
        try:
            while not instream.endswith('\n\n\n'):
                instream += input().lstrip().rstrip() + '\n'
        except EOFError:
            keepGoing = False
        except Exception as e:
            sys.stderr.write(str(e))
            sys.exit(4)

        instream = instream.rstrip().lstrip()

        if len(instream) > 0:
            if recs is None:
                recs = []

            (res, strres) = protocol.interpretMessage(instream, getFactories(), recs)

            if res is False:
                sys.stderr.write("Operation failed!\n")
                if strres is not None:
                    sys.stderr.write(strres + "\n")
            else:
                if strres is not None:
                    print(strres)
                else:
                    print('OK')

    commitRecords(targFile, recs)
