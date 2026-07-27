"""Command-line interface for rf."""

import argparse
import re
import subprocess

from . import executor
from . import version_control
from . import workflow


def pretty_print_status(args):
    """Print the status of all nodes in a subtree."""
    command = ['tree', '--noreport', '-d', '-I', '_c|_o', args.node]
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    max_length = max(len(line.decode().rstrip()) for line in process.stdout)

    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    path = []
    for line in process.stdout:
        rendered = line.decode().rstrip()
        match = re.search('(─ )?([^─]*)$', rendered)
        position = match.start(2) // 4
        del path[position:]
        path.append(match.group(2))
        node = '/'.join(path)
        status = workflow.node_status(node)
        if args.parseable:
            print(node, status, sep='\t')
        else:
            padding = ' ' * (max_length - len(rendered) + 13 - len(status))
            print(rendered, padding, status)


def print_tree(args):
    """Print the directory tree under a node."""
    subprocess.check_call([
        'tree', '--noreport', '-d', '-I', '_c|_o', args.node,
    ])


def build_parser():
    """Build the rf argument parser."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    run_parser = subparsers.add_parser('run', help='run driver script')
    run_parser.add_argument('-n', '--dry-run', action='store_true')
    run_parser.add_argument('-v', '--verbose', action='store_true')
    run_parser.add_argument('-r', '--recursive', action='store_true')
    run_parser.add_argument('node')
    run_parser.set_defaults(func=executor.run)

    drop_parser = subparsers.add_parser('drop', help='drop output directory')
    drop_parser.add_argument('-r', '--recursive', action='store_true')
    drop_parser.add_argument('-f', '--force', action='store_true')
    drop_parser.add_argument('node')
    drop_parser.set_defaults(func=executor.drop)

    clone_parser = subparsers.add_parser(
        'clone', help='clone an analysis tree')
    clone_parser.add_argument('repository')
    clone_parser.add_argument('directory')
    clone_parser.set_defaults(func=version_control.clone)

    commit_parser = subparsers.add_parser(
        'commit', help='commit to git and git-annex')
    commit_parser.add_argument('-r', '--recursive', action='store_true')
    commit_parser.add_argument('-m', '--message', required=True)
    commit_parser.add_argument('node')
    commit_parser.set_defaults(func=version_control.commit)

    commit_code_parser = subparsers.add_parser(
        'commit-code',
        aliases=['cc'],
        help='stage and commit only the _c directories',
    )
    commit_code_parser.add_argument('node')
    commit_code_parser.add_argument(
        '-r', '--recursive', action='store_true')
    commit_code_parser.add_argument('-m', '--message', required=True)
    commit_code_parser.set_defaults(func=version_control.commit_code)

    get_parser = subparsers.add_parser(
        'get', help='get output directory contents from origin repository')
    get_parser.add_argument('-r', '--recursive', action='store_true')
    get_parser.add_argument('node')
    get_parser.set_defaults(func=version_control.get)

    status_parser = subparsers.add_parser(
        'status', help='print analysis tree status')
    status_parser.add_argument(
        '-p', '--parseable', action='store_true',
        help='print path <tab> status for each node')
    status_parser.add_argument('node', nargs='?', default='.')
    status_parser.set_defaults(func=pretty_print_status)

    tree_parser = subparsers.add_parser(
        'tree', help='print analysis tree')
    tree_parser.add_argument('node', nargs='?', default='.')
    tree_parser.set_defaults(func=print_tree)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.parse_args(['--help'])
