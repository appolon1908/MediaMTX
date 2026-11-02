"""Isolated status and dry planning tests; the execution primitive is denied."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'scripts/nabeel-distribution.py'


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.blocked = self.root / 'exec-attempted'
        # Applied before product imports: a regression cannot replace this process
        # with FFmpeg, even if dry planning accidentally reaches os.execvp.
        (self.root / 'sitecustomize.py').write_text(
            'import os\nfrom pathlib import Path\n'
            'def forbidden(*args, **kwargs):\n'
            '    Path(os.environ["EXEC_SENTINEL"]).write_text("blocked")\n'
            '    raise SystemExit("external execution blocked by test harness")\n'
            'os.execvp = forbidden\n')
        self.env = {key: value for key, value in os.environ.items()
                    if not key.startswith('NABEEL_')}
        self.env.update({'PYTHONPATH': str(self.root), 'EXEC_SENTINEL': str(self.blocked),
                         'FIXTURE_STREAM_REF': 'fixture-only-not-a-provider-credential'})
        self.config = {'schema': 'nabeel.distribution.v1',
                       'source': 'rtsp://example.invalid/source',
                       'destinations': [{'id': 'fixture', 'protocol': 'rtmp', 'enabled': True,
                                         'url': 'rtmp://example.invalid/live/{secret}',
                                         'secret_env': 'FIXTURE_STREAM_REF'}]}

    def invoke(self, *args, config=None, remove_secret=False):
        path = self.root / 'destinations.json'
        path.write_text(json.dumps(self.config if config is None else config))
        env = dict(self.env)
        if remove_secret:
            env.pop('FIXTURE_STREAM_REF')
        result = subprocess.run([sys.executable, str(CLI), '--config', str(path), *args],
                                env=env, text=True, capture_output=True, timeout=5)
        self.assertFalse(self.blocked.exists(), 'External execution primitive was attempted')
        return result

    def test_status_reports_readiness_without_secret_values(self):
        result = self.invoke('status')
        self.assertEqual(0, result.returncode)
        destination = json.loads(result.stdout)['destinations'][0]
        self.assertIs(destination['ready'], True)
        self.assertEqual('FIXTURE_STREAM_REF', destination['secret_ref'])
        self.assertNotIn(self.env['FIXTURE_STREAM_REF'], result.stdout + result.stderr)

    def test_disabled_destination_stays_disabled_even_with_secret(self):
        self.config['destinations'][0]['enabled'] = False
        result = self.invoke('status')
        destination = json.loads(result.stdout)['destinations'][0]
        self.assertIs(destination['ready'], False)
        self.assertEqual('disabled', destination['reason'])

    def test_text_false_does_not_activate_destination(self):
        for invalid in ('false', 'true', 1, 0, None, {}, []):
            with self.subTest(enabled=invalid):
                self.config['destinations'][0]['enabled'] = invalid
                destination = json.loads(self.invoke('status').stdout)['destinations'][0]
                self.assertIs(destination['enabled'], False)
                self.assertIs(destination['ready'], False)

    def test_harness_rejects_execution_before_product_import(self):
        result = subprocess.run([sys.executable, '-c',
                                 'import os; os.execvp("not-a-real-fixture-binary", ["fixture"])'],
                                env=self.env, text=True, capture_output=True, timeout=5)
        self.assertNotEqual(0, result.returncode)
        self.assertTrue(self.blocked.exists())
        self.assertIn('external execution blocked by test harness', result.stderr)

    def test_missing_secret_fails_closed_and_dry_planning_exits_nonzero(self):
        result = self.invoke('run', 'fixture', '--dry-run', remove_secret=True)
        self.assertEqual(4, result.returncode)
        self.assertEqual('missing_secret', json.loads(result.stderr)['reason'])

    def test_missing_url_is_not_ready(self):
        self.config['destinations'][0]['url'] = ''
        destination = json.loads(self.invoke('status').stdout)['destinations'][0]
        self.assertIs(destination['ready'], False)
        self.assertEqual('missing_url', destination['reason'])

    def test_unknown_destination_rejected_before_any_execution(self):
        result = self.invoke('run', 'not-registered', '--dry-run')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('unknown_destination', result.stderr)

    def test_rtmp_dry_plan_has_bounded_argv_and_redacts_secret(self):
        result = self.invoke('run', 'fixture', '--dry-run')
        self.assertEqual(0, result.returncode)
        plan = json.loads(result.stdout)
        self.assertEqual(['ffmpeg', '-hide_banner', '-loglevel', 'warning', '-re', '-i',
                          'rtsp://example.invalid/source', '-c', 'copy', '-f', 'flv',
                          'rtmp://example.invalid/live/<secret>'], plan['command_redacted'])
        self.assertNotIn(self.env['FIXTURE_STREAM_REF'], result.stdout + result.stderr)

    def test_srt_dry_plan_uses_mpegts_without_execution(self):
        self.config['destinations'][0].update(protocol='srt', url='srt://example.invalid:9000?streamid={secret}')
        plan = json.loads(self.invoke('run', 'fixture', '--dry-run').stdout)
        self.assertEqual(['-f', 'mpegts', 'srt://example.invalid:9000?streamid=<secret>'],
                         plan['command_redacted'][-3:])

    def test_invalid_schema_rejected(self):
        self.config['schema'] = 'not-approved'
        result = self.invoke('status')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('invalid_schema', result.stderr)

    def test_literal_shell_metacharacters_stay_inside_argv(self):
        marker = self.root / 'must-not-exist'
        literal = '$(touch ' + str(marker) + ');echo not-a-command'
        self.config['source'] = literal
        plan = json.loads(self.invoke('run', 'fixture', '--dry-run').stdout)
        self.assertEqual(literal, plan['command_redacted'][6])
        self.assertFalse(marker.exists())

    def test_committed_example_is_disabled_and_uses_secret_references(self):
        config = json.loads((ROOT / 'docs/nabeel-destinations.example.json').read_text())
        self.assertEqual('nabeel.distribution.v1', config['schema'])
        self.assertEqual({'rtmp', 'srt'}, {d['protocol'] for d in config['destinations']})
        for destination in config['destinations']:
            self.assertIs(destination['enabled'], False)
            self.assertTrue(destination['secret_env'].startswith('NABEEL_'))
            self.assertIn('{secret}', destination['url'])


if __name__ == '__main__':
    unittest.main()
