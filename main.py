from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import root
from fastapi.responses import JSONResponse
from fastapi import status
from fastapi.exceptions import RequestValidationError
from fastapi import Request

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # 사용자가 참고할 수 있는 올바른 예시 URL 구성
    example_url = "/?year=1995&month=5&day=12&hour=14&min=30&sl=sol&gen=남"
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": "필수 입력 값이 누락되었거나 형식이 올바르지 않습니다.",
            "correct_usage": f"아래와 같은 형식으로 요청을 보내주세요.",
            "example": example_url,
            "required_fields": {
                "year": "int (연도)",
                "month": "str (월, 예: '5')",
                "day": "str (일, 예: '12')",
                "hour": "int (시간, 0-23)",
                "min": "int (분, 0-59)",
                "sl": "str ('sol' ,'lun', 'lun_y')",
                "gen": "str ('남' , '여')"
            }
        },
    )

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(root.router)
