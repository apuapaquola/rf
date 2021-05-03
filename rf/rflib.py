#!/usr/bin/env python
""" rf - A framework for collaborative data analysis

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

import os
import subprocess
import functools
import yaml

__author__ = 'Apuã Paquola, Ricardo S jacomini'
__email__ = "apuapaquola@gmail.com"
__version__ = '2.0.0'
__date__ = "April / 26 / 2021"
__status__ = "Development"


def is_ready_to_run(node):
    """Tests if a node is ready to run.

    Args:
        node: a directory (node)
    Returns:
        bool: True if the node is ready to run, i.e., if it has no _m/ dir and if there is an
         executable driver script at _h/ and there is no 'yield' file in _h
    """
    return node is not None\
        and os.path.isdir(node + '/_h')\
        and not os.path.exists(node + '/_m')\
        and not os.path.exists(node + '/_h/yield')\
        and os.access(node + '/_h/run', os.X_OK)


def find_dependencies(node, recursive):
    """Finds the human directories _h/ in a subtree, and dependencies.

    Args:
        node (str): a node at the root of the tree.
        recursive (bool): whether to look at the entire tree recursively.

    Yields:
        (list, str): a tuple that contains a list of dependencies and a node, for each node
         of the tree that is ready to run.

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

        if is_ready_to_run(os.path.realpath(child)) and belongs_to_tree(child, node):
            yield (dependencies, child)

        if recursive:
            queue.extend(((child, xx) for xx in filter(os.path.isdir,
                                                       (os.path.join(child, x) for x in os.listdir(child) if
                                                        x not in ['_h', '_m']))))


def driver_script_command_native(node):
    assert (os.path.isdir(node))
    return '../_h/run > nohup.out 2>&1'


def get_basedir():
    """Gets the root of the analysis tree. The one that contains the .git directory"""
    return subprocess.check_output('git rev-parse --show-toplevel', shell=True).decode().rstrip()


def get_config_parameter(key):
    """Gets a configuration parameter from the config file or from the defaults defined here

    :param key:
    :return:
    """

    defaults = {
        'always_use_docker': False,
        'default_docker_run_command':
            '''docker run -v '{basedir}':'{basedir}':ro -v '{node}/_m':'{node}/_m' '{container_image}' ''' +
            '''bash -c 'cd "{node}/_m" && ../_h/run > nohup.out 2>&1' ''',
        'default_singularity_run_command':
            '''singularity exec --bind '{mount}' '{container_image}' ''' +
            '''bash -c 'cd "{node}/_m" && ../_h/run > nohup.out 2>&1' '''
    }
    
    config = {}

    try:
        with open(get_basedir()+'/.cdaconfig', 'r') as f:
            config = yaml.load(f)
    except:
        pass

    if key in config:
        return config[key]
    elif key in defaults:
        return defaults[key]
    else:
        return None


def driver_script_command_container(node, container_image, storage):
    """If the file node/_h/container_run exists, then a command calling it is generated. Otherwise,
    a standard container run call is generated using container parameters.

    The standard container run call mounts the base directory (where .git is located) as read_only and
    current _m directory as read-write.

    Args:
        node: a node of the tree
        container: parameters of container

    Returns:
        A driver script calling command

    """
    assert (os.path.isdir(node))
         	
    if node is not None and \
            os.path.isdir(node + '/_h') and \
            os.access(node + '/_h/container_run', os.X_OK):
        return '../_h/container_run'
    elif '.sif' in container_image:
        return get_config_parameter('default_singularity_run_command').format(basedir=get_basedir(), node=node, mount=storage, container_image=container_image )
    else:
        return get_config_parameter('default_docker_run_command').format(basedir=get_basedir(), node=node, container_image=container_image)
        	


def success_file(node):
    return node + '/_m/SUCCESS'


def rule_string(dependencies, node, driver_script_command_function):
    """Generates a makefile rule for a node given its dependencies.

    Args:
        dependencies (list of str): list of nodes
        node (str): a tree node
        driver_script_command_function: function that generates a driver script call

    Returns:
        str: a makefile rule specifying how to generate the machine directory
            of the current node, given the its dependencies.
    """
    dep_string = ' '.join((success_file(x) for x in dependencies))

    command = driver_script_command_function(node)

    return '''.ONESHELL:
%s: %s
\tset -o errexit -o pipefail
\techo -n "Start %s: "; date --rfc-3339=seconds
\tmkdir %s/_m
\tcd %s/_m
\t%s
\ttouch SUCCESS
\techo -n "End %s: "; date --rfc-3339=seconds

''' % (success_file(node), dep_string, node, node, node, command, node)


def dependency_links(node):
    """Finds out the dependencies of a given node and yields them one by one.

    Args:
        node (str): a tree node.

    Yields:
        str: a node that is a dependency of node.

    """

    dep_dir = node + '/_h/dep'
    if os.path.isdir(dep_dir):
        for x in os.listdir(dep_dir):
            if os.path.islink(dep_dir + '/' + x) and os.path.isdir(dep_dir + '/' + x):
                yield os.path.realpath(dep_dir + '/' + x)


def belongs_to_tree(dirname, basedir):
    """Tests if a node belongs to a tree.

    Args:
        dirname: a directory (node)
        basedir: the root of the analysis tree
    Returns:
        bool: True if the node is under basedir.

    """
    assert os.path.isdir(dirname) and os.path.isdir(basedir)
    return (os.path.realpath(dirname) + '/').startswith(os.path.realpath(basedir) + '/')


def makefile(dependency_iter, rule_string_function):
    """Generates a makefile given a list of tuples specifying nodes and dependencies.

    Args:
        dependency_iter (iterable on list of tuples): output of find_human_dirs
        rule_string_function: a function that generates a rule string. See function rule_string.

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

    makefile_string = 'all: ' + ' '.join(map(success_file, dependency_set.union(child_set))) + \
                      '\n\n' + makefile_string

    return makefile_string


def run_make(makefile_string):
    """Runs make on makefile_string
    :param makefile_string:
    :return:
    """
    p = subprocess.Popen(['make', '--keep-going', '--silent', '-f', '-'], stdin=subprocess.PIPE)

    p.stdin.write(makefile_string.encode())
    p.stdin.close()
    p.wait()


def run(args):
    """Implements rf run arguments from command line"""

    if args.container_image is not None or get_config_parameter('always_use_container'):
        dscf = functools.partial(driver_script_command_container, container_image=args.container_image, storage=args.storage)
    else:
        dscf = driver_script_command_native

    rule_string_function = functools.partial(rule_string, driver_script_command_function=dscf)
    
    mf = makefile(find_dependencies(os.path.realpath(args.node), args.recursive), rule_string_function)

    if args.verbose:
        print(mf)
    if not args.dry_run:
        run_make(mf)
