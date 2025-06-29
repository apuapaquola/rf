#!/usr/bin/env python
""" rf - A minimalist framework for reproducible computation

    Copyright (C) 2015 Apuã Paquola <apuapaquola@gmail.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import argparse
import os
import shutil
import subprocess
import re

from . import rflib

__author__ = 'Apuã Paquola'


def nodes(parent):
    """Finds the nodes under a directory tree.
    Args:
    parent: a node at the root of the tree.

    Yields:
    str: each node of the tree
    """
    assert os.path.isdir(parent)
    yield parent
    for x in os.listdir(parent):
        if x not in ['_c', '_o', '.git']:
            child = os.path.join(parent, x)
            if os.path.isdir(child):
                yield from nodes(child)


def run(args):
    """ Runs driver scripts throughout the tree
    :param args:
    :return:
    """
    rflib.run(args)


def drop(args):
    """Deletes the contents of output dirs _o
    """
    if args.recursive:
        nl = list(nodes(args.node))
    else:
        nl = [args.node]

    dirs = [os.path.join(x, '_o') for x in nl]

    for x in dirs:
        assert x.endswith('_o')
        assert not x.endswith('_c')

        if not os.path.isdir(x):
            continue

        command = ['git', 'rm', '-r'] + [x]

        try:
            subprocess.check_call(command)
        except subprocess.CalledProcessError:
            pass

        if args.force and os.path.isdir(x):
            shutil.rmtree(x)


def clone(args):
    """Clones a tree
    """
    subprocess.check_call(['git', 'clone', args.repository, args.directory])
    os.chdir(args.directory)
    subprocess.check_call(['git', 'annex', 'init'])
    subprocess.check_call(['git', 'annex', 'sync', '--no-push'])


def commit(args):
    """Commits code and output dirs to git and git-annex
    """
    if args.recursive:
        nl = list(nodes(args.node))
    else:
        nl = [args.node]

    output_dirs = [y for y in [os.path.join(x, '_o') for x in nl] if os.path.isdir(y)]
    code_dirs = [y for y in [os.path.join(x, '_c') for x in nl] if os.path.isdir(y)]

    try:
        subprocess.check_call(['git', 'add'] + code_dirs)
        subprocess.check_call(['git', 'annex', 'add'] + output_dirs)
        subprocess.check_call(['git', 'commit', '-m', args.message] + code_dirs + output_dirs)
    except subprocess.CalledProcessError:
        raise


def commit_code(args):
    """
    Commit ONLY the `_c` (code) directories under the requested node(s).

    Usage pattern mirrors `commit`, but skips git-annex entirely.
    """
    if args.recursive:
        nl = list(nodes(args.node))
    else:
        nl = [args.node]

    code_dirs = [
        y for y in (os.path.join(x, '_c') for x in nl) if os.path.isdir(y)
    ]

    if not code_dirs:
        print("No _c directories found to commit.", file=sys.stderr)
        return

    try:
        subprocess.check_call(['git', 'add'] + code_dirs)
        subprocess.check_call(['git', 'commit', '-m', args.message] + code_dirs)
    except subprocess.CalledProcessError:
        raise


def get(args):
    """Fetches contents of output directories from origin repository
    :param args:
    :return:
    """
    if args.recursive:
        nl = list(nodes(args.node))
    else:
        nl = [args.node]

    output_dirs = [y for y in [os.path.join(x, '_o') for x in nl] if os.path.isdir(y)]

    subprocess.check_call(['git', 'annex', 'sync', '--no-push'])
    subprocess.check_call(['git', 'annex', 'get'] + output_dirs)


def node_status(node):
    """Returns node status"""
    if not os.path.isdir(node + '/_c'):
        return 'no _c'
    elif os.path.exists(node + '/_c/run') and os.path.exists(node + '/_c/yield'):
        return 'run/yield'
    elif os.path.exists(node + '/_c/yield'):
        return 'yield'
    elif not (os.path.exists(node + '/_c/run') and os.access(node + '/_c/run', os.X_OK)):
        return 'no run script'
    elif not os.path.isdir(node + '/_o'):
        return 'ready to run'
    elif os.path.exists(node + '/_o/SUCCESS'):
        return 'done'
    else:
        return 'incomplete'


def pretty_print_status(args):
    """Prints status of all nodes in a subtree
    """
    command = ['tree', '--noreport', '-d', '-I', '_c|_o'] + [args.node]
    p = subprocess.Popen(command, stdout=subprocess.PIPE)
    maxlen = max((len(x.decode().rstrip()) for x in p.stdout))

    p = subprocess.Popen(command, stdout=subprocess.PIPE)

    path = []
    for line in p.stdout:
        l = line.decode().rstrip()
        m = re.search('(─ )?([^─]*)$', l)
        pos = m.start(2) // 4
        del path[pos:]
        path.append(m.group(2))
        node = '/'.join(path)
        s = node_status(node)
        if args.parseable:
            print(node, s, sep='\t')
        else:
            print(l, ' ' * (maxlen - len(l) + 13 - len(s)), s)


def print_tree(args):
    """Prints directory tree under a node.
    """
    subprocess.check_call(['tree', '--noreport', '-d', '-I', '_c|_o'] + [args.node])


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_run = subparsers.add_parser('run', help='run driver script')
    parser_run.add_argument('-n', '--dry-run', action='store_true')
    parser_run.add_argument('-v', '--verbose', action='store_true')
    parser_run.add_argument('-r', '--recursive', action='store_true')
    parser_run.add_argument('node')
    parser_run.set_defaults(func=run)

    parser_drop = subparsers.add_parser('drop', help='drop output directory')
    parser_drop.add_argument('-r', '--recursive', action='store_true')
    parser_drop.add_argument('-f', '--force', action='store_true')
    parser_drop.add_argument('node')
    parser_drop.set_defaults(func=drop)

    parser_clone = subparsers.add_parser('clone', help='clone an analysis tree')
    parser_clone.add_argument('repository')
    parser_clone.add_argument('directory')
    parser_clone.set_defaults(func=clone)

    parser_commit = subparsers.add_parser('commit', help='commit to git and git-annex')
    parser_commit.add_argument('-r', '--recursive', action='store_true')
    parser_commit.add_argument('-m', '--message', required=True)
    parser_commit.add_argument('node')
    parser_commit.set_defaults(func=commit)

    parser_commit_code = subparsers.add_parser('commit-code', aliases=['cc'], help='Stage and commit only the _c (code) directories.')
    parser_commit_code.add_argument('node', help='Path to the node whose _c dir you want to commit.')
    parser_commit_code.add_argument('-r', '--recursive', action='store_true', help='Recurse into all descendant nodes.')
    parser_commit_code.add_argument('-m', '--message', required=True, help='Commit message.')
    parser_commit_code.set_defaults(func=commit_code)


    parser_get = subparsers.add_parser('get', help='get output directory contents from origin repository')
    parser_get.add_argument('-r', '--recursive', action='store_true')
    parser_get.add_argument('node')
    parser_get.set_defaults(func=get)

    parser_get = subparsers.add_parser('status', help='print analysis tree status')
    parser_get.add_argument('-p', '--parseable', action='store_true', help='prints path <tab> status for each node')
    parser_get.add_argument('node', nargs='?', default='.')
    parser_get.set_defaults(func=pretty_print_status)

    parser_get = subparsers.add_parser('tree', help='print analysis tree')
    parser_get.add_argument('node', nargs='?', default='.')
    parser_get.set_defaults(func=print_tree)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.parse_args(['--help'])

if __name__ == '__main__':
    main()
