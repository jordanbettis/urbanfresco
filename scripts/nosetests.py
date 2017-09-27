import sys, os
from pkg_resources import load_entry_point

if __name__ == '__main__':
    os.environ['NH_UNITTEST_RUN'] = 'TRUE'
    sys.exit(
        load_entry_point('nose', 'console_scripts', 'nosetests')())
