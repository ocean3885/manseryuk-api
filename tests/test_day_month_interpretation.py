"""일주·월지 해설의 DB 이전, 중복 생성 방지, 루트 응답을 검증한다."""
from pathlib import Path
import json
import os
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from core.day_month_database import (
    claim_generation, fail_generation, finish_generation, lookup_or_queue,
)
from core.interpretation_database import DDL, find_rule
from main import app
from schemas.interpretation_rule import InterpretationQuery, empty_rule
from services.day_month_generation import generate_queued, request_explanation


class DayMonthDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.database = Path(self.directory.name) / 'interpretations.db'

    def test_missing_database_is_created_and_claim_is_unique(self):
        self.assertEqual(lookup_or_queue('甲子', '午', self.database), (None, True))
        self.assertTrue(self.database.is_file())
        self.assertEqual(lookup_or_queue('甲子', '午', self.database), (None, True))
        attempt = claim_generation('甲子', '午', self.database)
        self.assertEqual(attempt, 1)
        self.assertIsNone(claim_generation('甲子', '午', self.database))
        self.assertEqual(lookup_or_queue('甲子', '午', self.database), (None, False))
        text = '일주·월지의 일반 해설입니다.'
        self.assertTrue(finish_generation('甲子', '午', attempt, text, 'model', self.database))
        self.assertFalse(finish_generation('甲子', '午', attempt, '늦은 응답', 'model', self.database))
        self.assertEqual(lookup_or_queue('甲子', '午', self.database), (text, False))
        with sqlite3.connect(self.database) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM day_month_interpretations').fetchone()[0], 1)

    def test_v1_upgrade_keeps_written_relation_rules(self):
        rule = empty_rule('stem', 'control', ['식신', '편관'])
        with sqlite3.connect(self.database) as db:
            db.execute(DDL)
            db.execute('PRAGMA user_version=1')
            db.execute('''INSERT INTO interpretation_rules
                (rule_id, layer, relation_type, participant_pattern, conditions_json, explanation, content_status)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (rule.rule_id, rule.layer, rule.relation_type, rule.pattern_json,
                 '{"scope":"natal"}', '기존 해설', 'ready'))
        self.assertEqual(lookup_or_queue('甲子', '子', self.database), (None, True))
        query = InterpretationQuery(layer='stem', relation_type='control',
                                    participant_pattern=['식신', '편관'], facts={'scope': 'natal'})
        self.assertEqual(find_rule(query, self.database).explanation, '기존 해설')
        with sqlite3.connect(self.database) as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 2)

    def test_failure_has_cooldown_and_retry(self):
        with patch('core.day_month_database.time.time', return_value=1000):
            lookup_or_queue('甲子', '午', self.database)
            attempt = claim_generation('甲子', '午', self.database)
            fail_generation('甲子', '午', attempt, self.database)
            self.assertEqual(lookup_or_queue('甲子', '午', self.database), (None, False))
        with patch('core.day_month_database.time.time', return_value=4600):
            self.assertEqual(lookup_or_queue('甲子', '午', self.database), (None, True))
            self.assertEqual(claim_generation('甲子', '午', self.database), 2)

    def test_invalid_day_pillar_is_not_stored(self):
        with self.assertRaises(ValueError):
            lookup_or_queue('甲丑', '午', self.database)
        self.assertFalse(self.database.exists())

    def test_background_generator_stores_only_valid_response(self):
        lookup_or_queue('甲子', '午', self.database)
        with patch('services.day_month_generation.request_explanation', return_value=('감성적인 해설', 'test-model')):
            generate_queued('甲子', '午', self.database)
        self.assertEqual(lookup_or_queue('甲子', '午', self.database), ('감성적인 해설', False))


class DayMonthGenerationTests(unittest.TestCase):
    def test_provider_receives_only_pair_and_validates_structured_response(self):
        text = '계절의 이미지를 엮은 일반 해설입니다. ' * 30
        response = MagicMock(status_code=200)
        response.json.return_value = {'candidates': [{
            'finishReason': 'STOP',
            'content': {'parts': [{'text': json.dumps({'explanation': text}, ensure_ascii=False)}]},
        }]}
        with (patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key', 'GEMINI_MODEL': 'test-model'}),
              patch('services.day_month_generation.httpx.Client') as client):
            client.return_value.__enter__.return_value.post.return_value = response
            self.assertEqual(request_explanation('甲子', '午'), (text.strip(), 'test-model'))
            body = client.return_value.__enter__.return_value.post.call_args.kwargs['json']
            payload = json.loads(body['contents'][0]['parts'][0]['text'])
            self.assertEqual(set(payload), {'day_pillar', 'month_branch', 'month_label'})
            self.assertEqual(payload['day_pillar'], '갑자(甲子)')
            self.assertEqual(payload['month_label'], '오월(午月)')
            response.json.return_value['candidates'][0]['content']['parts'][0]['text'] = '{"explanation":"짧음"}'
            with self.assertRaises(ValueError):
                request_explanation('甲子', '午')


@unittest.skipUnless((Path(__file__).resolve().parents[1] / 'manseryuk.db').is_file(), '달력 DB가 필요합니다.')
class RootDayMonthTests(unittest.TestCase):
    def test_disabled_feature_does_not_touch_explanation_database(self):
        query = dict(year=1995, month='5', day='12', hour=14, min=30, sl='sol', gen='남')
        with TemporaryDirectory() as directory:
            database = Path(directory) / 'interpretations.db'
            with (patch('routers.root.DEFAULT_DATABASE', database),
                  patch('routers.root.interpretation_enabled', return_value=False)):
                with TestClient(app) as client:
                    response = client.get('/', params=query)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertIsNone(response.json()['day_month_interpretation'])
            self.assertFalse(database.exists())

    def test_first_lookup_is_empty_and_next_lookup_has_generated_text(self):
        query = dict(year=1995, month='5', day='12', hour=14, min=30, sl='sol', gen='남')
        with TemporaryDirectory() as directory:
            database = Path(directory) / 'interpretations.db'
            content = '갑자일주와 자월의 감성적인 일반 해설입니다.'
            with (patch('routers.root.DEFAULT_DATABASE', database),
                  patch('routers.root.interpretation_enabled', return_value=True),
                  patch('services.day_month_generation.request_explanation', return_value=(content, 'test-model'))):
                with TestClient(app) as client:
                    first = client.get('/', params=query)
                    self.assertEqual(first.status_code, 200, first.text)
                    self.assertIsNone(first.json()['day_month_interpretation'])
                    second = client.get('/', params=query)
                    self.assertEqual(second.status_code, 200, second.text)
                    interpretation = second.json()['day_month_interpretation']
                    self.assertEqual(interpretation['explanation'], content)
                    self.assertEqual(len(interpretation['day_pillar']), 2)
                    self.assertEqual(len(interpretation['month_branch']), 1)
