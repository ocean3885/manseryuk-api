module.exports = {
    apps: [{
        name: "bazi-api",
        // 가상환경 내의 gunicorn 절대 경로를 적어주는 것이 가장 에러가 없습니다.
        script: "./venv/bin/gunicorn",
        args: "-w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000",
        cwd: "/var/www/manseryuk-api", // 프로젝트의 절대 경로
        instances: 1,
        autorestart: true,
        watch: false,
        env: {
            NODE_ENV: "production",
        }
    }]
}