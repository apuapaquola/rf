import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from rf import rflib


class OutputStateTests(unittest.TestCase):

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)

    def make_node(self, relative_path, script):
        node = self.root / relative_path
        code = node / '_c'
        code.mkdir(parents=True)
        driver = code / 'run'
        driver.write_text(script, encoding='utf-8')
        driver.chmod(0o755)
        return node

    def test_output_state_recognizes_absent_incomplete_and_legacy_success(self):
        node = self.make_node('node', '#!/bin/sh\nexit 0\n')

        self.assertEqual(rflib.OutputState.ABSENT, rflib.output_state(node))

        output = node / '_o'
        output.mkdir()
        self.assertEqual(rflib.OutputState.INCOMPLETE, rflib.output_state(node))

        (output / 'SUCCESS').touch()
        self.assertEqual(rflib.OutputState.SUCCESS, rflib.output_state(node))

    def test_conflicting_markers_are_invalid(self):
        node = self.make_node('node', '#!/bin/sh\nexit 0\n')
        output = node / '_o'
        output.mkdir()
        (output / 'SUCCESS').touch()
        (output / 'FAILURE').touch()

        self.assertEqual(rflib.OutputState.INVALID, rflib.output_state(node))

    def test_successful_execution_records_metadata_and_output(self):
        node = self.make_node(
            'node', '#!/bin/sh\nprintf "driver output\\n"\n')

        rflib.execute_node(node)

        self.assertEqual(rflib.OutputState.SUCCESS, rflib.output_state(node))
        self.assertFalse((node / '_o' / 'RUNNING').exists())
        self.assertFalse((node / '_o' / 'FAILURE').exists())
        self.assertEqual(
            'driver output\n',
            (node / '_o' / 'nohup.out').read_text(encoding='utf-8'))

        metadata = json.loads(
            (node / '_o' / 'SUCCESS').read_text(encoding='utf-8'))
        self.assertEqual(1, metadata['schema_version'])
        self.assertEqual(0, metadata['exit_code'])
        self.assertIn('run_id', metadata)
        self.assertIn('started_at', metadata)
        self.assertIn('finished_at', metadata)

    def test_failed_execution_records_failure_and_exit_code(self):
        node = self.make_node(
            'node', '#!/bin/sh\nprintf "failure output\\n"\nexit 7\n')

        with self.assertRaises(rflib.NodeExecutionError) as raised:
            rflib.execute_node(node)

        self.assertEqual(7, raised.exception.returncode)
        self.assertEqual(rflib.OutputState.FAILURE, rflib.output_state(node))
        self.assertFalse((node / '_o' / 'RUNNING').exists())
        self.assertFalse((node / '_o' / 'SUCCESS').exists())

        metadata = json.loads(
            (node / '_o' / 'FAILURE').read_text(encoding='utf-8'))
        self.assertEqual(7, metadata['exit_code'])
        self.assertEqual(
            'failure output\n',
            (node / '_o' / 'nohup.out').read_text(encoding='utf-8'))

    def test_failed_dependency_blocks_descendant_and_make_failure_propagates(self):
        tree = self.root / 'tree'
        tree.mkdir()
        dependency = self.make_node(
            'tree/dependency', '#!/bin/sh\nexit 9\n')
        descendant = self.make_node(
            'tree/dependency/descendant',
            '#!/bin/sh\nprintf "must not run\\n"\n')

        with self.assertRaises(rflib.NodeExecutionError):
            rflib.execute_node(dependency)

        makefile = rflib.makefile(
            rflib.find_dependencies(str(tree), recursive=True))

        self.assertIn(
            str(dependency / '_o' / 'SUCCESS'),
            makefile)
        self.assertIn('failed (exit code 9)', makefile)
        with self.assertRaises(subprocess.CalledProcessError):
            rflib.run_make(makefile)

        self.assertFalse((descendant / '_o').exists())


if __name__ == '__main__':
    unittest.main()
