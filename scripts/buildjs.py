#!/usr/bin/env python

import os, sys

from nh.core.app import initialize
initialize()
from nh.core.config import CONFIG

import jsmin

def main(config_name):
    base_dir = CONFIG[config_name]['base-dir']
    file_names = CONFIG[config_name]['files']
    output = []
    for fname in file_names:
        fd = open(os.path.join(base_dir, fname))
        output.append(
            u"\n\n/************ BEGIN FILE %s *****************/\n\n" % fname)
        output.append(fd.read().decode("utf8"))
        output.append(
            u"\n\n/************ END FILE %s *******************/\n\n" % fname)

    output_string = u"".join(output)
    if not CONFIG.DEBUG:
        output_string = jsmin.jsmin(output_string)

    sys.stdout.write(output_string.encode("utf8"))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        config_name = sys.argv[1]
    else:
        config_name = "NH_CLIENT_APP"
    main(config_name)
        
