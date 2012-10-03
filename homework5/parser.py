#!/usr/bin/python

import re
import unittest

def getKvPairs(line):
    "Gets the key/value pairs back from a string. Returns as a dict."

    if line is None or len(line) == 0:
        return None

    reg = re.compile(r'\s*(?:(?P<name>\w+)\s*=\s*"(?P<value>[^"]+)"|(?P<tag>\w+)\s+(?=[^=]))\s*')
    fields = reg.findall(line)

    if fields is None or len(fields) == 0:
        return None

    result = []
    for (name, value, tag) in fields:
        if tag == '':
            result.append((name,value))
        else:
            result.append((tag,))
    
    return result

def processTotal(block):
    "Does an initial pass over block. Processes/sanitizes block data."
    return block.replace('\\\n', '')

def extractRecordName(block):
    "Gets the name of the element being declared."
    if block is None or len(block) == 0:
        return None

    reg = re.compile(r'\s*(\w+):')

    match = reg.match(block)

    if match is None:
        return None

    result = match.group(1)
    remain = None

    at = match.span()[1]

    if len(block) > at + 1:
        remain = block[at:]

    return (result, remain)

def isModifier(mod):
    return re.match(r'\s*\w+\s*=')

def processLine(line):
    recRes = extractRecordName(line)

    if recRes is None:
        return ('Modifier', line)
    
    return ('Record', (recRes[0], getKvPairs(recRes[1])))


def parseTextBlock(block, recordFactories, forMatch = False):
    if block is None or len(block) == 0 or recordFactories is None:
        return None
    
    block = processTotal(block)
    blocks = block.split('\n')
    blocks = map(lambda s: s.lstrip().rstrip(), blocks)
    blocks = filter(lambda x: len(x) > 0, blocks)

    result = {'Record': [], 'Modifier': []}
    
    for i in blocks:
        (type_, res) = processLine(i)
        if type_ == 'Record':
            (recName, recLine) = res
            if recName in recordFactories.keys():
                fact = recordFactories[recName]
                if forMatch:
                    res = fact.generateMatchRecord(recLine)
                else:
                    res = fact.generateRecord(recLine)
                res = (recName, res)
        if res is not None:
            result[type_].append(res)

    if len(result['Record']) == 0 and len(result['Modifier']) == 0:
        return None

    return result

class ParserTests(unittest.TestCase):
    def test_process(self):
        x = "hello\nworld\nwhat's\nup"
        self.assertEqual(processTotal(x), x)
        
        y = "hel\\\nlo\nworld\nwhat\\\n's\nup"
        self.assertEqual(processTotal(y), x)

    def test_recordName(self):
        self.assertIsNone(extractRecordName(None))
        self.assertIsNone(extractRecordName(""))
        self.assertIsNone(extractRecordName("hello"))
        self.assertIsNone(extractRecordName("he llo:"))
        self.assertIsNone(extractRecordName(":hello"))
        self.assertIsNone(extractRecordName(" : hello"))
        self.assertIsNone(extractRecordName("he!llo:"))

        res = extractRecordName("hello:")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "hello")
        self.assertIsNone(res[1])

        res = extractRecordName("hello: world")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "hello")
        self.assertIsNotNone(res[1])
        self.assertIn("world", res[1])

        res = extractRecordName("hello: world: how: are: you")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "hello")
        self.assertIsNotNone(res[1])
        self.assertIn("world: how: are: you", res[1])

    def test_kvPairs(self):
        self.assertIsNone(getKvPairs(None))
        self.assertIsNone(getKvPairs(""))
        self.assertIsNone(getKvPairs("notakey"))
        self.assertIsNone(getKvPairs("=notavalue"))
        self.assertIsNone(getKvPairs('="notavalue"'))
        self.assertIsNone(getKvPairs('hello=world'))

        kv = getKvPairs(r'hello="world"')
        self.assertIsNotNone(kv)
        self.assertEqual(len(kv), 1)
        self.assertEqual(len(kv[0]), 2)
        self.assertEqual(kv[0][0], "hello")
        self.assertEqual(kv[0][1], "world")

        kv = getKvPairs(r'hello="world" world="hello" whatup')
        self.assertIsNotNone(kv)
        self.assertEqual(len(kv), 2)
        self.assertEqual(len(kv[0]), 2)
        self.assertEqual(kv[0][0], "hello")
        self.assertEqual(kv[0][1], "world")
        self.assertEqual(len(kv[1]), 2)
        self.assertEqual(kv[1][0], "world")
        self.assertEqual(kv[1][1], "hello")

        kv = getKvPairs(r'hello="world" world="hello" whatup')
        self.assertIsNotNone(kv)
        self.assertEqual(len(kv), 2)
        self.assertEqual(len(kv[0]), 2)
        self.assertEqual(kv[0][0], "hello")
        self.assertEqual(kv[0][1], "world")
        self.assertEqual(len(kv[1]), 2)
        self.assertEqual(kv[1][0], "world")
        self.assertEqual(kv[1][1], "hello")

    def test_parseTextBlock(self):
        self.assertIsNone(parseTextBlock("", None))
        self.assertIsNone(parseTextBlock("str", None))
        self.assertIsNone(parseTextBlock(None, [record.RecordFactory()]))
        self.assertIsNone(parseTextBlock(None, None))

        for txt in ["", "    ", "\n\n    \n"]:
            parsed = parseTextBlock(txt, [record.RecordFactory()]) 
            self.assertIsNone(parsed)

        allTests = [("hello\n    \t\t\t    \nworld!", ["hello", "world!"], [])]

        for (txt, modres, recres) in allTests:
            parsed = parseTextBlock(txt, record.RecordFactory()) 
            self.assertIsNotNone(parsed)
            self.assertIn("Modifier", parsed.keys())
            self.assertIn("Record", parsed.keys())
            self.assertEqual(len(parsed["Modifier"]), len(modres))
            self.assertEqual(len(parsed["Record"]), len(recres))
            for i in modres:
                self.assertIn(i, parsed["Modifier"])
            for i in recres:
                self.assertIn(i, parsed["Record"])

if __name__ == '__main__':
    import record
    unittest.main()
