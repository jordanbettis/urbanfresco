#!/usr/bin/env python
"""
Outputs the minified version of javascript code only if DEBUG = True

Otherwise, it simply echos input
"""

from nh.core.app import initialize
initialize()
from nh.core.config import CONFIG

import jsmin, sys

def main():

    if not CONFIG.DEBUG:
        data = jsmin.jsmin(sys.stdin.read().decode("utf8"))
    else:
        data = sys.stdin.read().decode("utf8")

    sys.stdout.write(data.encode("utf8"))
        

if __name__ == "__main__":
    main()
