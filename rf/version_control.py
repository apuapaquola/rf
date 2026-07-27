"""Git and Git Annex operations for analysis trees."""

import os
import subprocess
import sys

from .workflow import nodes


def get_basedir():
    """Return the root of the current Git repository."""
    return subprocess.check_output(
        'git rev-parse --show-toplevel',
        shell=True,
    ).decode().rstrip()


def clone(args):
    """Clone an analysis tree and initialize its Git Annex metadata."""
    subprocess.check_call(['git', 'clone', args.repository, args.directory])
    os.chdir(args.directory)
    subprocess.check_call(['git', 'annex', 'init'])
    subprocess.check_call(['git', 'annex', 'sync', '--no-push'])


def commit(args):
    """Commit code and output directories to Git and Git Annex."""
    selected_nodes = (
        list(nodes(args.node)) if args.recursive else [args.node]
    )
    output_dirs = [
        os.path.join(node, '_o') for node in selected_nodes
        if os.path.isdir(os.path.join(node, '_o'))
    ]
    code_dirs = [
        os.path.join(node, '_c') for node in selected_nodes
        if os.path.isdir(os.path.join(node, '_c'))
    ]

    subprocess.check_call(['git', 'add'] + code_dirs)
    subprocess.check_call(['git', 'annex', 'add'] + output_dirs)
    subprocess.check_call(
        ['git', 'commit', '-m', args.message] + code_dirs + output_dirs
    )


def commit_code(args):
    """Commit only code directories under the requested nodes."""
    selected_nodes = (
        list(nodes(args.node)) if args.recursive else [args.node]
    )
    code_dirs = [
        os.path.join(node, '_c') for node in selected_nodes
        if os.path.isdir(os.path.join(node, '_c'))
    ]

    if not code_dirs:
        print('No _c directories found to commit.', file=sys.stderr)
        return

    subprocess.check_call(['git', 'add'] + code_dirs)
    subprocess.check_call(
        ['git', 'commit', '-m', args.message] + code_dirs
    )


def get(args):
    """Fetch output-directory contents from the origin repository."""
    selected_nodes = (
        list(nodes(args.node)) if args.recursive else [args.node]
    )
    output_dirs = [
        os.path.join(node, '_o') for node in selected_nodes
        if os.path.isdir(os.path.join(node, '_o'))
    ]

    subprocess.check_call(['git', 'annex', 'sync', '--no-push'])
    subprocess.check_call(['git', 'annex', 'get'] + output_dirs)
