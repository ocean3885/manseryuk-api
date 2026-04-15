# manseryuk-api

## 초기 설정 및 실행 가이드 (Setup and Run Guide)

### 1. 프로젝트 클론 (Clone the project)
```bash
git clone <repository-url>
cd manseryuk-api
```

### 2. 가상환경 생성 (Create Virtual Environment)
Python 3.3 이상부터 내장된 `venv` 모듈을 사용하여 가상환경을 생성합니다.
```bash
python -m venv venv
```

### 3. 가상환경 활성화 (Activate Virtual Environment)
사용 중인 운영체제에 맞게 가상환경을 활성화합니다.
- **Windows:**
  ```bash
  .\venv\Scripts\activate
  ```
- **Linux / macOS:**
  ```bash
  source venv/bin/activate
  ```

### 4. 필수 패키지 설치 (Install Requirements)
가상환경이 활성화된 상태에서 `requirements.txt`에 명시된 필수 패키지들을 설치합니다.
```bash
pip install -r requirements.txt
```

### 5. 서버 실행 (Run the Server)
개발 서버를 실행하려면 아래 명령어를 사용하세요.
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 기타 명령어 (Other Commands)
background에서 supervisor를 이용해 프로세스를 관리할 경우 아래 명령어를 참고하세요:
```bash
supervisord -c /etc/supervisord.conf
```
