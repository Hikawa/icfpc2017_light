#!/usr/bin/python

import sys, collections, libpunter

IODEBUG_OUT, IODEBUG_IN = False, False
#IODEBUG_OUT, IODEBUG_IN = "[P->S]", "[S->P]"
NAME="lambda punter"

def setup(data):
    state = {"punter":data["punter"]}
    return {"ready":data["punter"],"state":state}

def move(data):
    state = data["state"]
    return {"pass":{"punter":state["punter"]},"state":state}

def main():
    libpunter.writeobj(sys.stdout, {"me":NAME}, IODEBUG_OUT)
    if not libpunter.readobj(sys.stdin, IODEBUG_IN):
        return # no responce {"you":NAME}
    data = libpunter.readobj(sys.stdin, IODEBUG_IN)
    if "punter" in data and "map" in data:
        libpunter.writeobj(sys.stdout, setup(data), IODEBUG_OUT)
    elif "move" in data:
        libpunter.writeobj(sys.stdout, move(data), IODEBUG_OUT)
    elif "stop" in data:
        for score in data["stop"]["scores"]:
            if score["punter"] == data["state"]["punter"]:
                sys.stderr.write("MY SCORE: %s\n" % score["score"])
    else:
        sys.stderr.write("ERROR: UNKNOWN COMMAND: %s\n" % data)

if __name__ == "__main__":
    main()
