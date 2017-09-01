#!/usr/bin/python
import sys, json

def readstr(f, DEBUG = False):
    # read length
    chars, debughdr = [], False
    while True:
        c = f.read(1)
        if DEBUG:
            if not debughdr:
                debughdr = True
                sys.stderr.write("%s> " % DEBUG)
            sys.stderr.write(c)
        if len(c) == 0:
            if DEBUG: sys.stderr.write("[incomplete length, connection closed]\n")
            return ""
        if c == ":":
            break
        chars.append(c)
    msglen = int("".join(chars))
    result, s = "", "1"
    while len(result) < msglen and len(s) > 0:
        s = f.read(msglen-len(result))
        result = result + s
    if DEBUG: sys.stderr.write("%s" % result)
    if len(result) < msglen:
        if DEBUG: sys.stderr.write("[incomplete msg, connection closed]\n")
        return ""
    if DEBUG: sys.stderr.write("\n")
    return result

def writestr(f, s, DEBUG = False):
    f.write("%d:%s" % (len(s), s))
    f.flush()
    if DEBUG:
        sys.stderr.write("%s> %d:%s\n" % (DEBUG, len(s), s))

def readobj(f, DEBUG = False):
    s = readstr(f, DEBUG)
    if s:
        return json.loads(s)
    else:
        return False

def writeobj(f, obj, DEBUG = False):
    return writestr(f, json.dumps(obj, separators=(',',':')), DEBUG)
