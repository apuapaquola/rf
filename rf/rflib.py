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
import os
import subprocess
import functools

__author__ = 'Apua Paquola'


def is_ready_to_run(node):
    """Tests if a node is ready to run.

    Args:
        node: a directory (node)
    Returns:
        bool: True if the node is ready to run, i.e., if it has no _m/ dir and if there is an executable driver script at _h/
    """
    return node is not None and \
           os.path.isdir(node + '/_h') and \
           not os.path.exists(node + '/_m') and \
           os.access(node + '/_h/driver', os.X_OK)


def find_dependencies(node, recursive):
    """Finds the human directories _h/ in a subtree, and dependencies.

    Args:
        node (str): a node at the root of the tree.
        recursive (bool): whether to look at the entire tree recursively.

    Yields:
        (list, str): a tuple that contains a list of dependencies and a node, for each node of the tree that is ready to run.

    """
    assert os.path.isdir(node)
    queue = [(None, node)]
    while queue:
        (parent, child) = queue.pop(0)

        l = list(dependency_links(child))
        dependencies = [x for x in [parent] + l
                        if x is not None and
                        is_ready_to_run(os.path.realpath(x)) and
                        belongs_to_tree(x, node)]

        if is_ready_to_run(os.path.realpath(child)) and \
           belongs_to_tree(child, node):
            yield (dependencies, child)

        if recursive:
            queue.extend(((child, xx) for xx in filter(os.path.isdir, (os.path.join(child,x) for x in os.listdir(child) if x not in ['_h','_m']))))


def nohup_out(node):
    return node + '/_m/nohup.out'


def driver_script_command_native():
    return '../_h/driver > nohup.out 2>&1'


def driver_script_command_docker(node, docker_image):
    """
    If the file node/_h/docker_driver exists, then a command called it is generated. Otherwise,
    a standard docker run call is generated using docker_image.

    Args:
        node: a node of the tree
        docker_image: name of docker image to use

    Returns:
        A driver script calling command

    """
    if node is not None and \
        os.path.isdir(node + '/_h') and \
            os.access(node + '/_h/docker_driver', os.X_OK):
        return '../_h/docker_driver > nohup.out 2>&1'

    else:
        base_node = subprocess.check_output('git rev-parse --show-toplevel', shell=True).decode().rstrip()

        return ('''docker run -v '%s':'%s':ro -v '%s/_m':'%s/_m' '%s' ''' +
                '''bash -c 'cd "%s/_m" && ../_h/driver > nohup.out 2>&1' ''') % \
                (base_node, base_node, node, node, docker_image, node)




def rule_string_native(dependencies, node):
    """Generates a makefile rule for a node given its dependencies.

    Args:
        dependencies (list of str): list of nodes
        node (str): the base directory of the node

    Returns:
        str: a makefile rule specifying how to generate the machine directory
            of the current node, given the its dependencies.
    """

    dep_string = ' '.join((nohup_out(x) for x in dependencies))
    return '''.ONESHELL:
%s: %s
\tdate
\tmkdir %s/_m
\tcd %s/_m
\t../_h/driver > nohup.out 2>&1
\tdate

''' % (nohup_out(node), dep_string, node, node)


def rule_string_docker(dependencies, node, docker_image):
    """Generates a makefile rule for a node given its dependencies.

    Args:
        dependencies (list of str): list of nodes
        node (str): the base directory of the node
        docker_image (str): name of docker image to use

    Returns:
        str: a makefile rule specifying how to generate the machine directory
            of the current node, given the its dependencies.
    """
    dep_string = ' '.join((nohup_out(x) for x in dependencies))

    command = driver_script_command_docker(node, docker_image)

    return '''.ONESHELL:
%s: %s
\tdate
\tmkdir %s/_m
\tcd %s/_m
\t%s
\tdate

''' % (nohup_out(node), dep_string, node, node, command)


def dependency_links(node):
    """Finds out the dependencies of a given node and yields them one by one.

    Args:
        node (str): a tree node.

    Yields:
        str: a node that is a dependency of node.

    """

    depdir = node+'/_h/dep'
    if os.path.isdir(depdir):
        for x in os.listdir(depdir):
            if os.path.islink(depdir+'/'+x) and os.path.isdir(depdir+'/'+x):
                yield os.path.realpath(depdir+'/'+x)


def belongs_to_tree(dirname, basedir):
    """Tests if a node belongs to a tree.

    Args:
        dirname (str): a directory (node)
    Returns:
        bool: True if the node is under basedir.

    """
    assert os.path.isdir(dirname) and os.path.isdir(basedir)
    return (os.path.realpath(dirname)+'/').startswith(os.path.realpath(basedir)+'/')


def makefile(dependency_iter, rule_string_function):
    """Generates a makefile given a list of tuples specifying nodes and dependencies.

    Args:
        dependency_iter (iterable on list of tuples): output of find_human_dirs
    Returns:
        str: a makefile

    """
    dependency_set = set()
    child_set = set()

    makefile_string = ''
    for (dependencies, child) in dependency_iter:
        makefile_string += rule_string_function(dependencies, child)

        for p in dependencies:
            dependency_set.add(p)

        child_set.add(child)

    for node in dependency_set.difference(child_set):
        makefile_string += rule_string_function([], node)

    makefile_string = 'all: ' + ' '.join(map(nohup_out, dependency_set.union(child_set))) + \
               '\n\n' + makefile_string

    return makefile_string


def run_make(makefile_string):
    """Runs make on makefile_string
    :param makefile_string:
    :return:
    """
    p = subprocess.Popen(['make', '-f', '-'], stdin=subprocess.PIPE)

    p.stdin.write(makefile_string.encode())
    p.stdin.close()
    p.wait()


def run(args):
    """Implements rf run
    arguments from command line"""

    if args.docker_image is not None:
        rule_string_function = functools.partial(rule_string_docker, docker_image=args.docker_image)
    else:
        rule_string_function = rule_string_native

    mf = makefile(find_dependencies(os.path.realpath(args.node), args.recursive), rule_string_function)
    if args.verbose:
        print(mf)
    if not args.dry_run:
        run_make(mf)


