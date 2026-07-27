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
import json
import os
import shlex
import socket
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

__author__ = 'Apuã Paquola'


class OutputState(Enum):
    """The state represented by a node's output directory."""

    ABSENT = 'absent'
    RUNNING = 'running'
    SUCCESS = 'success'
    FAILURE = 'failure'
    INCOMPLETE = 'incomplete'
    INVALID = 'invalid'


class NodeExecutionError(RuntimeError):
    """Raised when a node's driver script does not complete successfully."""

    def __init__(self, node, returncode, message=None):
        self.node = os.fspath(node)
        self.returncode = returncode
        if message is None:
            message = 'Node %s failed with exit code %s' % (self.node, returncode)
        super().__init__(message)


_MARKERS = {
    OutputState.RUNNING: 'RUNNING',
    OutputState.SUCCESS: 'SUCCESS',
    OutputState.FAILURE: 'FAILURE',
}


def output_state(node):
    """Return the state represented by a node's ``_o`` directory."""
    output = Path(node) / '_o'
    if not output.exists():
        return OutputState.ABSENT
    if not output.is_dir():
        return OutputState.INVALID

    states = [
        state for state, marker in _MARKERS.items()
        if (output / marker).exists()
    ]
    if len(states) > 1:
        return OutputState.INVALID
    if not states:
        return OutputState.INCOMPLETE
    return states[0]


def _utc_now():
    return datetime.now(timezone.utc).isoformat()


def _write_json_atomic(path, data):
    """Write JSON to path without exposing a partially-written marker."""
    path = Path(path)
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(
                mode='w', encoding='utf-8', dir=path.parent,
                prefix='.rf-state-', delete=False) as temporary:
            temporary_name = temporary.name
            json.dump(data, temporary, sort_keys=True)
            temporary.write('\n')
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, path)
        temporary_name = None
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass


def _finish_execution(output, marker, record, **updates):
    """Atomically replace RUNNING with the final state marker."""
    record.update(updates)
    running = output / _MARKERS[OutputState.RUNNING]
    _write_json_atomic(running, record)
    os.replace(running, output / marker)


def execute_node(node):
    """Run one node and record RUNNING, SUCCESS, or FAILURE in ``_o``."""
    node = Path(node).resolve()
    driver = node / '_c' / 'run'
    output = node / '_o'

    if not driver.is_file() or not os.access(driver, os.X_OK):
        raise NodeExecutionError(
            node, None, 'Node %s has no executable _c/run script' % node)
    if output.exists():
        raise NodeExecutionError(
            node, None, 'Node %s cannot run while _o exists (%s)' %
            (node, output_state(node).value))

    output.mkdir()
    record = {
        'schema_version': 1,
        'run_id': str(uuid.uuid4()),
        'started_at': _utc_now(),
        'hostname': socket.gethostname(),
        'pid': os.getpid(),
    }
    _write_json_atomic(output / _MARKERS[OutputState.RUNNING], record)

    try:
        with (output / 'nohup.out').open('wb') as log:
            result = subprocess.run(
                [str(driver)], cwd=output, stdout=log,
                stderr=subprocess.STDOUT, check=False)
    except BaseException as error:
        _finish_execution(
            output, _MARKERS[OutputState.FAILURE], record,
            finished_at=_utc_now(),
            exit_code=130 if isinstance(error, KeyboardInterrupt) else None,
            error='%s: %s' % (type(error).__name__, error))
        raise

    if result.returncode != 0:
        _finish_execution(
            output, _MARKERS[OutputState.FAILURE], record,
            finished_at=_utc_now(), exit_code=result.returncode)
        raise NodeExecutionError(node, result.returncode)

    _finish_execution(
        output, _MARKERS[OutputState.SUCCESS], record,
        finished_at=_utc_now(), exit_code=0)


def is_computational_node(node):
    """Return whether node defines a driver that participates in the graph."""
    return node is not None\
        and os.path.isdir(node + '/_c')\
        and not os.path.exists(node + '/_c/yield')\
        and os.access(node + '/_c/run', os.X_OK)


def is_ready_to_run(node):
    """Tests if a node is ready to run.

    Args:
        node: a directory (node)
    Returns:
        bool: True if the node is ready to run, i.e., if it has no _o/ dir and if there is an
         executable driver script at _c/ and there is no 'yield' file in _c
    """
    return is_computational_node(node)\
        and output_state(node) == OutputState.ABSENT


def find_dependencies(node, recursive):
    """Finds the code directories _c/ in a subtree, and dependencies.

    Args:
        node (str): a node at the root of the tree.
        recursive (bool): whether to look at the entire tree recursively.

    Yields:
        (list, str): a tuple containing a node's dependencies and the node.
        Nodes in terminal or blocked states are included so make can report
        their state and block descendants.

    """
    assert os.path.isdir(node)
    queue = [(None, node)]
    while queue:
        (parent, child) = queue.pop(0)

        l = list(dependency_links(child))
        dependencies = [
            x for x in [parent] + l
            if x is not None
            and belongs_to_tree(x, node)
            and is_computational_node(os.path.realpath(x))
        ]

        if (is_computational_node(os.path.realpath(child))
                and belongs_to_tree(child, node)):
            yield (dependencies, child)

        if recursive:
            queue.extend(((child, xx) for xx in filter(os.path.isdir,
                                                       (os.path.join(child, x) for x in os.listdir(child) if
                                                        x not in ['_c', '_o']))))

            

def driver_script_command(node):
    """Generate a command to call the driver script. This command is
    to be included in the makefile.
    """

    assert (os.path.isdir(node) and os.path.isdir(node + '/_c') and os.access(node + '/_c/run', os.X_OK))
    return ' '.join(shlex.quote(part) for part in
                    [sys.executable, os.path.abspath(__file__), node])

    
def get_basedir():
    """Gets the root of the analysis tree. The one that contains the .git directory"""
    return subprocess.check_output('git rev-parse --show-toplevel', shell=True).decode().rstrip()


def success_file(node):
    return node + '/_o/SUCCESS'


def rule_string(dependencies, node):
    """Generates a makefile rule for a node given its dependencies.

    Args:
        dependencies (list of str): list of nodes
        node (str): a tree node

    Returns:
        str: a makefile rule specifying how to generate the machine directory
            of the current node, given the its dependencies.
    """
    dep_string = ' '.join((success_file(x) for x in dependencies))

    command = driver_script_command(node)

    return '''.ONESHELL:
%s: %s
\tset -o errexit -o pipefail
\techo -n "Start %s: "; date --rfc-3339=seconds
\t%s
\techo -n "End %s: "; date --rfc-3339=seconds

''' % (success_file(node), dep_string, node, command, node)


def _failure_exit_code(node):
    """Read an exit code from a FAILURE marker when one is available."""
    try:
        with open(os.path.join(node, '_o', 'FAILURE'), encoding='utf-8') as marker:
            return json.load(marker).get('exit_code')
    except (OSError, ValueError, AttributeError):
        return None


def blocked_rule_string(node):
    """Generate a failing make rule that explains why a node is blocked."""
    state = output_state(os.path.realpath(node))
    detail = {
        OutputState.RUNNING: 'running',
        OutputState.FAILURE: 'failed',
        OutputState.INCOMPLETE: 'incomplete',
        OutputState.INVALID: 'invalid',
    }[state]
    if state == OutputState.FAILURE:
        exit_code = _failure_exit_code(node)
        if exit_code is not None:
            detail += ' (exit code %s)' % exit_code

    message = 'Node %s is %s; preserve or remove _o before retrying' % (
        node, detail)
    return """.ONESHELL:
%s:
\tprintf 'Blocked: %%s\\n' %s >&2
\texit 1

""" % (success_file(node), shlex.quote(message))


def dependency_links(node):
    """Finds out the dependencies of a given node and yields them one by one.

    Args:
        node (str): a tree node.

    Yields:
        str: a node that is a dependency of node.

    """

    dep_dir = node + '/_c/dep'
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


def makefile(dependency_iter):
    """Generates a makefile given a list of tuples specifying nodes and dependencies.

    Args:
        dependency_iter (iterable on list of tuples): output of find_dependencies

    Returns:
        str: a makefile

    """
    dependency_set = set()
    child_set = set()

    makefile_string = ''
    for (dependencies, child) in dependency_iter:
        state = output_state(os.path.realpath(child))
        if state == OutputState.ABSENT:
            makefile_string += rule_string(dependencies, child)
        elif state != OutputState.SUCCESS:
            makefile_string += blocked_rule_string(child)

        for p in dependencies:
            dependency_set.add(p)

        child_set.add(child)

    for node in dependency_set.difference(child_set):
        state = output_state(os.path.realpath(node))
        if state == OutputState.ABSENT:
            makefile_string += rule_string([], node)
        elif state != OutputState.SUCCESS:
            makefile_string += blocked_rule_string(node)

    makefile_string = 'SHELL := /bin/bash\n\nall: ' + \
                      ' '.join(map(success_file, dependency_set.union(child_set))) + \
                      '\n\n' + makefile_string

    return makefile_string


def run_make(makefile_string):
    """Runs make on makefile_string
    :param makefile_string:
    :return:
    """
    subprocess.run(
        ['make', '--keep-going', '--silent', '-f', '-'],
        input=makefile_string.encode(),
        check=True,
    )


def run(args):
    """Implements rf run
    arguments from command line"""

    mf = makefile(find_dependencies(os.path.realpath(args.node), args.recursive))
    if args.verbose:
        print(mf)
    if not args.dry_run:
        run_make(mf)


def main():
    """Internal entry point used by generated makefile recipes."""
    parser = argparse.ArgumentParser()
    parser.add_argument('node')
    args = parser.parse_args()
    try:
        execute_node(args.node)
    except NodeExecutionError as error:
        print(error, file=sys.stderr)
        return error.returncode if error.returncode is not None else 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
