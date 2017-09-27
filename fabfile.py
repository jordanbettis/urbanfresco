from fabric.api import local
from fabric.context_managers import settings
import os, sys

_LOCAL_ROOT=os.path.split(__file__)[0]

def install_reqs():
    local(_venv("pip install -r %s/requirements.txt" % _LOCAL_ROOT))

def create_env():
    local("python2.7 /usr/bin/virtualenv --clear --system-site-packages env")
    fd = open(
        "%s/env/lib/python2.7/site-packages/easy-install.pth" % _LOCAL_ROOT)
    lines = fd.readlines()
    fd.close()
    fd = open("%s/env/lib/python2.7/site-packages/easy-install.pth" \
                  % _LOCAL_ROOT, "w")
    fd.write(lines[0])
    fd.write("%s/server\n" % _LOCAL_ROOT)
    local("mkdir %s/env/log" % _LOCAL_ROOT)
    local("mkdir %s/env/test_output/" % _LOCAL_ROOT)
    local("mkdir %s/env/upload/" % _LOCAL_ROOT)
    local("mkdir %s/env/cache/" % _LOCAL_ROOT)
    local("mkdir %s/env/srv/" % _LOCAL_ROOT)
    local("mkdir %s/env/run/" % _LOCAL_ROOT)
    local("mkdir %s/env/static/" % _LOCAL_ROOT)
    for x in lines[1:]:
        fd.write(x)

def pyshell():
    local(_venv("python ./scripts/shell.py"))

def shell():
    local("bash --rcfile ./env/bin/activate")

def run_server():
    """ Start daemons and tail the output log for development """
    local("echo > /tmp/nh.output.log")
    stop_daemons()
    start_daemons()
    local("tail -f /tmp/nh.output.log")

def run_tests():
    local(_venv("python ./scripts/test_db.py setup"))
    local("rm -r %s/env/test_output" % _LOCAL_ROOT)
    local("mkdir %s/env/test_output" % _LOCAL_ROOT)
    with settings(warn_only=True):
        local(_venv("python ./scripts/nosetests.py server"))
    local(_venv("python ./scripts/test_db.py teardown"))

def start_daemons():
    """ Start web and tile server daemons """
    local(_venv("python ./scripts/start_daemons.py %s" % _LOCAL_ROOT))

def stop_daemons():
    """ Stop web server and tile server daemons """
    run_dir = "%s/env/run" % _LOCAL_ROOT
    for pidfile in os.listdir(run_dir):
        file_fqn = os.path.join(run_dir, pidfile)
        with settings(warn_only=True):
            local("kill -HUP `cat %s`" % file_fqn)
        local("rm %s" % file_fqn)

def build_full_client():
    """ Build all assets in the static serve directory, including contrib """
    build_client()
    build_contrib()

def build_client():
    """
    Build the client side app, including assets and javascript. But skip
    the contrib applications.
    """
    with settings(warn_only=True):
        local("rm -r %s/env/static/img" % _LOCAL_ROOT)
    local("mkdir %s/env/static/img" % _LOCAL_ROOT)
    local("cp %s/media/*.jpg %s/env/static/img" % (_LOCAL_ROOT, _LOCAL_ROOT))
    local("cp %s/media/*.png %s/env/static/img" % (_LOCAL_ROOT, _LOCAL_ROOT))
    local("cp %s/media/*.gif %s/env/static/img" % (_LOCAL_ROOT, _LOCAL_ROOT))
    
    with settings(warn_only=True):
        local("rm -r %s/env/static/css" % _LOCAL_ROOT)
    local("mkdir %s/env/static/css" % _LOCAL_ROOT)
    local("cp %s/media/*.css %s/env/static/css" % (_LOCAL_ROOT, _LOCAL_ROOT))
        
    with settings(warn_only=True):
        local("rm -r %s/env/static/client" % _LOCAL_ROOT)
    local("mkdir %s/env/static/client" % _LOCAL_ROOT)
    fname = "%s/env/static/client/nh.js" % _LOCAL_ROOT
    local(_venv("python ./scripts/buildjs.py > %s" % fname))

def build_contrib():
    """ Add the javascript code """
    with settings(warn_only=True):
        local("rm -r %s/env/static/contrib" % _LOCAL_ROOT)
    local("mkdir %s/env/static/contrib" % _LOCAL_ROOT)
    fname = "%s/env/static/contrib/merged.js" % _LOCAL_ROOT
    local(_venv("python ./scripts/buildjs.py CONTRIB_APP > %s" % fname))
    
    local(_venv("cat %s | python ./scripts/minify.py > %s" % (
                "%s/client/contrib/modernizr.js" % _LOCAL_ROOT,
                "%s/env/static/contrib/modernizr.js" % _LOCAL_ROOT)))

    local(_venv("python ./scripts/build-openlayers.py"))

    local("cp -r ./client/contrib/OpenLayers/theme ./env/static/contrib/")
    local("cp -r ./client/contrib/OpenLayers/img ./env/static/contrib/")
    
    
def _venv(command):
    """
    Prepend 'command' string to activate the virtualenv before running
    it.
    """
    return ". %s/env/bin/activate && %s" % (_LOCAL_ROOT, command)
