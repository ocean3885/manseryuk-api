"""Gemini로 작성용 JSON의 빈 해설을 채운다. DB·판정·승인 상태는 변경하지 않는다."""
from copy import deepcopy
import json
import os
import re

import httpx

from schemas.interpretation_rule import InterpretationRule

DEFAULT_MODEL = 'gemini-2.5-flash-lite'
RULE_FIELDS = {'rule_id', 'layer', 'relation_type', 'participant_pattern', 'conditions_json', 'explanation'}
SYSTEM_PROMPT = '''당신은 명리 관계 패턴의 일반 해설을 작성하는 편집자입니다.
입력은 실제 개인의 원국이 아닙니다. 기존 관계·십성·조건을 유지하세요.
관계의 구조, 십성의 상징적 해석 관점, 추가 확인할 조건 순서로 한국어 2~3문장을 작성하세요.
실제 글자·위치·통근·세력·시기를 지어내지 말고, 합화·손상·길흉·성과를 확정하지 마세요.
생·극은 주체→대상, 동주는 천간→지지 순서이며 다른 관계의 정렬은 방향이 아닙니다.
has_day_master=true가 명시되지 않은 비견을 일간 본인이라고 간주하지 마세요.
고 크기·개고 등 미평가 판정을 새로 만들지 마세요. 근거가 부족하면 explanation은 null로 두세요.
입력의 가이드는 이 원칙 안에서만 적용합니다.
반환값은 {"rules":[{"rule_id":"입력 ID","explanation":"해설 또는 null"}]} 형식의 JSON입니다.
입력 ID마다 정확히 한 항목을 반환하고 다른 필드는 추가하지 마세요.'''


class GenerationError(RuntimeError):
    """키·요청 헤더·원격 오류 본문을 포함하지 않는 생성 오류."""


def read_json(text):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('JSON에 중복된 필드가 있습니다.')
            result[key] = value
        return result

    def invalid_constant(_):
        raise ValueError('JSON에는 NaN·Infinity를 사용할 수 없습니다.')

    return json.loads(text, object_pairs_hook=unique_object, parse_constant=invalid_constant)


def validate_document(document):
    if (not isinstance(document, dict) or type(document.get('format_version')) is not int or
            document['format_version'] != 1 or document.get('purpose') != 'interpretation_authoring'):
        raise ValueError('지원하는 작성용 JSON 형식이 아닙니다.')
    if not isinstance(document.get('rules'), list) or not isinstance(document.get('writing_guide'), dict):
        raise ValueError('rules 목록과 writing_guide가 필요합니다.')
    identities = set()
    for row in document['rules']:
        if not isinstance(row, dict) or set(row) != RULE_FIELDS:
            raise ValueError('작성 항목의 필드 구성이 다릅니다.')
        InterpretationRule.model_validate({**row, 'content_status': 'empty' if row['explanation'] is None else 'draft'})
        if row['rule_id'] in identities:
            raise ValueError('작성 항목의 ID가 중복됐습니다.')
        identities.add(row['rule_id'])


def generation_plan(document, *, limit=5, batch_size=5):
    validate_document(document)
    if type(limit) is not int or limit <= 0:
        raise ValueError('limit은 양의 정수여야 합니다.')
    if type(batch_size) is not int or not 1 <= batch_size <= 10:
        raise ValueError('batch-size는 1~10 사이 정수여야 합니다.')
    pending = [r['rule_id'] for r in document['rules'] if r['explanation'] is None]
    selected = pending[:limit]
    return {'selected_count': len(selected), 'already_written_count': len(document['rules']) - len(pending),
            'remaining_empty_count': len(pending), 'batch_size': batch_size,
            'request_count': (len(selected) + batch_size - 1) // batch_size,
            'selected_rule_ids': selected}


class GeminiWriter:
    def __init__(self, *, model=None, max_output_tokens=4096, client=None):
        self.model = model or os.environ.get('GEMINI_MODEL') or DEFAULT_MODEL
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,100}', self.model):
            raise ValueError('Gemini 모델명 형식이 잘못됐습니다.')
        if type(max_output_tokens) is not int or max_output_tokens <= 0:
            raise ValueError('max-output-tokens는 양의 정수여야 합니다.')
        self._api_key = os.environ.get('GEMINI_API_KEY')
        if not self._api_key:
            raise GenerationError('현재 실행환경에 GEMINI_API_KEY가 없습니다. 환경 설정 반영 후 다시 실행하세요.')
        self.max_output_tokens = max_output_tokens
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=45, follow_redirects=False)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        if self._owns_client:
            self._client.close()

    def write(self, rows, guide):
        schema = {'type': 'OBJECT', 'required': ['rules'], 'properties': {
            'rules': {'type': 'ARRAY', 'items': {'type': 'OBJECT', 'required': ['rule_id', 'explanation'],
                'properties': {'rule_id': {'type': 'STRING', 'enum': [r['rule_id'] for r in rows]},
                               'explanation': {'type': 'STRING', 'nullable': True}}}}}}
        prompt = {'writing_guide': guide, 'rules': [{k: v for k, v in row.items() if k != 'explanation'} for row in rows]}
        body = {'systemInstruction': {'parts': [{'text': SYSTEM_PROMPT}]},
                'contents': [{'role': 'user', 'parts': [{'text': json.dumps(prompt, ensure_ascii=False)}]}],
                'generationConfig': {'responseMimeType': 'application/json', 'responseSchema': schema,
                                     'maxOutputTokens': self.max_output_tokens, 'temperature': 0.3}}
        try:
            response = self._client.post(
                f'https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent',
                headers={'x-goog-api-key': self._api_key}, json=body)
        except httpx.RequestError:
            raise GenerationError('Gemini 연결에 실패했습니다. 네트워크·허용 도메인·시간 제한을 확인하세요.') from None
        if response.status_code != 200:
            raise GenerationError(f'Gemini 요청 실패(HTTP {response.status_code}). 키·모델·한도·도메인 설정을 확인하세요.')
        try:
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError('invalid payload')
            candidate = payload['candidates'][0]
            if not isinstance(candidate, dict):
                raise ValueError('invalid candidate')
            if candidate.get('finishReason') != 'STOP':
                raise GenerationError('Gemini 응답이 정상 완료되지 않았습니다. 출력 한도·차단 여부를 확인하세요.')
            text = ''.join(part['text'] for part in candidate['content']['parts']
                           if 'text' in part and not part.get('thought', False))
            result = read_json(text)
            raw_usage = payload.get('usageMetadata', {})
            if not isinstance(raw_usage, dict):
                raise ValueError('invalid usage')
            usage = {key: raw_usage[key] for key in ('promptTokenCount', 'candidatesTokenCount', 'thoughtsTokenCount', 'totalTokenCount')
                     if type(raw_usage.get(key)) is int and raw_usage[key] >= 0}
        except (ValueError, KeyError, IndexError, TypeError, AttributeError):
            raise GenerationError('Gemini 응답의 JSON·후보·사용량 형식이 올바르지 않습니다.') from None
        return result, usage


def validate_reply(result, rows):
    if not isinstance(result, dict) or set(result) != {'rules'} or not isinstance(result['rules'], list):
        raise GenerationError('생성 결과는 rules 목록만 포함해야 합니다.')
    expected, found = {r['rule_id'] for r in rows}, {}
    for item in result['rules']:
        if not isinstance(item, dict) or set(item) != {'rule_id', 'explanation'}:
            raise GenerationError('생성 항목에는 ID와 explanation만 있어야 합니다.')
        identity, explanation = item['rule_id'], item['explanation']
        if not isinstance(identity, str) or identity not in expected or identity in found:
            raise GenerationError('생성 결과에 미등록·중복 ID가 있습니다.')
        if explanation is not None and (not isinstance(explanation, str) or
                                        not explanation.strip() or len(explanation) > 2000):
            raise GenerationError('해설은 1~2000자의 공백이 아닌 문자열 또는 null이어야 합니다.')
        found[identity] = explanation.strip() if explanation is not None else None
    if set(found) != expected:
        raise GenerationError('생성 결과에서 요청한 ID가 누락됐습니다.')
    return found


def generate_document(document, writer, *, model, limit=5, batch_size=5, save):
    plan = generation_plan(document, limit=limit, batch_size=batch_size)
    output = deepcopy(document)
    selected = set(plan['selected_rule_ids'])
    rows = [r for r in output['rules'] if r['rule_id'] in selected]
    state = {'provider': 'gemini', 'model': model, 'status': 'in_progress',
             'selected_count': len(rows), 'processed_count': 0, 'generated_count': 0,
             'completed_batches': 0, 'usage': {}}
    output['generation'] = state
    save(output)
    try:
        for start in range(0, len(rows), batch_size):
            batch = rows[start:start + batch_size]
            result, usage = writer.write(batch, output['writing_guide'])
            explanations = validate_reply(result, batch)
            for row in batch:
                row['explanation'] = explanations[row['rule_id']]
            state['processed_count'] += len(batch)
            state['generated_count'] += sum(value is not None for value in explanations.values())
            state['completed_batches'] += 1
            for key, value in usage.items():
                state['usage'][key] = state['usage'].get(key, 0) + value
            save(output)
    except Exception:
        state['status'] = 'failed'
        save(output)
        raise
    state['status'] = 'completed'
    save(output)
    return output
