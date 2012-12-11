import random
import re

def help(sender, topic):
    # If this gets sooper-big, we can just have it automatically
    # put together help based on docstrings
    helptopics = {"random": ".random [max|min-max]\n" +
                            "Generates a random number from 0 to 1000." + 
                            " Minimum and maximum are specifiable." + 
                            " No negatives plz"} 

    # If they started the topic with a ., ignore it.
    if topic.startswith('.'):
        topic = topic[1:]

    topic = topic.lower()

    if not topic:
        hts = ("{}: {}".format(k,v) for k, v in helptopics.items())
        # Start with \n to prep for name
        res = "\n"
        res += '\n\n'.join(hts)
    elif topic in helptopics:
        res = helptopics[topic]
    else:
        res = "Invalid topic."

    return "{}, {}".format(sender, res)

def sayHi(sender, _):
    return "Hello, {}!".format(sender)

def _tryParse(string, default, targtype = int):
    try:
        return targtype(string)
    except:
        return default

def randomNumber(sender, rest):
    rest = rest.strip()

    lowlimit = 0
    uplimit = 1000

    # if rest isn't empty
    if rest:
        # ignore everything but the first "word"
        rest = re.split('\s+', rest, maxsplit = 1)[0]
        
        # if both lower and upper limit were specified
        if rest.find('-') != -1:
            low, rest = rest.split('-')[0:1]
            lowlimit = _tryParse(low, lowlimit)

        uplimit = _tryParse(rest, uplimit)

        if lowlimit == uplimit:
            return "{}, that's not very random.".format(sender)

        # we allow "backward" ranges
        if lowlimit > uplimit:
            t = uplimit
            uplimit = lowlimit
            lowlimit = t

    return "{}: {}".format(sender, random.randint(lowlimit, uplimit))

