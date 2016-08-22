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

import os
import subprocess
import functools
import shutil

__author__ = 'Apua Paquola'


def is_ready_to_run(node):
    """Tests if a node is ready to run.

    Args:
        node: a directory (node)
    Returns:
        bool: True if the node is ready to run, i.e., if it has no _m/ dir
        and if there is an executable driver script at _h/
    """
    return node is not None and \
           os.path.isdir(node + '/_h') and \
           not os.path.exists(node + '/_m') and \
           os.access(node + '/_h/driver', os.X_OK)


def find_dependencies(node, recursive=False):
    """Finds the human directories _h/ in a subtree, and dependencies.

    Args:
        node (str): a node at the root of the tree.
        recursive (bool): whether to look at the entire tree recursively.

    Yields:
        (list, str): a tuple that contains a list of dependencies and a node,
        for each node of the tree that is ready to run.

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
            queue.extend(((child, xx) for xx in filter(os.path.isdir, \
                         (os.path.join(child, x) for x in os.listdir(child) \
                          if x not in ['_h', '_m']))))


def driver_script_command_native(node):
    assert(os.path.isdir(node))
    return '../_h/driver > nohup.out 2>&1'


def driver_script_command_docker(node, docker_image):
    """If the file node/_h/docker_driver exists, then a command called it is generated. Otherwise,
    a standard docker run call is generated using docker_image.

    Args:
        node: a node of the tree
        docker_image: name of docker image to use

    Returns:
        A driver script calling command

    """
    assert(os.path.isdir(node))
    if node is not None and \
        os.path.isdir(node + '/_h') and \
            os.access(node + '/_h/docker_driver', os.X_OK):
        return '../_h/docker_driver > nohup.out 2>&1'

    else:
        base_node = subprocess.check_output('git rev-parse --show-toplevel', shell=True).decode().rstrip()

        DOCKER_DRIVER_TEMPLATE = '''docker run -v '{base_node}':'{base_node}':ro ''' + \
                                 ''' -v '{node}/_m':'{node}/_m' '{docker_image}' ''' + \
                                 '''bash -c 'cd "{node}/_m" && ../_h/driver > nohup.out 2>&1' '''

        data = {'base_node': base_node, 'node': node, 'docker_image': docker_image}

        return DOCKER_DRIVER_TEMPLATE.format(**data)


def success_file(node):
    return node + '/_m/SUCCESS'


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
                # yield from nodes(child)
                # for support python 2,7
                for node in nodes(child):
                    yield node


def clone(repository, directory):
    """Clones a tree
    """
    subprocess.check_call(['git', 'clone', repository, directory])
    init_repo(directory)


def init_repo(node, annex=True, commit=True):
    """Init annex on node
    """

    os.chdir(node)
    subprocess.check_call(['git', 'init'])
    subprocess.check_call(['git', 'annex', 'init'])

    if commit:
        commit(node, recursive=False, message='Started the repo, commited using rf')


def create_node(node, custom_templates=None, create_deps_folder=True, commit=True):
    """Create rf folders and empty drivers
    """

    # Create Folders
    if not os.path.exists(node):
        os.makedirs(node)
    if not os.path.exists(node + '/_h'):
        os.makedirs(node + '/_h')
    if create_deps_folder and not os.path.exists(node + '/_h/dep'):
        os.makedirs(node + '/_h/dep')

    # 0o777 or stat.S_IXUSR see https://docs.python.org/2/library/stat.html
    driver_permissions = [0o754]

    templates = {'DRIVER': '''# Created with RF\n''' + \
                           '''echo 'running driver at {node}';\n''' + \
                           '''date > driver_output;\n''',
                 'README': '''# Created with RF\n''' + \
                           '''## rf - A framework for collaborative computational research\n''' + \
                           '''## About: https://github.com/apuapaquola/rf\n''' + \
                           '''## To install: pip install git+git://github.com/apuapaquola/rf.git\n''' + \
                           '''## To run: \n'''
                 }

    if custom_templates:
        templates = custom_templates

    if not os.path.isfile(node + '/_h/driver'):
        data = {'node': node[2:],
                'parent_node': os.path.abspath(node)}
        with open(node + '/_h/README.md', 'w') as readme:
            readme.write(templates['README'].format(**data))
        with open(node + '/_h/driver', 'w') as driver:
            driver.write(templates['DRIVER'].format(**data))
        for perm in driver_permissions:
            os.chmod(node + '/_h/driver', perm)

    if commit:
        commit(node, recursive=False, message='Started the node %s, commited using rf' % node)


def drop(node, recursive=False, force=False):
    """Deletes the contents of machine dirs _m
    """
    if recursive:
        nl = list(nodes(node))
    else:
        nl = [node]

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

        if force and os.path.isdir(x):
            shutil.rmtree(x)


def get(node, recursive=False):
    """Fetches real machine data from origin repository
    :param args:
    :return:
    """
    if recursive:
        nl = list(nodes(node))
    else:
        nl = [node]

    machine_dirs = [y for y in [os.path.join(x, '_m') for x in nl] if os.path.isdir(y)]

    subprocess.check_call(['git', 'annex', 'sync', '--no-push'])
    subprocess.check_call(['git', 'annex', 'get'] + machine_dirs)


def commit(node, recursive=False, message='commited using rf'):
    """Commits human and machine dirs to git and git-annex
    """
    if recursive:
        nl = list(nodes(node))
    else:
        nl = [node]

    machine_dirs = [y for y in [os.path.join(x, '_m') for x in nl] if os.path.isdir(y)]
    human_dirs = [y for y in [os.path.join(x, '_h') for x in nl] if os.path.isdir(y)]

    try:
        subprocess.check_call(['git', 'add'] + human_dirs)
        subprocess.check_call(['git', 'annex', 'add'] + machine_dirs)
        subprocess.check_call(['git', 'commit', '-m', message] + human_dirs + machine_dirs)
    except subprocess.CalledProcessError:
        raise


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

    RULE_STRING_TEMPLATE = '''.ONESHELL:\n''' + \
                           '''{success_file}: {dep_string}\n''' + \
                           '''\tset -o errexit -o pipefail\n''' + \
                           '''\techo -n "Start {node}: "; date --rfc-3339=seconds\n''' + \
                           '''\tmkdir {node}/_m\n''' + \
                           '''\tcd {node}/_m\n''' + \
                           '''\t{command}\n''' + \
                           '''\ttouch SUCCESS\n''' + \
                           '''\techo -n "End {node}: "; date --rfc-3339=seconds\n'''

    data = {'success_file': success_file(node), 'dep_string': dep_string,
            'node': node, 'command': command}
    return RULE_STRING_TEMPLATE.format(**data)


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

    # set -o errexit -o pipefail
    # works for bash, setting SHELL=/bin/bash in makefile
    makefile_string = 'SHELL=/bin/bash\n\n'
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


def run(node, recursive=False, verbose=True, dry_run=False, docker_image=None):
    """Implements rf run"""

    if docker_image is not None:
        dscf = functools.partial(driver_script_command_docker, docker_image=docker_image)
    else:
        dscf = driver_script_command_native

    rule_string_function = functools.partial(rule_string, driver_script_command_function=dscf)

    mf = makefile(find_dependencies(os.path.realpath(node), recursive), rule_string_function)

    if verbose:
        print(mf)
    if not dry_run:
        run_make(mf)
