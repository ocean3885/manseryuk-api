module.exports = {
    apps: [{
        name: "bazi-api",
        script: "gunicorn", // 가상환경 활성화 상태라면 gunicorn만 써도 됩니다.
        args: "-w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000",
        exec_mode: "fork",  // gunicorn이 자체적으로 워커를 관리하므로 fork 모드가 적합합니다.
        interpreter: "none", // Node.js로 해석하지 않도록 설정
        cwd: "./",           // 현재 폴더를 작업 디렉토리로 설정
    }]
}