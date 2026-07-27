"""Output-state classification and marker persistence."""

import json
import os
import tempfile
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path


class OutputState(Enum):
    """The state represented by a node's output directory."""

    ABSENT = 'absent'
    RUNNING = 'running'
    SUCCESS = 'success'
    FAILURE = 'failure'
    INCOMPLETE = 'incomplete'
    INVALID = 'invalid'


MARKERS = {
    OutputState.RUNNING: 'RUNNING',
    OutputState.SUCCESS: 'SUCCESS',
    OutputState.FAILURE: 'FAILURE',
}


def output_state(node):
    """Return the state represented by a node's _o directory."""
    output = Path(node) / '_o'
    if not output.exists():
        return OutputState.ABSENT
    if not output.is_dir():
        return OutputState.INVALID

    states = [
        state for state, marker in MARKERS.items()
        if (output / marker).exists()
    ]
    if len(states) > 1:
        return OutputState.INVALID
    if not states:
        return OutputState.INCOMPLETE
    return states[0]


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def write_json_atomic(path, data):
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


def finish_execution(output, marker, record, **updates):
    """Atomically replace RUNNING with the final state marker."""
    record.update(updates)
    running = output / MARKERS[OutputState.RUNNING]
    write_json_atomic(running, record)
    os.replace(running, output / marker)
