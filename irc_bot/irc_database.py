import json

_database = {}
_dat_file = 'reg.dat'

def writeToDisc():
    global _database
    global _dat_file

    with open(_dat_file, 'w') as f:
        f.write(json.dumps(_database))

def readFromDisc():
    global _database
    global _dat_file

    try:
        with open(_dat_file, 'r') as f:
            instr = f.read()
    except IOError:
        # File does not exist. clear registry.
        _database = {}
    else:
        _database = json.loads(instr)

def write(key, val, force_write = True):
    global _database

    _database[key] = val

    if force_write:
        writeToDisc()

def read(key, default = None):
    global _database

    if key in _database:
        return _database[key]
    else:
        return default

def delete(key, force_write = True):
    global _database

    if key in _database:
        del _database[key]

        if force_write:
            writeToDisc()

# Initialization

readFromDisc()
