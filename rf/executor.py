"""Driver execution and the current Make-based workflow backend."""

import argparse
import json
import os
import shlex
import shutil
import socket
import subprocess
import sys
import uuid
from pathlib import Path

from . import state
from . import workflow


class NodeExecutionError(RuntimeError):
    """Raised when a node's driver script does not complete successfully."""

    def __init__(self, node, returncode, message=None):
        self.node = os.fspath(node)
        self.returncode = returncode
        if message is None:
            message = 'Node %s failed with exit code %s' % (self.node, returncode)
        super().__init__(message)


def execute_node(node):
    """Run one node and record RUNNING, SUCCESS, or FAILURE in _o."""
    node = Path(node).resolve()
    driver = node / '_c' / 'run'
    output = node / '_o'

    if not driver.is_file() or not os.access(driver, os.X_OK):
        raise NodeExecutionError(
            node, None, 'Node %s has no executable _c/run script' % node)
    if output.exists():
        raise NodeExecutionError(
            node, None, 'Node %s cannot run while _o exists (%s)' %
            (node, state.output_state(node).value))

    output.mkdir()
    record = {
        'schema_version': 1,
        'run_id': str(uuid.uuid4()),
        'started_at': state.utc_now(),
        'hostname': socket.gethostname(),
        'pid': os.getpid(),
    }
    state.write_json_atomic(
        output / state.MARKERS[state.OutputState.RUNNING],
        record,
    )

    try:
        with (output / 'nohup.out').open('wb') as log:
            result = subprocess.run(
                [str(driver)], cwd=output, stdout=log,
                stderr=subprocess.STDOUT, check=False)
    except BaseException as error:
        state.finish_execution(
            output, state.MARKERS[state.OutputState.FAILURE], record,
            finished_at=state.utc_now(),
            exit_code=130 if isinstance(error, KeyboardInterrupt) else None,
            error='%s: %s' % (type(error).__name__, error))
        raise

    if result.returncode != 0:
        state.finish_execution(
            output, state.MARKERS[state.OutputState.FAILURE], record,
            finished_at=state.utc_now(), exit_code=result.returncode)
        raise NodeExecutionError(node, result.returncode)

    state.finish_execution(
        output, state.MARKERS[state.OutputState.SUCCESS], record,
        finished_at=state.utc_now(), exit_code=0)


def drop(args):
    """Delete output directories for the requested nodes."""
    selected_nodes = (
        list(workflow.nodes(args.node)) if args.recursive else [args.node]
    )
    output_dirs = [os.path.join(node, '_o') for node in selected_nodes]

    for output_dir in output_dirs:
        assert output_dir.endswith('_o')
        assert not output_dir.endswith('_c')

        if not os.path.isdir(output_dir):
            continue

        try:
            subprocess.check_call(['git', 'rm', '-r', output_dir])
        except subprocess.CalledProcessError:
            pass

        if args.force and os.path.isdir(output_dir):
            shutil.rmtree(output_dir)


def driver_script_command(node):
    """Generate the command used by a Make recipe to execute one node."""
    assert (
        os.path.isdir(node)
        and os.path.isdir(node + '/_c')
        and os.access(node + '/_c/run', os.X_OK)
    )
    return ' '.join(shlex.quote(part) for part in [
        sys.executable, '-m', 'rf.executor', node,
    ])


def rule_string(dependencies, node):
    """Generate a Make rule for one runnable node."""
    dep_string = ' '.join(
        workflow.success_file(dependency) for dependency in dependencies
    )
    command = driver_script_command(node)

    return '''.ONESHELL:
%s: %s
\tset -o errexit -o pipefail
\techo -n "Start %s: "; date --rfc-3339=seconds
\t%s
\techo -n "End %s: "; date --rfc-3339=seconds

''' % (
        workflow.success_file(node), dep_string, node, command, node,
    )


def _failure_exit_code(node):
    """Read an exit code from a FAILURE marker when one is available."""
    try:
        with open(
                os.path.join(node, '_o', 'FAILURE'),
                encoding='utf-8') as marker:
            return json.load(marker).get('exit_code')
    except (OSError, ValueError, AttributeError):
        return None


def blocked_rule_string(node):
    """Generate a failing Make rule that explains why a node is blocked."""
    output_state = state.output_state(os.path.realpath(node))
    detail = {
        state.OutputState.RUNNING: 'running',
        state.OutputState.FAILURE: 'failed',
        state.OutputState.INCOMPLETE: 'incomplete',
        state.OutputState.INVALID: 'invalid',
    }[output_state]
    if output_state == state.OutputState.FAILURE:
        exit_code = _failure_exit_code(node)
        if exit_code is not None:
            detail += ' (exit code %s)' % exit_code

    message = 'Node %s is %s; preserve or remove _o before retrying' % (
        node, detail)
    return """.ONESHELL:
%s:
\tprintf 'Blocked: %%s\\n' %s >&2
\texit 1

""" % (workflow.success_file(node), shlex.quote(message))


def makefile(dependency_iter):
    """Generate a Makefile from dependency and node tuples."""
    dependency_set = set()
    child_set = set()

    makefile_string = ''
    for dependencies, child in dependency_iter:
        output_state = state.output_state(os.path.realpath(child))
        if output_state == state.OutputState.ABSENT:
            makefile_string += rule_string(dependencies, child)
        elif output_state != state.OutputState.SUCCESS:
            makefile_string += blocked_rule_string(child)

        dependency_set.update(dependencies)
        child_set.add(child)

    for node in dependency_set.difference(child_set):
        output_state = state.output_state(os.path.realpath(node))
        if output_state == state.OutputState.ABSENT:
            makefile_string += rule_string([], node)
        elif output_state != state.OutputState.SUCCESS:
            makefile_string += blocked_rule_string(node)

    targets = dependency_set.union(child_set)
    return (
        'SHELL := /bin/bash\n\nall: '
        + ' '.join(map(workflow.success_file, targets))
        + '\n\n'
        + makefile_string
    )


def run_make(makefile_string):
    """Run Make with a generated Makefile supplied on standard input."""
    subprocess.run(
        ['make', '--keep-going', '--silent', '-f', '-'],
        input=makefile_string.encode(),
        check=True,
    )


def run(args):
    """Run requested nodes in dependency order."""
    makefile_string = makefile(workflow.find_dependencies(
        os.path.realpath(args.node),
        args.recursive,
    ))
    if args.verbose:
        print(makefile_string)
    if not args.dry_run:
        run_make(makefile_string)


def main():
    """Internal entry point used by generated Makefile recipes."""
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
