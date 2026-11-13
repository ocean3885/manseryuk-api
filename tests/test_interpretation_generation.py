"""키·유료 호출 없이 Gemini 요청·해설 검증·부분 저장·재개를 검사한다."""
from copy import deepcopy
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

import httpx

from services.interpretation_generation import (
    GenerationError, GeminiWriter, generate_document, generation_plan, read_json, validate_reply,
)

ROOT = Path(__file__).resolve().parents[1]


def sample():
    return json.loads((ROOT / 'data/interpretation_authoring_sample20.json').read_text(encoding='utf-8'))


def response_for(rows, explanation='관계의 구조를 확인하는 검증용 해설입니다.'):
    return {'rules': [{'rule_id': row['rule_id'], 'explanation': explanation} for row in rows]}


class GenerationValidationTests(unittest.TestCase):
    def test_plan_limits_empty_rows_and_preserves_source(self):
        document = sample()
        document['rules'][0]['explanation'] = '기존 작성본'
        before = deepcopy(document)
        plan = generation_plan(document)
        self.assertEqual(plan['selected_count'], 5)
        self.assertEqual(plan['request_count'], 1)
        self.assertEqual(plan['already_written_count'], 1)
        self.assertNotIn(document['rules'][0]['rule_id'], plan['selected_rule_ids'])
        self.assertEqual(document, before)

    def test_invalid_identity_conditions_duplicate_rows_and_limits_are_rejected(self):
        for mutation in (
            lambda d: d['rules'][0].update(rule_id='unknown'),
            lambda d: d['rules'][0].update(conditions_json={'scope': 'cross_context'}),
            lambda d: d['rules'].append(deepcopy(d['rules'][0])),
            lambda d: d.update(format_version=True),
            lambda d: d['rules'][0].update(explanation=' '),
            lambda d: d['rules'][0].update(content_status='ready'),
        ):
            document = sample()
            mutation(document)
            with self.assertRaises(ValueError):
                generation_plan(document)
        for options in ({'limit': 0}, {'limit': True}, {'batch_size': 11}, {'batch_size': 0}):
            with self.assertRaises(ValueError):
                generation_plan(sample(), **options)

    def test_response_requires_exact_ids_fields_and_valid_text(self):
        rows = sample()['rules'][:2]
        good = response_for(rows)
        self.assertEqual(len(validate_reply(good, rows)), 2)
        self.assertTrue(all(v is None for v in validate_reply(response_for(rows, None), rows).values()))
        for invalid in (
            {'rules': good['rules'][:1]},
            {'rules': [good['rules'][0], good['rules'][0]]},
            {'rules': [{'rule_id': 'unknown', 'explanation': '설명'}, good['rules'][1]]},
            {'rules': [{**good['rules'][0], 'conditions_json': {}}, good['rules'][1]]},
            response_for(rows, ''), response_for(rows, 123), response_for(rows, '가' * 2001),
            {**good, 'content_status': 'ready'},
        ):
            with self.subTest(invalid=invalid), self.assertRaises(GenerationError):
                validate_reply(invalid, rows)

    def test_json_rejects_duplicate_keys_and_nonfinite_numbers(self):
        for text in ('{"rules":[],"rules":[]}', '{"rules":NaN}', '{"rules":Infinity}'):
            with self.assertRaises(ValueError):
                read_json(text)


class GeminiRequestTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, {'GEMINI_API_KEY': 'fake-key-for-offline-tests'}, clear=False)
        env.start()
        self.addCleanup(env.stop)
        self.rows = sample()['rules'][:2]

    def run_response(self, response):
        with httpx.Client(transport=httpx.MockTransport(lambda request: response)) as client:
            with GeminiWriter(model='gemini-test', client=client) as writer:
                return writer.write(self.rows, sample()['writing_guide'])

    def test_native_request_uses_header_key_schema_and_separate_system_instruction(self):
        def handler(request):
            self.assertEqual(request.url.host, 'generativelanguage.googleapis.com')
            self.assertEqual(request.url.path, '/v1beta/models/gemini-test:generateContent')
            self.assertEqual(request.headers['x-goog-api-key'], 'fake-key-for-offline-tests')
            self.assertNotIn('fake-key', str(request.url))
            body = json.loads(request.content)
            self.assertNotIn('fake-key', json.dumps(body))
            self.assertIn('systemInstruction', body)
            self.assertEqual(body['generationConfig']['responseMimeType'], 'application/json')
            prompt = json.loads(body['contents'][0]['parts'][0]['text'])
            self.assertEqual([r['rule_id'] for r in prompt['rules']], [r['rule_id'] for r in self.rows])
            return httpx.Response(200, json={
                'candidates': [{'finishReason': 'STOP', 'content': {'parts': [
                    {'thought': True, 'text': '모델 내부 사고'},
                    {'text': json.dumps(response_for(self.rows), ensure_ascii=False)}]}}],
                'usageMetadata': {'promptTokenCount': 30, 'candidatesTokenCount': 20, 'totalTokenCount': 50}})
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            with GeminiWriter(model='gemini-test', client=client) as writer:
                reply, usage = writer.write(self.rows, sample()['writing_guide'])
        self.assertEqual(reply, response_for(self.rows))
        self.assertEqual(usage['totalTokenCount'], 50)

    def test_http_errors_are_not_retried_and_do_not_expose_server_body_or_key(self):
        calls = []
        def handler(request):
            calls.append(request)
            return httpx.Response(429, text='fake-key-for-offline-tests confidential response')
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            with GeminiWriter(client=client) as writer, self.assertRaises(GenerationError) as error:
                writer.write(self.rows, {})
        self.assertIn('429', str(error.exception))
        self.assertNotIn('fake-key', str(error.exception))
        self.assertNotIn('confidential', str(error.exception))
        self.assertEqual(len(calls), 1)

    def test_timeout_truncated_blocked_and_malformed_outputs_fail(self):
        def timeout(request):
            raise httpx.ReadTimeout('fake-key-for-offline-tests', request=request)
        with httpx.Client(transport=httpx.MockTransport(timeout)) as client:
            with GeminiWriter(client=client) as writer, self.assertRaises(GenerationError) as error:
                writer.write(self.rows, {})
        self.assertNotIn('fake-key', str(error.exception))
        for payload in (
            {'candidates': [{'finishReason': 'MAX_TOKENS'}]},
            {'promptFeedback': {'blockReason': 'SAFETY'}},
            {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': 'bad JSON'}]}}]},
            {'candidates': [None]}, [],
        ):
            with self.subTest(payload=payload), self.assertRaises(GenerationError):
                self.run_response(httpx.Response(200, json=payload))

    def test_missing_key_and_invalid_model_fail_before_request(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(GenerationError):
            GeminiWriter()
        with self.assertRaises(ValueError):
            GeminiWriter(model='../other-host')


class GenerationCheckpointTests(unittest.TestCase):
    def test_success_changes_only_selected_explanations_and_retains_authored_content(self):
        document = sample()
        document['rules'][0]['explanation'] = '기존 해설'
        before = deepcopy(document)
        writer = Mock()
        writer.write.side_effect = lambda rows, guide: (response_for(list(reversed(rows))), {'totalTokenCount': 50})
        checkpoints = []
        output = generate_document(document, writer, model='gemini-test', limit=5, batch_size=2,
                                   save=lambda data: checkpoints.append(deepcopy(data)))
        self.assertEqual(document, before)
        self.assertEqual(output['generation']['generated_count'], 5)
        self.assertEqual(output['generation']['completed_batches'], 3)
        self.assertEqual(output['generation']['usage']['totalTokenCount'], 150)
        self.assertEqual(output['generation']['status'], 'completed')
        self.assertEqual(checkpoints[0]['generation']['status'], 'in_progress')
        for index, row in enumerate(output['rules']):
            for key in row:
                if key != 'explanation':
                    self.assertEqual(row[key], before['rules'][index][key])
        self.assertEqual(output['rules'][0]['explanation'], '기존 해설')
        self.assertEqual(output['rules'][6:], before['rules'][6:])

    def test_failed_batch_keeps_successful_checkpoint_and_resume_skips_written_rows(self):
        writer = Mock()
        calls = []
        def write(rows, guide):
            calls.append(rows)
            if len(calls) == 2:
                return {'rules': []}, {}
            return response_for(rows), {}
        writer.write.side_effect = write
        checkpoints = []
        with self.assertRaises(GenerationError):
            generate_document(sample(), writer, model='gemini-test', limit=5, batch_size=2,
                              save=lambda data: checkpoints.append(deepcopy(data)))
        last = checkpoints[-1]
        self.assertEqual(last['generation']['status'], 'failed')
        self.assertEqual(last['generation']['processed_count'], 2)
        self.assertTrue(all(r['explanation'] for r in last['rules'][:2]))
        self.assertTrue(all(r['explanation'] is None for r in last['rules'][2:]))
        self.assertEqual(generation_plan(last)['selected_rule_ids'][0], last['rules'][2]['rule_id'])


class GenerationCommandTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.source = self.directory / 'source.json'
        self.source.write_text(json.dumps(sample(), ensure_ascii=False), encoding='utf-8')
        self.output = self.directory / 'result.json'

    def command(self, *arguments):
        environment = dict(os.environ)
        environment.pop('GEMINI_API_KEY', None)
        return subprocess.run([sys.executable, str(ROOT / 'scripts' / 'interpretation_rules.py'), 'generate',
                               '--input', str(self.source), '--output', str(self.output), *arguments],
                              cwd=ROOT, env=environment, text=True, encoding='utf-8', capture_output=True)

    def test_dry_run_needs_no_key_and_writes_no_files(self):
        result = self.command('--dry-run')
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertEqual(plan['selected_count'], 5)
        self.assertFalse(plan['api_key_available'])
        self.assertFalse(self.output.exists())

    def test_missing_key_creates_no_output_and_preserves_source(self):
        before = self.source.read_bytes()
        result = self.command()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('GEMINI_API_KEY', result.stderr)
        self.assertFalse(self.output.exists())
        self.assertEqual(self.source.read_bytes(), before)

    def test_existing_output_is_preserved_even_for_dry_run(self):
        self.output.write_text('기존 작성 파일', encoding='utf-8')
        result = self.command('--dry-run')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.output.read_text(encoding='utf-8'), '기존 작성 파일')

    def test_all_written_input_is_saved_without_key_or_network_and_metadata_is_not_approved(self):
        document = sample()
        for row in document['rules']:
            row['explanation'] = '이미 작성한 해설'
        self.source.write_text(json.dumps(document), encoding='utf-8')
        result = self.command()
        self.assertEqual(result.returncode, 0, result.stderr)
        saved = json.loads(self.output.read_text(encoding='utf-8'))
        self.assertEqual(saved['generation']['generated_count'], 0)
        self.assertEqual(saved['generation']['status'], 'completed')
        self.assertEqual(saved['rules'], document['rules'])
        self.assertFalse(list(self.directory.glob('.interpretation-*.tmp')))

    def test_cli_partial_failure_atomically_keeps_completed_batch_in_output(self):
        from scripts.interpretation_rules import main
        before = self.source.read_bytes()
        writer = Mock()
        calls = []
        def write(rows, guide):
            calls.append(rows)
            if len(calls) > 1:
                raise GenerationError('검증용 연결 실패')
            return response_for(rows), {'totalTokenCount': 30}
        writer.write.side_effect = write
        arguments = ['interpretation_rules.py', 'generate', '--input', str(self.source),
                     '--output', str(self.output), '--limit', '4', '--batch-size', '2']
        with patch('scripts.interpretation_rules.GeminiWriter') as factory:
            factory.return_value.__enter__.return_value = writer
            with patch.object(sys, 'argv', arguments), redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                with self.assertRaises(SystemExit) as error:
                    main()
        self.assertEqual(error.exception.code, 2)
        saved = json.loads(self.output.read_text(encoding='utf-8'))
        self.assertEqual(saved['generation']['status'], 'failed')
        self.assertEqual(saved['generation']['generated_count'], 2)
        self.assertTrue(all(row['explanation'] for row in saved['rules'][:2]))
        self.assertTrue(all(row['explanation'] is None for row in saved['rules'][2:]))
        self.assertEqual(self.source.read_bytes(), before)
        self.assertFalse(list(self.directory.glob('.interpretation-*.tmp')))


if __name__ == '__main__':
    unittest.main()
