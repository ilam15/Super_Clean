@echo off
setlocal

:: Switch to script directory
cd /d "%~dp0"

echo [1/3] Starting Redis (requires Docker)...
docker run --name auto-dub-redis -p 6379:6379 -d redis:alpine >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Docker failed or Redis already running. Trying to start existing container...
    docker start auto-dub-redis >nul 2>&1
)

:: Wait a sec for Redis
timeout /t 2 >nul

echo [2/3] Starting Celery Worker...
start "Celery Worker" cmd /k "title Celery Worker && set PYTHONPATH=. && celery -A app.tasks.celery_app worker --loglevel=info --pool=solo"

echo [3/3] Starting FastAPI App...
start "FastAPI Server" cmd /k "title FastAPI Server && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo.
echo Pipeline is running!
echo API Docs: http://localhost:8000/docs
echo Redis: localhost:6379
echo.
echo Press any key to exit this launcher (sub-processes will stay open)...
pause >nul
