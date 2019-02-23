#!/usr/bin/env python
# Script to sync db and/or data from remote host
#
# Brainstorm S.n.c - http://brainstorm.it
# author: Mario Orlandi, 2019

from __future__ import absolute_import

REMOTE_HOST = 'www1.somewhere.com'
PROJECT = 'someproject'

import os
import sys
import argparse
import traceback

try:
    # this raw_input is not converted by 2to3
    term_input = raw_input
except NameError:
    term_input = input
args = None


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = term_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")


def run_command(command):
    dry_run = args.dry_run
    interactive = not args.quiet
    if dry_run:
        print("\x1b[1;37;40m# " + command + "\x1b[0m")
    else:
        print("\x1b[1;37;40m" + command + "\x1b[0m")

        if interactive and not query_yes_no("Proceed ?"):
            print('skipped')
        else:
            rc = os.system(command)
            if rc != 0:
                raise Exception(command)


def sync_db(remote_host, project):

    # Drop local tables
    command = 'psql --command=\'drop owned by "{project}";\''.format(
        project=project
    )
    run_command(command)

    # Dump remote db and feed local one
    # Example: ssh www1.brainstorm.it "pg_dump --dbname=$PROJECT | gzip" | gunzip | psql $PROJECT
    command = 'ssh {remote_host} "pg_dump --dbname={dbname} | gzip" | gunzip | psql {dbname}'.format(
        remote_host=remote_host,
        dbname=project,
    )
    run_command(command)


def sync_media(remote_host, project):
    source = '{remote_host}:/home/{project}/public/media/'.format(
        remote_host=remote_host,
        project=project,
    )
    target = '/home/{project}/public/media/'.format(
        project=project,
    )

    command = 'rsync -avz --progress --delete {source} {target}'.format(
        source=source,
        target=target,
    )
    run_command(command)


def main():

    global args

    # Parse command line
    parser = argparse.ArgumentParser(description='Syncs database and media files for project "{project}" from remote server "{remote_server}"'.format(
        project=PROJECT,
        remote_server=REMOTE_HOST
    ))
    parser.add_argument('--dry-run', '-d', action='store_true', help="simulate actions")
    parser.add_argument('--quiet', '-q', action='store_true', help="do not require user confirmation before executing commands")
    args = parser.parse_args()

    # Add complementary info to args
    vars(args)['interactive'] = not args.quiet

    try:

        print("""
(1) SYNC database "{project}" from remote server "{remote_server}":
Here, we assume that user "{project}" has access to database "{project}" on both remote (source) and local (target) servers ...
""").format(
    project=PROJECT,
    remote_server=REMOTE_HOST
)
        sync_db(REMOTE_HOST, PROJECT)

        print("""
(2) SYNC media for project "{project}" from remote server "{remote_server}":
Here we assume that user "{project}" can access remote server "{remote_server}" via SSH, having read access to source folder '/home/{project}/public/media/'
""").format(
    project=PROJECT,
    remote_server=REMOTE_HOST
)
        sync_media(REMOTE_HOST, PROJECT)

    except Exception as e:
        print('ERROR: ' + str(e))
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
