#!/usr/bin/python

import sys, collections, libpunter

IODEBUG_OUT, IODEBUG_IN = False, False
#IODEBUG_OUT, IODEBUG_IN = "[P->S]", "[S->P]"
NAME="lambda punter"
MODE=255 # 0=passer, 1=semirandom, 2=greed, 3=bfs, 4=bridges, 5=siteadd

def setup_dijkstra(map, start):
    d, result = {start:0}, {}
    while d:
        a = min(d, key=d.get)
        result[a] = d[a]
        del d[a]
        for b in map.get(a,()):
            if b not in result and b not in d:
                d[b] = result[a]+1
    return result

def setup(data):
    state = {"punter":data["punter"]}
    #state["sites"] = [str(site["id"]) for site in data["map"]["sites"]]
    state["mines"] = [str(mine) for mine in data["map"]["mines"]]
    map = {}
    for river in data["map"]["rivers"]:
        a, b = str(river["source"]), str(river["target"])
        if a != b:
            map.setdefault(a,[]).append(b)
            map.setdefault(b,[]).append(a)
    # remove repeats:
    for k,v in map.iteritems():
        map[k] = list(set(v))
    state["map"] = map
    #state["myrivers"] = []
    #state["otherrivers"] = []
    # helpers
    state["mymines"] = dict( (i,[i]) for i in state["mines"] )
    state["d"] = dict( (v,setup_dijkstra(map,v)) for v in state["mines"] )
    state["myscore"] = 0
    # siteadd
    if MODE >= 5:
        dmin = {}
        for v,sitedists in state["d"].iteritems():
            for site,dist in sitedists.iteritems():
                dmin.setdefault(site,[]).append(dist)
        N = 1.0*len(data["map"]["sites"])
        for site,dists in dmin.iteritems():
            dmin[site] = min(dists)/N
        siteadd = dict(dmin)
        #sys.stderr.write("### 1 ### siteadd = %s\n" % siteadd)
        q = collections.deque()
        q.extendleft(dmin.iterkeys())
        delta = 1/N/N
        while q:
            a = q.pop()
            #sys.stderr.write("### 2 ### pop = %s\n" % a)
            for b in map.get(a,[]):
                if dmin[a] > dmin[b]:
                    if siteadd[a] > delta:
                        siteadd[b] = siteadd[a]-delta
                    else:
                        siteadd[b] = 0
                    q.appendleft(b)
        state["siteadd"] = siteadd
    else: # MODE <= 5 - set them all to zero
        state["siteadd"] = dict( (str(site["id"]),0) for site in data["map"]["sites"] )
    return {"ready":data["punter"],"state":state}

def estimate(state, site2mine, a, b):
    if a not in site2mine and b not in site2mine:
        #raise RuntimeError("IMPOSSIBLE! Claiming unconnected river!") # TODO
        return 0
    elif a in site2mine and b not in site2mine:
        return sum(state["d"][mine][b]**2 for mine in site2mine[a])
    elif a not in site2mine and b in site2mine:
        return estimate(state, site2mine, b, a)
    elif site2mine[a] == site2mine[b]:
        return 0
    else:
        return sum(state["d"][minea][siteb]**2 for minea in site2mine[a] for siteb in state["mymines"][site2mine[b][0]]) + sum(state["d"][mineb][sitea]**2 for mineb in site2mine[b] for sitea in state["mymines"][site2mine[a][0]])

def addriver(state, site2mine, a, b, value):
    if a not in site2mine and b not in site2mine:
        pass #raise RuntimeError("IMPOSSIBLE! Claiming unconnected river!") # TODO/FIXME
        state["map"][a].remove(b) # remove it from map to make sure we won't try to claim it again
        state["map"][b].remove(a)
    elif a in site2mine and b not in site2mine:
        merged = state["mymines"][site2mine[a][0]]
        merged.append(b)
        for minea in site2mine[a]:
            state["mymines"][minea] = merged
    elif a not in site2mine and b in site2mine:
        return addriver(state, site2mine, b, a, value)
    elif site2mine[a] == site2mine[b]:
        pass # state unchanged
    else:
        merged = state["mymines"][site2mine[a][0]] + state["mymines"][site2mine[b][0]]
        for minea in site2mine[a]:
            state["mymines"][minea] = merged
        for mineb in site2mine[b]:
            state["mymines"][mineb] = merged
    state["myscore"] += value
    #state["myrivers"].append([a,b])
    #TODO: FIXME for unconnected rivers

def bridgebest(state, site2mine):
    map = state["map"]
    for mine,sites in state["mymines"].iteritems():
        exits = dict( (b,a) for a in sites for b in map.get(a,[]) if b not in site2mine )
        if len(exits) == 1:
            for b,a in exits.iteritems():
                return (a,b), estimate(state, site2mine, a, b)
    return None, 0

def bfsbest(state, site2mine):
    site2id = dict( (site,min(mines)) for site,mines in site2mine.iteritems() )
    if len(set(site2id.values())) <= 1:
        return None, 0
    q = collections.deque()
    # start points
    map = state["map"]
    for mine,sites in state["mymines"].iteritems():
        for a in sites:
            for b in map.get(a,[]):
                if a in site2id and b in site2id and site2id[a] != site2id[b]:
                    return (a,b), estimate(state, site2mine, a, b) # found
                if b not in site2id:
                    site2id[b] = site2id[a]
                    q.appendleft( (a,b,site2id[a],b) )
    while q:
        a, b, id, cura = q.pop()
        for curb in map.get(cura,[]):
            if curb in site2id and site2id[curb] != id:
                return (a,b), estimate(state, site2mine, a, b) # found
            if curb not in site2id:
                site2id[curb] = id
                q.appendleft( (a,b,id,curb) )
    return None, 0

def greedbest(state, site2mine):
    map = state["map"]
    best, bestvalue = None, 0
    for mine,sites in state["mymines"].iteritems():
        thisset = set(sites)
        for a in sites:
            for b in map.get(a,[]):
                if b not in thisset: #and (a,b) not in otherrivers and (b,a) not in otherrivers:
                    value = estimate(state, site2mine, a, b) + state["siteadd"][b]
                    if best is None or value > bestvalue:
                        best, bestvalue = (a,b), value
    return best, int(bestvalue)

def anybest(state, site2mine):
        #try:
        map = state["map"]
        sitecnt = dict( (site,len(sites)) for site,sites in map.iteritems() if site not in site2mine and sites )
        a = min(sitecnt, key=sitecnt.get)
        b = min(map[a], key=sitecnt.get)
        return (a,b), estimate(state, site2mine, a,b)
        #except:
        #return None, 0

def move(data):
    state = data["state"]
    # add foreign rivers
    for move in data["move"]["moves"]:
        if "claim" in move:
            claim = move["claim"]
            if claim["punter"] != state["punter"]:
                a, b = str(claim["source"]), str(claim["target"])
                #state["otherrivers"].append([ str(claim["source"]), str(claim["target"]) ])
                state["map"][a].remove(b)
                state["map"][b].remove(a)
    #otherrivers = set( (r[0],r[1]) for r in state["otherrivers"] )
    # generate site2mine from state
    site2mine = {}
    for mine,sites in state["mymines"].iteritems():
        for site in sites:
            site2mine.setdefault(site,[]).append(mine)
    # find best move
    best, bestvalue = None, 0
    if best is None and MODE >= 4:
        best, bestvalue = bridgebest(state, site2mine)
    if best is None and MODE >= 3:
        best, bestvalue = bfsbest(state, site2mine)
    if best is None and MODE >= 2:
        best, bestvalue = greedbest(state, site2mine)
    if best is None and MODE >= 1:
        best, bestvalue = anybest(state, site2mine)
    # return result
    if best is None:
        return {"pass":{"punter":state["punter"]},"state":state}
    else:
        addriver(state, site2mine, best[0], best[1], bestvalue)
        return {"claim":{"punter":state["punter"],"source":int(best[0]),"target":int(best[1])},"state":state}

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
    try: MODE = int(sys.argv[1])
    except: pass
    main()
