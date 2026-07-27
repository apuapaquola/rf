"""Analysis-tree traversal, dependency discovery, and node status."""

import os

from .state import OutputState, output_state


def nodes(parent):
    """Yield every node under a directory tree."""
    assert os.path.isdir(parent)
    yield parent
    for name in os.listdir(parent):
        if name not in ['_c', '_o', '.git']:
            child = os.path.join(parent, name)
            if os.path.isdir(child):
                yield from nodes(child)


def is_computational_node(node):
    """Return whether node defines a driver that participates in the graph."""
    return node is not None\
        and os.path.isdir(node + '/_c')\
        and not os.path.exists(node + '/_c/yield')\
        and os.access(node + '/_c/run', os.X_OK)


def is_ready_to_run(node):
    """Return whether a computational node has no output yet."""
    return is_computational_node(node)\
        and output_state(node) == OutputState.ABSENT


def find_dependencies(node, recursive):
    """Yield dependencies and nodes participating in an analysis tree."""
    assert os.path.isdir(node)
    queue = [(None, node)]
    while queue:
        parent, child = queue.pop(0)

        links = list(dependency_links(child))
        dependencies = [
            dependency for dependency in [parent] + links
            if dependency is not None
            and belongs_to_tree(dependency, node)
            and is_computational_node(os.path.realpath(dependency))
        ]

        if (is_computational_node(os.path.realpath(child))
                and belongs_to_tree(child, node)):
            yield dependencies, child

        if recursive:
            queue.extend(
                (child, descendant)
                for descendant in filter(
                    os.path.isdir,
                    (os.path.join(child, name)
                     for name in os.listdir(child)
                     if name not in ['_c', '_o'])
                )
            )


def dependency_links(node):
    """Yield dependencies referenced by symlinks in a node's _c/dep."""
    dep_dir = node + '/_c/dep'
    if os.path.isdir(dep_dir):
        for name in os.listdir(dep_dir):
            dependency = dep_dir + '/' + name
            if os.path.islink(dependency) and os.path.isdir(dependency):
                yield os.path.realpath(dependency)


def belongs_to_tree(dirname, basedir):
    """Return whether dirname is contained by basedir."""
    assert os.path.isdir(dirname) and os.path.isdir(basedir)
    return (os.path.realpath(dirname) + '/').startswith(
        os.path.realpath(basedir) + '/'
    )


def success_file(node):
    return node + '/_o/SUCCESS'


def node_status(node):
    """Return the structural and output state of a node."""
    if not os.path.isdir(node + '/_c'):
        return 'no _c'
    if os.path.exists(node + '/_c/run') and os.path.exists(node + '/_c/yield'):
        return 'run/yield'
    if os.path.exists(node + '/_c/yield'):
        return 'yield'
    if not (os.path.exists(node + '/_c/run') and
            os.access(node + '/_c/run', os.X_OK)):
        return 'no run script'

    state_labels = {
        OutputState.ABSENT: 'ready to run',
        OutputState.RUNNING: 'running',
        OutputState.SUCCESS: 'done',
        OutputState.FAILURE: 'failed',
        OutputState.INCOMPLETE: 'incomplete',
        OutputState.INVALID: 'invalid',
    }
    return state_labels[output_state(node)]
