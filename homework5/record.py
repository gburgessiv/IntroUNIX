#!/usr/bin/python

import attribute
import copy
import parser
import unittest

class Record:
    def __init__(self, attrs):
        if attrs is None or len(attrs) == 0:
            raise ValueError("Can't create a Record with no attributes")
        self.attributes = copy.deepcopy(attrs)

    def __contains__(self, obj):
        if type(obj) is Attribute:
            for i in self.attributes:
                if i == obj:
                    return True
            return False

        if type(obj) is str:
            if obj in self.attributes:
                return True
        return False

    def __eq__(self, other):
        if type(self) is not type(other):
            raise ValueError("Can't compare Record to " + str(type(other)))

        if len(self.attributes) != len(other.attributes):
            return False

        for i in self.attributes:
            if i not in other:
                return False
        return True

    def __str__(self):
        if not self.isValid():
            raise ValueError("Invalid string conversion!")

        result = ""
        for (k,v) in self.attributes.items():
            if not v.isNull():
                result += ' {0}="{1}"'.format(k,v.asStr())
        return result

    def _parseString():
        pass

    def isValid(self):
        for i in self.attributes.values():
            if i.required and i.isNull():
                return False
        return True

    def getAttribute(self, attrStr):
        at = self.getRawAttribute(attrStr)
        return None if at is None else at.asNatural()

    def getRawAttribute(self, attrStr):
        if attrStr is None or attrStr not in self.attributes:
            return None
        return self.attributes[attrStr]

    def setAttribute(self, attrStr, value):
        at = self.getRawAttribute(attrStr)
        if at is None:
            return False
        try:
            return at.setValue(value)
        except:
            return False

    def setRawAttribute(self, attrStr, attr):
        "Sets an attribute's value"
        if attrStr is None or attr is None or attrStr not in self.attributes:
            return False
        if type(attr) is not attribute.Attribute:
            raise ValueError("Can't set attribute to non-attribute")
        self.attributes[attrStr] = attr
        return True

    def meetsCriteria(self, criteria):
        "Returns whether the given statement meets the given criteria."

        if criteria is None or criteria.attributes is None:
            return False

        # We do want criteria.attributes == [] to fall through and return True.
        for k, v in criteria.attributes.items():
            if not v.isNull():
                attr = self.getRawAttribute(k)
                if attr is None or attr.isNull() or not attr.matchesCriteria(v.asNatural()):
                    return False
                    
        return True

class RecordFactory:
    def __init__(self):
        self.attrs = {}
        self.matchAttrs = {}
        self.recType = Record

    def setFactoryType(self, recordType):
        if recordType is None:
            raise ValueError("recordType can't be None")
        self.recType = recordType

    def addAttribute(self, attrName, attr):
        if attrName is None or attr is None:
            return False

        self.attrs[attrName] = attr
        mattr = copy.deepcopy(attr)
        mattr.setType(str)
        self.matchAttrs[attrName] = mattr

        return True

    def _generateRecord(self, attrs, fromKv):
        result = self.recType(attrs)

        if fromKv is None:
            return result

        for i in fromKv:
            if len(i) == 1:
                result._parseString(i[0])
                continue
            assert len(i) == 2
            (key, value) = i
            if not result.setAttribute(key, value):
                errstr = ( "Invalid key or value for record ({0} ;; {1}). Available "
                         + "keys are ").format(key, value)
                for i in self.attrs:
                    errstr += i + " "
                raise ValueError(errstr)
        return result
            
    def generateRecord(self, fromKv):
        return self._generateRecord(self.attrs, fromKv)
        
    def generateMatchRecord(self, fromKv):
        return self._generateRecord(self.matchAttrs, fromKv)

class RecordTests(unittest.TestCase):
    @staticmethod
    def genAttrs():
        result = {} 
        for i in range(5):
            result["attr"+str(i)] = attribute.Attribute()
        
        at = result["attr3"]
        at.setType(int)

        at = result["attr4"]
        at.setType(float)

        return result

    def doValidSet(self, rec, key, setTo):
        self.assertTrue(rec.setAttribute(key, setTo))
        self.assertEqual(rec.getAttribute(key), setTo)

    def doInvalidSet(self, rec, key, setTo):
        self.assertFalse(rec.setAttribute(key, setTo))
        self.assertIsNone(rec.getAttribute(key))

    def test_record(self):
        try:
            Record(None)
            self.assertIsNotNone(None)
        except ValueError:
            pass

        attrs = RecordTests.genAttrs()
        rec = Record(attrs)

        for (k, v) in attrs.items():
            self.assertIsNotNone(rec.getRawAttribute(k))
            self.assertIsNone(rec.getAttribute(k))
            self.doValidSet(rec, k, None)

            if v.getType() is str:
                self.doValidSet(rec, k, "HELLO")
            elif v.getType() is int:
                self.doValidSet(rec, k, 32)
                self.doInvalidSet(rec, k, "lol")
                self.doInvalidSet(rec, k, "")
            elif v.getType() is float:
                self.doValidSet(rec, k, 32)
                self.doValidSet(rec, k, 32.0)
                self.doInvalidSet(rec, k, "lol")
                self.doInvalidSet(rec, k, "")
        
        self.assertFalse(rec.setRawAttribute("ATTRIBOOT", 'hi'))
        self.assertFalse(rec.setRawAttribute("", 'hi'))
        self.assertFalse(rec.setRawAttribute(None, 'hi'))

    class RecordTest(Record):
        def __init__(self, attrs):
            super().__init__(attrs)

    def test_factory(self):
        rf = RecordFactory()
        self.assertRaises(ValueError, rf.generateRecord, (rf, None))
        self.assertRaises(ValueError, rf.generateRecord, (rf, "Hello"))
        self.assertTrue(rf.addAttribute("attr1", attribute.Attribute()))

        at = attribute.Attribute()
        at.setValue("hello")
        self.assertTrue(rf.addAttribute("attr2", at))

        at = attribute.Attribute()
        at.setType(int)
        assert at.getType() is int
        self.assertTrue(rf.addAttribute("attr3", at))

        rec = rf.generateRecord(None)
        self.assertIsNotNone(rec)

        at = rec.getRawAttribute("attr1")
        self.assertIsNotNone(at)
        self.assertEqual(at.getType(), str)
        self.assertIsNone(at.asStr())
        
        at = rec.getRawAttribute("attr2")
        self.assertIsNotNone(at)
        self.assertIs(at.getType(), str)
        self.assertEqual(at.asStr(), "hello")

        at = rec.getRawAttribute("attr3")
        self.assertIsNotNone(at)
        self.assertIs(at.getType(), int)
        self.assertIsNone(at.asStr())

        rec = rf.generateMatchRecord(None)
        self.assertIsNotNone(rec)

        at = rec.getRawAttribute("attr1")
        self.assertIsNotNone(at)
        self.assertIs(at.getType(), str)
        self.assertIsNone(at.asStr())
        
        at = rec.getRawAttribute("attr2")
        self.assertIsNotNone(at)
        self.assertIs(at.getType(), str)
        self.assertEqual(at.asStr(), "hello")

        at = rec.getRawAttribute("attr3")
        self.assertIsNotNone(at)
        self.assertIs(at.getType(), str)

        self.assertRaises(ValueError, rf.setFactoryType, None)

        rf.setFactoryType(RecordTests.RecordTest)
        rec = rf.generateRecord(None)
        self.assertEqual(type(rec), RecordTests.RecordTest)


if __name__ == '__main__':
    unittest.main()
