from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import root
from fastapi.exceptions import RequestValidationError

app = FastAPI()

from starlette.exceptions import HTTPException as StarletteHTTPException
from core.api_errors import http_error_handler, validation_error_handler, unexpected_error_handler

app.add_exception_handler(StarletteHTTPException, http_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, unexpected_error_handler)

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
