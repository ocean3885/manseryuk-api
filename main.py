from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import calenda_data

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(calenda_data.router)
