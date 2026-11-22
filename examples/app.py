import argparse
import platform
import sys


def main():
    parser = argparse.ArgumentParser(prog="app", description="ZORA Builder demo application")
    parser.add_argument("name", nargs="?", default="world", help="who to greet")
    parser.add_argument("--shout", action="store_true", help="print the greeting in upper case")
    parser.add_argument("--info", action="store_true", help="print Python and platform details")
    args = parser.parse_args()

    message = f"Hello, {args.name}!"
    print(message.upper() if args.shout else message)

    if args.info:
        print(f"python {platform.python_version()} on {platform.machine()}")
        print(f"argv[0] = {sys.argv[0]}")


if __name__ == "__main__":
    main()
