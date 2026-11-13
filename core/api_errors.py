from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from schemas.api_error import ApiErrorResponse
import logging


class ApiError(HTTPException):
    def __init__(self, status_code, code, message, *, field=None, constraints=None):
        super().__init__(status_code, message)
        self.code = code
        self.errors = [dict(field=field, location=['query', field] if field else [],
                            code=code, message=message, constraints=constraints or {})]


def selection_error():
    return ApiError(400, 'invalid_cycle_selection',
                    'daewoon_index 또는 sewoon_year 중 하나만 지정하세요.',
                    constraints={'exactly_one_of': ['daewoon_index', 'sewoon_year']})


def error_response(request: Request, status_code, code, message, errors, detail, headers=None):
    required = dict(year='int (연도)', month="str (월, 예: '5')", day="str (일, 예: '12')",
                    hour='int (시간, 0-23)', min='int (분, 0-59)',
                    sl="str ('sol' ,'lun', 'lun_y')", gen="str ('남' , '여')")
    example = f'{request.url.path}?year=1995&month=5&day=12&hour=14&min=30&sl=sol&gen=남'
    usage = '아래와 같은 형식으로 요청을 보내주세요.'
    if request.url.path == '/cycle-analysis':
        example += '&sewoon_year=2026'
        usage += ' daewoon_index 또는 sewoon_year 중 하나만 지정하세요.'
    body = ApiErrorResponse(code=code, message=message, errors=errors, detail=detail,
                            correct_usage=usage, example=example, required_fields=required)
    return JSONResponse(status_code=status_code, content=body.model_dump(mode='json'), headers=headers)


async def http_error_handler(request, exc):
    internal = exc.status_code >= 500
    code = 'internal_error' if internal else getattr(exc, 'code', f'http_{exc.status_code}')
    message = '서버 처리 중 오류가 발생했습니다.' if internal else str(exc.detail)
    errors = [dict(code=code, message=message)] if internal else getattr(
        exc, 'errors', [dict(code=code, message=message)])
    return error_response(request, exc.status_code, code, message, errors,
                          message if internal else exc.detail, exc.headers)


async def validation_error_handler(request, exc):
    errors = []
    for item in exc.errors():
        location = list(item['loc'])
        errors.append(dict(field=str(location[-1]) if location else None,
                           location=location, code=item['type'], message=item['msg']))
    return error_response(request, 422, 'request_validation_error',
                          '필수 입력 값이 누락되었거나 형식이 올바르지 않습니다.', errors, errors)


async def unexpected_error_handler(request, exc):
    logging.getLogger(__name__).error('Unhandled API error', exc_info=(type(exc), exc, exc.__traceback__))
    message = '서버 처리 중 오류가 발생했습니다.'
    return error_response(request, 500, 'internal_error', message,
                          [dict(code='internal_error', message=message)], message)
