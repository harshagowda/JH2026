import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import search_files


class SearchFilesTests(unittest.TestCase):
    def test_matches_pattern_by_filename_and_relative_path(self):
        root = Path('/tmp/project-root')
        path = root / 'src' / 'main.py'

        self.assertTrue(search_files.matches_pattern(path, root, ['*.py']))
        self.assertTrue(search_files.matches_pattern(path, root, ['src/*.py']))
        self.assertFalse(search_files.matches_pattern(path, root, ['*.md']))

    def test_search_file_respects_case_sensitivity(self):
        with TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / 'notes.txt'
            file_path.write_text('Hello\nworld\nHELLO\n', encoding='utf-8')

            case_sensitive = search_files.search_file(file_path, 'hello', ignore_case=False)
            case_insensitive = search_files.search_file(file_path, 'hello', ignore_case=True)

            self.assertEqual(case_sensitive, [])
            self.assertEqual(case_insensitive, [(1, 'Hello'), (3, 'HELLO')])

    def test_main_reports_matches(self):
        with TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / 'docs').mkdir()
            (root / 'docs' / 'readme.md').write_text('alpha\nBeta\nalpha\n', encoding='utf-8')

            stdout = io.StringIO()
            with patch('sys.argv', ['search_files.py', 'alpha', '*.md', '--root', str(root)]):
                with redirect_stdout(stdout):
                    exit_code = search_files.main()

            output = stdout.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn('docs/readme.md:1: alpha', output)
            self.assertIn('docs/readme.md:3: alpha', output)
            self.assertIn('Matched files: 1', output)
            self.assertIn('Total matches: 2', output)

    def test_main_handles_missing_root(self):
        stdout = io.StringIO()
        with patch('sys.argv', ['search_files.py', 'x', '*.txt', '--root', '/tmp/does-not-exist-xyz']):
            with redirect_stdout(stdout):
                exit_code = search_files.main()

        self.assertEqual(exit_code, 1)
        self.assertIn('ERROR: root path does not exist or is not a directory', stdout.getvalue())


if __name__ == '__main__':
    unittest.main()
