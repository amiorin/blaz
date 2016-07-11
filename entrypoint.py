#!/usr/bin/env python3

from os import execvpe, environ
from sys import argv, exit
from subprocess import check_call
import semantic_version

msg = """
Your version of Blaz ({}) is too old.
A version greater than or equal to {} is required.
Plese upgrade Blaz:

    pip install --upgrade blaz
"""


def main():
    if "BLAZ_VERSION" in environ:
        require_version = semantic_version.Version("0.0.23")
        current_version = semantic_version.Version(environ["BLAZ_VERSION"])
        if require_version > current_version:
            print(msg.format(current_version, require_version))
            exit(1)
    if "BLAZ_UID" in environ and "BLAZ_GID" in environ:
        print("Creting user jenkins with uid {} and gid {}".format(environ["BLAZ_UID"], environ["BLAZ_GID"]))
        check_call("groupadd -o --gid {} jenkins".format(environ["BLAZ_GID"]), shell=True)
        check_call("useradd -o --uid {} --gid jenkins jenkins".format(environ["BLAZ_UID"]), shell=True)
        check_call("install -d -o jenkins -g jenkins /home/jenkins".format(environ["BLAZ_UID"]), shell=True)
    execvpe(argv[1], argv[1:], environ)

if __name__ == "__main__":
    main()
