import subprocess
import sys
import unittest
from pathlib import Path

from rf import cli, executor, version_control


class CommandLineTests(unittest.TestCase):

    def test_subcommands_route_to_their_owning_modules(self):
        parser = cli.build_parser()
        cases = [
            (['run', '--dry-run', '.'], executor.run),
            (['drop', '.'], executor.drop),
            (['clone', 'repository', 'directory'], version_control.clone),
            (['commit', '-m', 'message', '.'], version_control.commit),
            (['commit-code', '-m', 'message', '.'],
             version_control.commit_code),
            (['get', '.'], version_control.get),
        ]

        for arguments, expected_handler in cases:
            with self.subTest(arguments=arguments):
                parsed = parser.parse_args(arguments)
                self.assertIs(expected_handler, parsed.func)

    def test_package_module_displays_help(self):
        repository_root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, '-m', 'rf', '--help'],
            cwd=repository_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('commit-code', result.stdout)
        self.assertIn('status', result.stdout)


if __name__ == '__main__':
    unittest.main()
