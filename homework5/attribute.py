#!/usr/bin/python

import re
import string
import unittest

def isBasicRegex(test):
    if type(test) is str:
        regexChars = ['*']
        for i in regexChars:
            if i in test:
                return True

    return False

def strToRegex(toRegex):
    handleChars = ['\\', '?', '^', '$', '(', ')', '[', ']', '.', '+']

    for i in handleChars:
        toRegex = toRegex.replace(i, '\\' + i)

    toRegex = toRegex.replace('*', '.*')
    toRegex = r'\A' + toRegex + r'\Z'

    try:
        return re.compile(toRegex, re.DOTALL)
    except:
        return None

# 
# Attribute class:
# Used so that attributes can be generic/very easily added/removed. 
# This class takes care of type casting, type matching, etc.
#
class Attribute:
    def __init__(self, attr = None):
            self.type_ = str
            self.value = None
            self.multi = False
            self.required = True

    def __str__(self):
        return self.asStr()

    def __eq__(self, other):
        if type(other) is not type(self):
            raise ValueError("Can't compare Attribute to " + str(type(other)))
        
        if self.type_ is not other.type_:
            return False

        if self.multi is not other.multi:
            return False

        if self.isNull() != other.isNull():
            return False

        return self.required == other.required and self.value == other.value

    def __ne__(self, other):
        return not self.__eq__(other)

    def isNull(self):
        "Return if this has a value."
        return self.value is None

    def asStr(self):
        "Return value as a string"
        return self.value if self.type_ is str or self.value is None else str(self.value)

    def asNatural(self):
        "Return value as the type it's supposed to be"
        return self.value

    def getType(self):
        return self.type_

    def setType(self, type_):
        "Set the type of the attribute. If we have a value, this will try to cast it."
        if type_ is list:
            raise ValueError("Lists aren't supported yet")
        if self.type_ is not type_:
            if self.value is not None:
                vTo = self.asStr()
                self.type_ = type_
                self.setValue(vTo)
            else:
                self.type_ = type_

    def setValue(self, valueTo):
        "Set the value of the Attribute, with necessary casting."
        if valueTo is None:
            self.value = None
        elif type(valueTo) is not self.type_:
            try:
                self.value = self.type_(valueTo)
                return True
            except:
                self.value = None
                return False
        else:
            self.value = valueTo
        return True

    def _matchesCriteriaRegex(self, criteriaStr):
        assert criteriaStr is not None
        assert self.value is not None
        
        reg = strToRegex(criteriaStr)

        if reg is None:
            raise ValueError("Couldn't parse input criteria")

        return reg.match(self.asStr()) is not None


    def _matchesCriteriaType(self, criteriaStr):
        assert criteriaStr is not None
        assert self.value is not None

        try:
            criteriaType = self.type_(criteriaStr)
        except:
            return False

        return self.asNatural() == criteriaType

    def multipleAllowed(self):
        return self.multi

    def setMultipleAllowed(self, multi):
        self.multi = bool(multi)

    def matchesCriteria(self, criteriaStr, forceRaw = False):
        "Checks if this matches the given criteria."
        if criteriaStr is None:
            return True

        if self.value is None:
            return False

        if not forceRaw and isBasicRegex(criteriaStr):
            return self._matchesCriteriaRegex(criteriaStr)
        else:
            return self._matchesCriteriaType(criteriaStr)

class AttributeTests(unittest.TestCase):
    def test_standalone(self):
        # testing isBasicRegex
        self.assertFalse(isBasicRegex("30"))
        self.assertFalse(isBasicRegex(30))
        self.assertFalse(isBasicRegex("!@#$%^&()_+{}|:<>?';/.,=-0987654321`~\""))
        self.assertTrue(isBasicRegex("*3*"))
        self.assertTrue(isBasicRegex("3*"))
        self.assertTrue(isBasicRegex("*3"))
        self.assertTrue(isBasicRegex("*"))

        # testing the building regex functions
        reg = strToRegex("3*")
        self.assertIsNotNone(reg)
        self.assertIsNotNone(reg.match("300"))
        self.assertIsNone(reg.match("0300"))

        reg = strToRegex("!@#$%^&()_+{}|:<>?';/.,=-0987654321`~\"")
        self.assertIsNotNone(reg)
        self.assertIsNotNone(reg.match("!@#$%^&()_+{}|:<>?';/.,=-0987654321`~\""))

        reg = strToRegex("*3*")
        self.assertIsNotNone(reg)
        self.assertIsNotNone(reg.match("hello my name is foobar\n 3 \nwhat is your name"))

        reg = strToRegex(".?")
        self.assertIsNotNone(reg)
        self.assertIsNotNone(reg.match(".?"))
        self.assertIsNone(reg.match("3"))
        self.assertIsNone(reg.match(""))

    def test_constructor(self):
        # make sure constructors work properly
        at1 = Attribute()
        self.assertFalse(at1.multipleAllowed())
        self.assertIsNone(at1.asStr())
        self.assertIsNone(at1.asNatural())
        self.assertIs(at1.getType(), str)
        at1.setType(int)
        self.assertTrue(at1.setValue("32"))

    def test_set(self):
        at1 = Attribute()

        self.assertTrue(at1.setValue("s"))
        self.assertEqual(at1.asNatural(), "s")
        self.assertEqual(at1.asStr(), "s")

        self.assertTrue(at1.setValue(3))
        self.assertEqual(at1.asStr(), "3")

        at1.setType(int)
        self.assertIs(at1.getType(), int)
        self.assertIs(at1.asNatural(), 3)
        
        self.assertTrue(at1.setValue("32"))
        at1.setMultipleAllowed(True)
        
        self.assertFalse(at1.setValue("hello"))
        self.assertIs(at1.asNatural(), None)
        
        self.assertTrue(at1.setValue("32"))
        self.assertEqual(at1.asNatural(), 32)

    def test_matches(self):
        # two blank attributes should match
        self.assertTrue(Attribute().matchesCriteria(None))
        self.assertFalse(Attribute().matchesCriteria(""))

        at1 = Attribute()
        at1.setType(int)
        at1.setValue("32")
        at1.setMultipleAllowed(True)

        # All possible matches...
        self.assertTrue(at1.matchesCriteria("32"))
        self.assertTrue(at1.matchesCriteria("*2"))
        self.assertTrue(at1.matchesCriteria("*"))
        self.assertTrue(at1.matchesCriteria("3*"))

        self.assertFalse(at1.matchesCriteria("2*"))
        self.assertFalse(at1.matchesCriteria("hello"))
        self.assertFalse(at1.matchesCriteria("*3"))
        self.assertFalse(at1.matchesCriteria(".3"))
        self.assertFalse(at1.matchesCriteria("[0-9]?3"))
        self.assertFalse(at1.matchesCriteria(""))
        self.assertTrue(at1.matchesCriteria(None))


# If we're main, unit tests.
if __name__ == '__main__':
    unittest.main()

