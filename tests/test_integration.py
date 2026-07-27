import shutil
import subprocess
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from rf import rflib


FIXTURE_ROOT = Path(__file__).parent / 'fixtures' / 'analysis_tree'
REQUIRES_WORKFLOW_TOOLS = (
    shutil.which('make') is not None and Path('/bin/bash').is_file()
)


@unittest.skipUnless(
    REQUIRES_WORKFLOW_TOOLS,
    'integration tests require Make and /bin/bash',
)
class WorkflowIntegrationTests(unittest.TestCase):

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

    def test_recursive_workflow_generates_expected_outputs(self):
        tree = self.root / 'analysis_tree'
        shutil.copytree(FIXTURE_ROOT, tree, symlinks=True)

        rflib.run(Namespace(
            node=str(tree),
            recursive=True,
            verbose=False,
            dry_run=False,
        ))

        expected = {}
        for node, prefix in [
                ('nodeA', 'a'),
                ('nodeB', 'b'),
                ('nodeB/nodeC', 'c'),
                ('nodeB/nodeD', 'd'),
                ('nodeE', 'e')]:
            for index in range(1, 4):
                expected[f'{node}/_o/s{index}.txt'] = f'{prefix}{index}\n'

        actual = {
            path.relative_to(tree).as_posix(): path.read_text(encoding='utf-8')
            for path in sorted(tree.rglob('*.txt'))
        }
        self.assertEqual(expected, actual)

        for node in [
                'nodeA', 'nodeB', 'nodeB/nodeC', 'nodeB/nodeD', 'nodeE']:
            self.assertEqual(
                rflib.OutputState.SUCCESS,
                rflib.output_state(tree / node),
            )

        self.assertEqual(
            [str((tree / 'nodeB' / 'nodeD').resolve())],
            list(rflib.dependency_links(str(tree / 'nodeE'))),
        )

    def test_failed_dependency_blocks_descendant_and_propagates_failure(self):
        tree = self.root / 'failure_tree'
        tree.mkdir()
        dependency = self.make_node(
            'failure_tree/dependency', '#!/bin/sh\nexit 9\n')
        descendant = self.make_node(
            'failure_tree/dependency/descendant',
            '#!/bin/sh\nprintf "must not run\\n"\n')

        with self.assertRaises(rflib.NodeExecutionError):
            rflib.execute_node(dependency)

        makefile = rflib.makefile(
            rflib.find_dependencies(str(tree), recursive=True))

        self.assertIn(str(dependency / '_o' / 'SUCCESS'), makefile)
        self.assertIn('failed (exit code 9)', makefile)
        with self.assertRaises(subprocess.CalledProcessError):
            rflib.run_make(makefile)

        self.assertFalse((descendant / '_o').exists())


if __name__ == '__main__':
    unittest.main()
