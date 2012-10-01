#!/usr/bin/python

import attribute
import copy
import parser
import record

requests = {}

def addRequest(reqName, method):
    if reqName is None or method is None or not callable(method):
        raise ValueError("reqName can't be none, method must be callable")
    global requests
    requests[reqName.lower()] = method

def _toRecords(recStr, factories, isMatch = False):
    if recStr is None:
        return None
    x = parser.parseTextBlock(recStr, factories, isMatch)

    if x is None or not "Record" in x:
        return None

    return x["Record"]

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
    listed = _findEntries(match, factories, records, True)

    if listed is None or len(listed) == 0:
        return (True, None)

    result = ""
    for k, r in listed:
        result += "{0}: {1}\n".format(k, str(r))

    return (True, result)

def _addEntries(entry, factories, records):
    "Default add entries method"
    try:
        recs = _toRecords(entry, factories)
    except:
        return (False, "One or more records had invalid data. Aborting.")

    if recs is None:
        return (False, None)

    validRecs = [(k, i) for (k, i) in recs if i.isValid()]

    if len(validRecs) != len(recs):
        print("WARNING: " + str(recs - validRecs) + " records were incomplete")
    records += validRecs
    return (True, None)

def _delEntries(entry, factories, records):
    "Default delete entries method"
    match = _toRecords(entry, factories, True)
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
    match = _toRecords(entry, factories, True)
    
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
                try:
                    i.setAttribute(k, v.asNatural())
                except Exception as e:
                    if len(msg) > 0:
                        msg += '\n'
                    msg += "Failed to update field {0} to {1}.".format(
                             k, str(v.asNatural()))

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
