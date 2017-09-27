import os, sys

def main(listen, make_tilemaker):
    from nh.core.app import CoreApp, initialize

    import tornado.httpserver
    import tornado.ioloop
    import tornado.web
    import tornado.wsgi

    initialize()

    from nh.core.config import CONFIG
    import nh.map.mapserver
    import nh.map.tilemaker

    if make_tilemaker:
        tornado_app = tornado.web.Application([
            ("/(\w+)/(\w+)/([0-9]+)/([0-9]+)/([0-9]+)/(\w+).png",
             nh.map.tilemaker.TileMaker,)
            ])
    else:
        wsgi_app = tornado.wsgi.WSGIContainer(CoreApp())
        tornado_app = tornado.web.Application(
            [(CONFIG.STATIC_URL + r"/(.*)",
              tornado.web.StaticFileHandler, {"path": CONFIG.STATIC_DIR}),
             (CONFIG.IMAGE_URL + r"/(.*)",
              tornado.web.StaticFileHandler, {"path": CONFIG.IMAGE_DIR}),
             (r"/tms/(\w+)/([0-9]+)/([0-9]+)/([0-9]+).png",
              nh.map.mapserver.MapServer),
             ('.*', tornado.web.FallbackHandler, dict(fallback=wsgi_app)),
             ])
        
    server = tornado.httpserver.HTTPServer(tornado_app)

    ## Only ever listen to localhost, since we use nginx in prod
    server.listen(listen, "127.0.0.1")
    tornado.ioloop.IOLoop.instance().start()

def curse(pid_filename):
    """
    Turn the process into a daemon, writing a pid to /var/run

    pid_filename is the fqpath to which we write the pid 
    """
    ## Fork dance to detach from the parent
    pid = os.fork() # Intermediate child
    if (pid == 0):
        os.setsid()
        pid = os.fork() # Daemon
        if (pid == 0):
            os.chdir("/tmp")
            os.umask(0)
        else:
            os._exit(0) # Kill intermediate
    else:
        os._exit(0) # Kill original parent

    pid = os.getpid()
    
    print "Creating nh daemon with pid %s" % (pid)

    pidfd = open(pid_filename, "w")
    pidfd.write("%s\n" % pid)
    pidfd.close()
    
    ## Close stdio
    sys.stdin.close()
    sys.stdout.close()
    sys.stderr.close()

    sys.stdin = open("/dev/null", "r")
    sys.stdout = open("/tmp/nh.output.log", "a+")
    sys.stderr = sys.stdout

    sys.stderr.write("Created daemon with %s\n" % pid_filename)
    
    return

if __name__ == '__main__':
    listen = sys.argv[-1:][0]
    if "-d" in sys.argv:
        fname_index = sys.argv.index("-d") + 1
        curse(sys.argv[fname_index])

    main(listen, "-t" in sys.argv)
