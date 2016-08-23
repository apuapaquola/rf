#!/usr/bin/env python
""" rf - A framework for collaborative computational research

    Copyright (C) 2015 Apua Paquola <apuapaquola@gmail.com>

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
import rflib

__author__ = 'Apua Paquola'


def run(args):
    """ Runs driver scripts throughout the tree
    :param args:
    :return:
    """
    rflib.run(node=args.node, recursive=args.recursive,
              verbose=args.verbose, dry_run=args.dry_run,
              docker_image=args.docker_image)


def drop(args):
    """Deletes the contents of machine dirs _m
    """
    rflib.drop(node=args.node, recursive=args.recursive, force=args.force)


def clone(args):
    """Clones a tree
    """
    rflib.clone(repository=args.repository, directory=args.directory)


def commit(args):
    """Commits human and machine dirs to git and git-annex
    """
    rflib.commit(node=args.node, recursive=args.recursive, message=args.message)


def get(args):
    """Fetches real machine data from origin repository
    :param args:
    :return:
    """
    rflib.get(node=args.node, recursive=args.recursive)


def create_node(args):
    """Create a new node
    :return:
    """
    rflib.create_node(node=args.node, custom_templates=args.custom_templates,
                      create_deps_folder=args.create_deps_folder,
                      make_commit=args.commit, root_node=args.root_node)


def init_repo(args):
    """Create a new node
    :return:
    """
    rflib.init_repo(node=args.node, annex=args.annex, make_commit=args.commit)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_run = subparsers.add_parser('run', help='run driver script')
    parser_run.add_argument('-n', '--dry-run', action='store_true')
    parser_run.add_argument('-v', '--verbose', action='store_true')
    parser_run.add_argument('-r', '--recursive', action='store_true')
    parser_run.add_argument('-d', '--docker-image')
    parser_run.add_argument('node')
    parser_run.set_defaults(func=run)

    parser_drop = subparsers.add_parser('drop', help='drop machine directory')
    parser_drop.add_argument('-r', '--recursive', action='store_true')
    parser_drop.add_argument('-f', '--force', action='store_true')
    parser_drop.add_argument('node')
    parser_drop.set_defaults(func=drop)

    parser_create_node = subparsers.add_parser('create_node',
                                               help='create a node with folders and empty files')
    parser_create_node.add_argument('-templates', '--custom_templates')
    parser_create_node.add_argument('-deps', '--create_deps_folder', action='store_true')
    parser_create_node.add_argument('-c', '--commit', action='store_true')
    parser_create_node.add_argument('-r', '--root_node', action='store_true')
    parser_create_node.add_argument('node')
    parser_create_node.set_defaults(func=create_node)

    parser_init_repo = subparsers.add_parser('init_repo',
                                             help='Start version control on folder')
    parser_init_repo.add_argument('-a', '--annex', action='store_true')
    parser_init_repo.add_argument('-c', '--commit', action='store_true')
    parser_init_repo.add_argument('node')
    parser_init_repo.set_defaults(func=init_repo)

    parser_clone = subparsers.add_parser('clone', help='clone an analysis tree')
    parser_clone.add_argument('repository')
    parser_clone.add_argument('directory')
    parser_clone.set_defaults(func=clone)

    parser_commit = subparsers.add_parser('commit', help='commit to git and git-annex')
    parser_commit.add_argument('-r', '--recursive', action='store_true')
    parser_commit.add_argument('-m', '--message', required=True)
    parser_commit.add_argument('node')
    parser_commit.set_defaults(func=commit)

    parser_get = subparsers.add_parser('get', help='get machine data')
    parser_get.add_argument('-r', '--recursive', action='store_true')
    parser_get.add_argument('node')
    parser_get.set_defaults(func=get)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.parse_args(['--help'])

if __name__ == '__main__':
    main()
