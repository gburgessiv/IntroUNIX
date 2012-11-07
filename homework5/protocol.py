#!/usr/bin/python

import attribute
import copy
import parser
import re
import record

requests = {}

def addRequest(reqName, method):
    if reqName is None or method is None or not callable(method):
        raise ValueError("reqName can't be none, method must be callable")
    global requests
    requests[reqName.lower()] = method

def _toRecords(recStr, factories, isMatch = False, justRecords = True):
    if recStr is None:
        return None
    x = parser.parseTextBlock(recStr, factories, isMatch)

    if x is None:
        return None

    if justRecords:
        if not "Record" in x:
            return None

        return x["Record"]

    return x

def _findEntries(match, factories, records, defaultAll = False):
    matchRecs = _toRecords(match, factories, True)

    result = []

    if matchRecs is None or len(matchRecs) == 0:
        if defaultAll:
            return records
        else:
            return None

    for i in records:
        for x in matchRecs:
            if i.meetsCriteria(x):
                result.append(i)

    return result

def _listEntries(match, factories, records):
    try:
        listed = _findEntries(match, factories, records, defaultAll = True)
    except Exception as e:
        return (False, str(e))

    if listed is None or len(listed) == 0:
        return (True, None)

    allList = parser.parseTextBlock(match, factories, False)
    
    # Sorting
    if allList is not None and 'Modifier' in allList and len(allList['Modifier']) > 0:
        modifiers = allList['Modifier']
        fields = None
        for i in modifiers:
            sortresult = re.match(r'\s*sort\s+(?P<Type>\w+)\s+by\s+(?P<Fields>.*)', i)
            if sortresult is None:
                return (False, "Could not interpret modifier '" + i + "'")
            else:
                results = sortresult.groups()
                if results[0] not in factories:
                    return (False, results[0] + ' is not a valid record')

                unsorted_records = [i[1] for i in listed if i[0] == results[0]]
                listed = [x for x in listed if x[0] != results[0]]

                if len(unsorted_records) == 0:
                    continue

                sortby = []
                
                for a in results[1].split(','):
                    a = a.lstrip().rstrip()
                    if not unsorted_records[0].hasAttribute(a):
                        return (False, 'asking to sort by invalid attribute ' + a + ' from ' + results[0])
                    sortby.append(a)
                
                # Now sort from least to most important (most important first)
                while len(sortby) > 0:
                    x = sortby.pop()
                    unsorted_records = sorted(unsorted_records, key = lambda z: z.getAttribute(x))

                listed += [(results[0], x) for x in unsorted_records]

    # Making string of [potentially sorted] keys...
    result = ""
    for k, r in listed:
        result += "{0}: {1}\n".format(k, str(r))

    return (True, result)

def _addEntries(entry, factories, records):
    "Default add entries method"
    try:
        recs = _toRecords(entry, factories)
    except:
        return (False, "One or more records had invalid data.")

    validRecs = [(k, i) for (k, i) in recs if i.isValid()]

    if len(validRecs) != len(recs):
        print("WARNING: " + str(recs - validRecs) + " records were incomplete")

    if records is None:
        records = []

    records += validRecs
    return (True, None)

def _delEntries(entry, factories, records):
    "Default delete entries method"
    try:
        match = _toRecords(entry, factories, True)
    except Exception as e:
        return (False, str(e))
    if match is None:
        return (False, None)
    
    idx = 0
    # Can't iterate through a list while modifying it, so we make a shallow
    # copy of it and then iterate through the copy.
    trecs = copy.copy(records)
    for (k, i) in trecs:
        # Getting matches with the same type as the current record.
        pertinent = [z for (k0, z) in match if k0 == k]
        for m in pertinent:
            if i.meetsCriteria(m):
                del records[idx]
                idx -= 1
                break
        idx += 1

    return (True, None)

def _updateEntries(entry, factories, records):
    updatesFailed = False
    try:
        match = _toRecords(entry, factories, True)
    except Exception as e:
        return (False, str(e))
    
    if match is None:
        return (False, "Couldn't find match records")

    msg = ""

    # Pairing everything up into match-set pairs
    paired = []
    for i in range(0, len(match), 2):
        if len(match) > i+1:
            if match[i][0] != match[i+1][0]:
                return (False, "Can't update one record to another.")
            paired.append((match[i], match[i+1]))
        else:
            msg = "Discarded matcher for update."

    if len(paired) == 0:
        return (False, None)
    
    for (mt,st) in paired:
        m = mt[1]
        s = st[1]
        mset = [z[1] for z in records if z[1].meetsCriteria(m)]
        for i in mset:
            for (k,v) in [z for z in s.attributes.items() if not z[1].isNull()]:
                linemsg = ""
                try:
                    i.setAttribute(k, v.asNatural())
                    linemsg = "Update of field {0} to {1} succeeded".format(
                            k, str(v.asNatural()))
                except Exception as e:
                    updatesFailed = True
                    linemsg = "Failed to update field {0} to {1}.".format(
                             k, str(v.asNatural()))
                if len(linemsg) > 0:
                    if len(msg) > 0:
                        msg += '\n'
                    msg += linemsg

    if not updatesFailed:
        msg = ""

    return (True, msg if len(msg) > 0 else None)
    
def reportError(message, moreInfo = None):
    if moreInfo is None:
        moreInfo = ""
    elif not moreInfo.endswith('\n'):
        moreInfo += '\n'
    return "error\n" + moreInfo + (message if message is not None 
                                   else "(No Message recieved)")

def interpretMessage(message, factories, records):
    global requests
    
    newline = message.find('\n')
    act = None
    if newline == -1:
        act = message
        rmessage = None
    else:
        act = message[:newline]
        rmessage = message[newline:]

    act = act.lstrip().rstrip().lower()

    if act not in requests.keys():
        return (False, reportError(message))

    return requests[act](rmessage, factories, records)

addRequest('add', _addEntries)
addRequest('append', _addEntries)
addRequest('remove', _delEntries)
addRequest('rm', _delEntries)
addRequest('del', _delEntries)
addRequest('update', _updateEntries)
addRequest('set', _updateEntries)
addRequest('list', _listEntries)
addRequest('show', _listEntries)
