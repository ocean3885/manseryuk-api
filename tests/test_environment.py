"""Deployment .env loading: explicit location, host precedence and optional file."""
import os
import json
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from core.environment import load_environment


class EnvironmentTests(unittest.TestCase):
    def test_project_file_loads_even_when_working_directory_differs(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / '.env'
            env.write_text('MANSERYUK_TEST_VALUE=한글\n', encoding='utf-8')
            other = Path(tmp) / 'other'
            other.mkdir()
            (other / '.env').write_text('MANSERYUK_TEST_VALUE=wrong\n')
            previous = Path.cwd()
            try:
                os.chdir(other)
                with patch.dict(os.environ, {}, clear=True), patch('core.environment.ENV_FILE', env):
                    load_environment()
                    self.assertEqual(os.environ['MANSERYUK_TEST_VALUE'], '한글')
            finally:
                os.chdir(previous)

    def test_host_variables_including_empty_values_take_precedence(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / '.env'
            env.write_text('MANSERYUK_TEST_VALUE=file\nMANSERYUK_TEST_EMPTY=file\n')
            with patch.dict(os.environ, {'MANSERYUK_TEST_VALUE': 'host', 'MANSERYUK_TEST_EMPTY': ''}, clear=True), patch('core.environment.ENV_FILE', env):
                load_environment()
                load_environment()
                self.assertEqual(os.environ['MANSERYUK_TEST_VALUE'], 'host')
                self.assertEqual(os.environ['MANSERYUK_TEST_EMPTY'], '')

    def test_missing_file_is_optional(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True), patch('core.environment.ENV_FILE', Path(tmp) / '.env'):
            self.assertFalse(load_environment())
            self.assertNotIn('GEMINI_API_KEY', os.environ)

    def test_api_and_cli_bootstrap_load_configuration(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / '.env'
            env.write_text('GEMINI_API_KEY=test-only-placeholder\nGEMINI_MODEL=gemini-3.1-flash-lite\nMANSERYUK_BOOT_TEST=loaded\n')
            bootstrap = (
                'import os, sys, runpy; '
                f'sys.path.insert(0, {str(root)!r}); '
                'from pathlib import Path; import core.environment as config; '
                f'config.ENV_FILE = Path({str(env)!r}); '
                'os.environ.pop("GEMINI_API_KEY", None); '
                'os.environ.pop("GEMINI_MODEL", None); '
                'os.environ.pop("MANSERYUK_BOOT_TEST", None); '
            )
            api = subprocess.run([sys.executable, '-c', bootstrap +
                'import main; assert os.environ.get("MANSERYUK_BOOT_TEST") == "loaded"'],
                cwd=tmp, capture_output=True, text=True)
            self.assertEqual(api.returncode, 0, 'API bootstrap failed')
            args = [str(root / 'scripts/interpretation_rules.py'), 'generate',
                    '--input', str(root / 'data/interpretation_authoring_sample20.json'),
                    '--output', str(Path(tmp) / 'dry.json'), '--dry-run']
            cli = subprocess.run([sys.executable, '-c', bootstrap +
                f'sys.argv = {args!r}; runpy.run_path(sys.argv[0], run_name="__main__")'],
                cwd=tmp, capture_output=True, text=True)
            self.assertEqual(cli.returncode, 0, 'CLI bootstrap failed')
            plan = json.loads(cli.stdout)
            self.assertTrue(plan['api_key_available'])
            self.assertEqual(plan['model'], 'gemini-3.1-flash-lite')
            self.assertFalse((Path(tmp) / 'dry.json').exists())
