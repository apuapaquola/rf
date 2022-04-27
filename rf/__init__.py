# -*- coding: utf-8 -*-

#!/usr/bin/env python
""" rf - A Reproducibility Framework (RF) for collaborative data analysis

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

__author__ = 'Apuã Paquola, Ricardo S jacomini'
__email__ = "apuapaquola@gmail.com"
__version__ = '0.2.1'
__date__ = "April / 26 / 2022"
__status__ = "Development"


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
        if x not in ['_h', '_m', '.git']:
            child = os.path.join(parent, x)
            if os.path.isdir(child):
                yield from nodes(child)

def sbatch(args):
    """ Runs slurm scripts throughout the tree
    :param args:
    :return:
    """
    rflib.sbatch(args)

def run(args):
    """ Runs driver scripts throughout the tree
    :param args:
    :return:
    """
    rflib.run(args)


def drop(args):
    """Deletes the contents of machine dirs _m
    """
    if args.recursive:
        nl = list(nodes(args.node))
    else:
        nl = [args.node]

    dirs = [os.path.join(x, '_m') for x in nl]

    for x in dirs:
        assert x.endswith('_m')
        assert not x.endswith('_h')

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
    """Commits human and machine dirs to git and git-annex
    """
    if args.recursive:
        nl = list(nodes(args.node))
    else:
        nl = [args.node]

    machine_dirs = [y for y in [os.path.join(x, '_m') for x in nl] if os.path.isdir(y)]
    human_dirs = [y for y in [os.path.join(x, '_h') for x in nl] if os.path.isdir(y)]

    try:
        subprocess.check_call(['git', 'add'] + human_dirs)
        subprocess.check_call(['git', 'annex', 'add'] + machine_dirs)
        subprocess.check_call(['git', 'commit', '-m', args.message] + human_dirs + machine_dirs)
    except subprocess.CalledProcessError:
        raise


def get(args):
    """Fetches contents of machine directories from origin repository
    :param args:
    :return:
    """
    if args.recursive:
        nl = list(nodes(args.node))
    else:
        nl = [args.node]

    machine_dirs = [y for y in [os.path.join(x, '_m') for x in nl] if os.path.isdir(y)]

    subprocess.check_call(['git', 'annex', 'sync', '--no-push'])
    subprocess.check_call(['git', 'annex', 'get'] + machine_dirs)


def node_status(node):
    """Returns node status"""
    if not os.path.isdir(node + '/_h'):
        return 'no _h'
    elif os.path.exists(node + '/_h/run') and os.path.exists(node + '/_h/yield'):
        return 'run/yield'
    elif os.path.exists(node + '/_h/yield'):
        return 'yield'
    elif not (os.path.exists(node + '/_h/run') and os.access(node + '/_h/run', os.X_OK)):
        return 'no run script'
    elif not os.path.isdir(node + '/_m'):
        return 'ready to run'
    elif os.path.exists(node + '/_m/SUCCESS'):
        return 'done'
    else:
        return 'incomplete'


def pretty_print_status(args):
    """Prints status of all nodes in a subtree
    """
    command = ['tree', '--noreport', '-d', '-I', '_h|_m'] + [args.node]
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
    subprocess.check_call(['tree', '--noreport', '-d', '-I', '_h|_m'] + [args.node])


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_run = subparsers.add_parser('run', help='run driver script')
    parser_run.add_argument('-n', '--dry-run', action='store_true')
    parser_run.add_argument('-v', '--verbose', action='store_true')
    parser_run.add_argument('-r', '--recursive', action='store_true')
    parser_run.add_argument('--container_image', help='Singularity (.sif) or Docker Container')
    parser_run.add_argument('--volume', help='Bind mount a volume')
    parser_run.add_argument('node')
    parser_run.set_defaults(func=run)

    parser_sbatch = subparsers.add_parser('sbatch', help='Submits a batch script to Slurm')
    parser_sbatch.add_argument('-o', '--options', action='store_true', help='sbatch arguments')
    parser_sbatch.add_argument('-v', '--verbose', action='store_true')
    parser_sbatch.add_argument('-r', '--recursive', action='store_true')
    parser_sbatch.add_argument('node')
    parser_sbatch.set_defaults(func=sbatch)

    parser_drop = subparsers.add_parser('drop', help='drop machine directory')
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

    parser_get = subparsers.add_parser('get', help='get machine directory contents from origin repository')
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
