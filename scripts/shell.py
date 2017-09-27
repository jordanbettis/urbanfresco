from nh.core.app import initialize

from IPython import embed

def main():
    initialize()
    from nh.core.db import Session
    session = Session()
    embed()

if __name__ == "__main__":
    main()
