import sys

from greeter import greet
from textkit.fmt import banner


def main():
    names = sys.argv[1:] or ["Termux"]
    print(banner("ZORA demo"))
    for name in names:
        print(greet(name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
