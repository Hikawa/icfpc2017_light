#!/usr/bin/python
import sys, socket, select, subprocess, libpunter
DEBUG = False #True
WIDTH, HEIGHT = 600, 450
VISUAL = False

class Empty: pass

def w_init():
    pygame.init()
    w = Empty()
    w.window = pygame.display.set_mode((WIDTH,HEIGHT))
    pygame.display.set_caption("PyGame Demo")
    w.bgColor = pygame.Color("#000000")
    w.mineColor = pygame.Color("#FF0000")
    w.riverColor = pygame.Color("#0000FF")
    w.myColor = pygame.Color("#00FF00")
    w.otherColors = [pygame.Color("#"+c) for c in (
        "707070","C0C0C0","800000","008000","000080","808000","008080","800080",
        "FFFF00","FF00FF","00FFFF","FF8080","80FF80","8080FF","FFFFFF","FF8000") ]
    #w.otherColors = [pygame.Color("#FF00FF")] # single color for everyone else
    return w

def w_redraw(w):
    #pygame.draw.rect(w.window, w.bgColor, (0,0,WIDTH,HEIGHT))
    for r,color in w.rivers.iteritems():
        pygame.draw.line(w.window, color, w.coords[r[0]], w.coords[r[1]])
    for mine in w.mines:
        pygame.draw.circle(w.window, w.mineColor, w.coords[mine], 2, 0)
    pygame.display.update()

def w_gamesetup(w, data):
    w.punter = data["punter"]
    map = data["map"]
    # sites coords
    xmin = min(site["x"] for site in map["sites"])
    xmax = max(site["x"] for site in map["sites"])
    ymin = min(site["y"] for site in map["sites"])
    ymax = max(site["y"] for site in map["sites"])
    kx, ky = (xmax-xmin)/(WIDTH-5), (ymax-ymin)/(HEIGHT-5)
    if kx <= 0: kx = 1
    if ky <= 0: ky = 1
    w.coords=dict( (site["id"], ( int(3+(site["x"]-xmin)/kx) , int(3+(site["y"]-ymin)/ky) )) for site in map["sites"] )
    # mines
    w.mines = set(map["mines"])
    # rivers
    w.rivers = dict( ((r["source"],r["target"]),w.riverColor) for r in map["rivers"] )
    #w_redraw(w)

def w_gameclaim(w, data):
    claim = data["claim"]
    if claim["punter"] == w.punter:
        c = w.myColor
    else:
        c = w.otherColors[claim["punter"] % len(w.otherColors)]
    a, b, found = claim["source"], claim["target"], 0
    if (a,b) in w.rivers:
        found += 1
        w.rivers[(a,b)] = c
    if (b,a) in w.rivers:
        found += 1
        w.rivers[(b,a)] = c
    if found != 1:
        sys.stderr.write("ERROR claiming %s (found=%d)\n" % (claim, found))
    #w_redraw(w)

def w_destroy(w):
    #sys.stderr.write("Press ENTER to close...")
    #sys.stdin.readline()
    pygame.quit()

def main(host, port, cmdargs):
    # open slave
    slave = subprocess.Popen(cmdargs, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    # read me/you
    msg = libpunter.readobj(slave.stdout, "initPin")
    myname = msg["me"]
    libpunter.writeobj(slave.stdin, {"you":myname}, "initPout")

    # connect
    sd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sd.connect( (host, port) )
    fd = sd.makefile()
    #if DEBUG:
    sys.stderr.write("connected to %s:%d.\n" % (host, port))
    # send initial me/you
    libpunter.writeobj(fd, {"me":myname}, "initSout")

    state = None
    if VISUAL: w = w_init()
    while True:
        readable, _, _ = select.select((slave.stdout,fd), (), ())
        if slave.stdout in readable:
            msg = libpunter.readobj(slave.stdout, DEBUG and "P->X")
            if not msg:
                # restart slave
                slave.stdin.close()
                slave.wait()
                slave = subprocess.Popen(cmdargs, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            elif "me" in msg:
                libpunter.writeobj(slave.stdin, {"you":msg["me"]}, DEBUG and "X->P")
            else:
                if "state" in msg:
                    state = msg["state"]
                    del msg["state"]
                if VISUAL and "claim" in msg:
                    w_gameclaim(w, msg)
                    w_redraw(w)
                libpunter.writeobj(fd, msg, DEBUG and "X->S")
        elif fd in readable:
            msg = libpunter.readobj(fd, DEBUG and "S->X")
            if not msg: break
            if "you" in msg:
                pass
            else:
                if VISUAL and "map" in msg:
                    w_gamesetup(w, msg)
                    w_redraw(w)
                if VISUAL and "move" in msg:
                    for move in msg["move"]["moves"]:
                        if "claim" in move:
                            w_gameclaim(w, move)
                    w_redraw(w)
                if state is not None: msg["state"] = state
                libpunter.writeobj(slave.stdin, msg, DEBUG and "X->P")
    if VISUAL: w_destroy(w)

    if DEBUG: sys.stderr.write("closing everything.")
    fd.close()
    if DEBUG: sys.stderr.write(".")
    sd.close()
    if DEBUG: sys.stderr.write(".")
    slave.stdin.close()
    if DEBUG: sys.stderr.write("\n")
    while True:
        msg = slave.stdout.read()
        if msg:
            if DEBUG: sys.stderr.write(msg)
        else:
            break
    if DEBUG: sys.stderr.write("done.\n")
    slave.wait()

if __name__ == "__main__":
    while len(sys.argv) > 1 and sys.argv[1] in ("-v", "-d"):
        if sys.argv[1] == "-v":
            import pygame
            VISUAL = True
        elif sys.argv[1] == "-d":
            DEBUG = True
        del sys.argv[1]
    if len(sys.argv) < 4:
        print("Online wrapper. Allows offline-player to play online!")
        print("USAGE: %s [-v] <host> <port> ./player.py [<args>]" % sys.argv[0])
    else:
        main(sys.argv[1], int(sys.argv[2]), sys.argv[3:])
