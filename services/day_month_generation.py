"""일주·월지의 일반적이고 감성적인 해설을 조회 이후 생성한다."""
import json
import logging
import os
import re

import httpx

from core.day_month_database import (
    BRANCHES, STEMS, claim_generation, fail_generation, finish_generation,
)
from services.interpretation_generation import read_json

logger = logging.getLogger(__name__)
DEFAULT_MODEL = 'gemini-3.1-flash-lite'
STEM_KR = '갑을병정무기경신임계'
BRANCH_KR = '자축인묘진사오미신유술해'

SYSTEM_PROMPT = '''당신은 만세력 서비스의 일주·월지 조합 해설을 쓰는 한국어 작가입니다.
입력된 일주와 월지의 명리학적 상징을 약 1,000자 내외의 감성적이고 읽기 쉬운 산문으로 풀어 주세요.
일주의 이미지와 월지의 계절감을 구체적으로 엮고, 이 조합의 고유한 분위기가 느껴지게 쓰세요.
뻔한 칭찬, 반복 문장, 과도한 전문 용어, 도입·결론의 고정 문구는 피하세요.
이 글은 일주·월지 조합의 일반적인 상징 해설입니다. 다른 기둥이나 관계의 실제 성립,
통근·세력·손상, 직업·재물·결혼·건강·미래 사건을 지어내거나 확정하지 마세요.
개인의 실제 성격이나 삶을 확정하지 말고 상징과 분위기를 자연스럽게 서술하세요.
면책 문구나 작성 과정 설명 없이 해설 본문만 작성하세요.
반환값은 {"explanation":"해설 본문"} 형식의 JSON만 사용하세요.'''


def interpretation_enabled() -> bool:
    return os.environ.get('DAY_MONTH_INTERPRETATION_ENABLED', '').lower() in ('1', 'true', 'yes')


def request_explanation(day_pillar: str, month_branch: str) -> tuple[str, str]:
    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        raise RuntimeError('Gemini API 키가 설정되지 않았습니다.')
    model = os.environ.get('GEMINI_MODEL') or DEFAULT_MODEL
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,100}', model):
        raise ValueError('Gemini 모델명 형식이 잘못됐습니다.')
    stem = STEM_KR[STEMS.index(day_pillar[0])]
    day_branch = BRANCH_KR[BRANCHES.index(day_pillar[1])]
    month = BRANCH_KR[BRANCHES.index(month_branch)]
    prompt = {'day_pillar': f'{stem}{day_branch}({day_pillar})',
              'month_branch': f'{month}({month_branch})',
              'month_label': f'{month}월({month_branch}月)'}
    body = {
        'systemInstruction': {'parts': [{'text': SYSTEM_PROMPT}]},
        'contents': [{'role': 'user', 'parts': [{'text': json.dumps(prompt, ensure_ascii=False)}]}],
        'generationConfig': {
            'responseMimeType': 'application/json',
            'responseSchema': {'type': 'OBJECT', 'required': ['explanation'],
                               'properties': {'explanation': {'type': 'STRING'}}},
            'temperature': 0.7,
            'maxOutputTokens': 4096,
        },
    }
    with httpx.Client(timeout=60, follow_redirects=False) as client:
        response = client.post(
            f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
            headers={'x-goog-api-key': key}, json=body)
    if response.status_code != 200:
        raise RuntimeError(f'Gemini 생성 요청 실패: HTTP {response.status_code}')
    try:
        candidate = response.json()['candidates'][0]
        if candidate.get('finishReason') != 'STOP':
            raise ValueError('생성이 정상 완료되지 않았습니다.')
        raw = ''.join(part.get('text', '') for part in candidate['content']['parts']
                      if not part.get('thought'))
        content = read_json(raw)
        if not isinstance(content, dict) or set(content) != {'explanation'}:
            raise ValueError('해설 응답 형식이 잘못됐습니다.')
        explanation = content['explanation']
        if not isinstance(explanation, str) or not 500 <= len(explanation.strip()) <= 1200:
            raise ValueError('해설 길이가 허용 범위를 벗어났습니다.')
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise ValueError('Gemini 해설 응답을 검증하지 못했습니다.') from error
    return explanation.strip(), model


def generate_queued(day_pillar: str, month_branch: str, database):
    """FastAPI 응답 이후 실행. 실패는 대기열에 기록하고 기본 조회는 유지한다."""
    try:
        attempt = claim_generation(day_pillar, month_branch, database)
        if attempt is None:
            return
        explanation, model = request_explanation(day_pillar, month_branch)
        finish_generation(day_pillar, month_branch, attempt, explanation, model, database)
    except Exception as error:
        if 'attempt' in locals() and attempt is not None:
            try:
                fail_generation(day_pillar, month_branch, attempt, database)
            except Exception:
                logger.exception('일주·월지 생성 실패 상태를 저장하지 못했습니다.')
        logger.warning('일주·월지 해설 생성 실패 (%s, %s): %s',
                       day_pillar, month_branch, type(error).__name__)
