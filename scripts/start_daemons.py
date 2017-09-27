from nh.core.app import initialize
from os import system, path
from sys import stdout, argv

def main(lr):
    ### Only argument should be the local root of the install
    ### We have to initialize the app to get at the config
    initialize()
    from nh.core.config import CONFIG

    for port in CONFIG.TILE_MAKER_PORTS:
        stdout.write("Starting tile maker on %d..." % port)
        pidfile = "%s/env/run/tile-%d.pid" % (lr, port)
        system("python %s/scripts/run_server.py -t -d %s %d" % (lr, pidfile, port))
        stdout.write("done.\n")
        
    for port in CONFIG.APP_SERVER_PORTS:
        stdout.write("Starting app server on %d..." % port)
        pidfile = "%s/env/run/app-%d.pid" % (lr, port)
        system("python %s/scripts/run_server.py -d %s %d" % (lr, pidfile, port))
        stdout.write("done.\n")

if __name__ == '__main__':
    local_root = argv[1]
    main(local_root)
