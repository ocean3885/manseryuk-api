from pathlib import Path
import unittest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException
from core.api_errors import http_error_handler, unexpected_error_handler
from core.dependencies import get_db
from main import app
from schemas.api_error import ApiErrorResponse

QUERY = dict(year=1995, month='5', day='12', hour=14, min=30, sl='sol', gen='남')
DB = Path(__file__).resolve().parents[1] / 'manseryuk.db'


class ErrorHandlerTests(unittest.TestCase):
    def test_framework_errors_and_openapi_use_common_schema(self):
        with TestClient(app) as client:
            cases = [('/missing-route', 404), ('/character-details', 422)]
            for path, status in cases:
                response = client.get(path)
                self.assertEqual(response.status_code, status)
                ApiErrorResponse.model_validate(response.json())
            response = client.post('/character-details')
            self.assertEqual(response.status_code, 405)
            self.assertIn('GET', response.headers['allow'])
            self.assertEqual(response.json()['code'], 'http_405')
            response = client.get('/cycle-analysis', params={**QUERY, 'sewoon_year': 'bad'})
            error = response.json()
            self.assertEqual(response.status_code, 422)
            self.assertEqual(error['errors'][0]['field'], 'sewoon_year')
            self.assertEqual(error['errors'][0]['code'], 'int_parsing')
            self.assertEqual(error['errors'][0]['location'], ['query', 'sewoon_year'])
            self.assertTrue(error['example'].startswith('/cycle-analysis?'))
            self.assertIn('sewoon_year=', error['example'])
            self.assertNotIn('bad', str(error))
            spec = client.get('/openapi.json').json()
            for path in ('/', '/character-details', '/relation-index', '/cycle-analysis'):
                for code in ('400', '404', '422', '500'):
                    schema = spec['paths'][path]['get']['responses'][code]['content']['application/json']['schema']
                    self.assertTrue(schema['$ref'].endswith('/ApiErrorResponse'))

    def test_server_errors_hide_internal_details_and_preserve_headers(self):
        isolated = FastAPI()
        isolated.add_exception_handler(StarletteHTTPException, http_error_handler)
        isolated.add_exception_handler(Exception, unexpected_error_handler)

        @isolated.get('/explicit')
        def explicit():
            raise HTTPException(503, 'private database path', headers={'Retry-After': '10'})

        @isolated.get('/unexpected')
        def unexpected():
            raise RuntimeError('private database path')

        with TestClient(isolated, raise_server_exceptions=False) as client:
            response = client.get('/explicit')
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.headers['retry-after'], '10')
            self.assertNotIn('private', response.text)
            with self.assertLogs('core.api_errors', level='ERROR'):
                response = client.get('/unexpected')
            self.assertEqual(response.status_code, 500)
            self.assertNotIn('private', response.text)
            ApiErrorResponse.model_validate(response.json())


@unittest.skipUnless(DB.is_file(), '달력 DB가 필요합니다.')
class ApiDomainErrorTests(unittest.TestCase):
    def test_domain_errors_have_fields_constraints_and_compatible_detail(self):
        engine = create_engine(f'sqlite:///file:{DB}?mode=ro&uri=true')
        def readonly_db():
            with Session(engine) as session:
                yield session
        previous = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = readonly_db
        try:
            with TestClient(app) as client:
                for path in ('/', '/character-details', '/relation-index', '/cycle-analysis'):
                    params = {**QUERY, **({'daewoon_index': 0} if path == '/cycle-analysis' else {})}
                    response = client.get(path, params={**params, 'hour': 24})
                    self.assertEqual(response.status_code, 400)
                    body = ApiErrorResponse.model_validate(response.json())
                    self.assertEqual(body.code, 'invalid_birth_input')
                    self.assertEqual(body.detail, body.message)
                    self.assertEqual(body.errors[0].field, 'hour')
                    self.assertEqual(body.errors[0].constraints, dict(minimum=0, maximum=23))
                for selection, code, field in [({}, 'invalid_cycle_selection', None),
                                              ({'daewoon_index': 10}, 'daewoon_index_out_of_range', 'daewoon_index'),
                                              ({'sewoon_year': 1800}, 'sewoon_year_out_of_range', 'sewoon_year')]:
                    response = client.get('/cycle-analysis', params={**QUERY, **selection})
                    self.assertEqual(response.status_code, 400)
                    self.assertEqual(response.json()['code'], code)
                    self.assertEqual(response.json()['errors'][0]['field'], field)
                response = client.get('/', params={**QUERY, 'year': 2024, 'month': '2', 'day': '1', 'sl': 'lun_y'})
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.json()['code'], 'calendar_date_not_found')
        finally:
            if previous is None:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = previous
            engine.dispose()
