@echo off
REM Start Mock Services for Halcytone Content Generator (Windows)
setlocal enabledelayedexpansion

REM Configuration
set PROJECT_ROOT=%~dp0..
set COMPOSE_FILE=%PROJECT_ROOT%\docker-compose.mocks.yml
set TIMEOUT=30

echo [%date% %time%] Starting Halcytone Mock Services...

REM Check if Docker is running
echo [INFO] Checking Docker availability...
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)
echo [INFO] Docker is running

REM Check if docker-compose is available
echo [INFO] Checking Docker Compose availability...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    docker compose version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Neither 'docker-compose' nor 'docker compose' is available.
        echo [ERROR] Please install Docker Compose and try again.
        pause
        exit /b 1
    )
    set COMPOSE_CMD=docker compose
) else (
    set COMPOSE_CMD=docker-compose
)
echo [INFO] Docker Compose available: !COMPOSE_CMD!

REM Check if services are already running
echo [INFO] Checking if mock services are already running...
curl -s http://localhost:8001/health >nul 2>&1
set CRM_RUNNING=!errorlevel!
curl -s http://localhost:8002/health >nul 2>&1
set PLATFORM_RUNNING=!errorlevel!

if !CRM_RUNNING! equ 0 if !PLATFORM_RUNNING! equ 0 (
    echo [SUCCESS] Mock services are already running!
    echo CRM Service: http://localhost:8001/docs
    echo Platform Service: http://localhost:8002/docs
    if not "%1"=="--force" if not "%1"=="-f" (
        pause
        exit /b 0
    )
    echo [INFO] Force restart requested...
)

REM Change to project root
cd /d "%PROJECT_ROOT%"

REM Stop existing services
echo [INFO] Stopping any existing mock services...
!COMPOSE_CMD! -f "%COMPOSE_FILE%" down --remove-orphans >nul 2>&1

REM Kill any processes on the ports (Windows approach)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do (
    echo [WARNING] Killing process on port 8001...
    taskkill /pid %%a /f >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8002 ^| findstr LISTENING') do (
    echo [WARNING] Killing process on port 8002...
    taskkill /pid %%a /f >nul 2>&1
)

timeout /t 2 >nul

echo [INFO] Building Docker images...
!COMPOSE_CMD! -f "%COMPOSE_FILE%" build --no-cache
if errorlevel 1 (
    echo [ERROR] Failed to build Docker images
    pause
    exit /b 1
)

echo [INFO] Starting services...
!COMPOSE_CMD! -f "%COMPOSE_FILE%" up -d
if errorlevel 1 (
    echo [ERROR] Failed to start services
    pause
    exit /b 1
)

echo [INFO] Waiting for services to become healthy...
set /a count=0
set /a max_attempts=%TIMEOUT%/2

:wait_loop
if !count! geq !max_attempts! (
    echo.
    echo [ERROR] Services failed to become healthy within %TIMEOUT% seconds
    !COMPOSE_CMD! -f "%COMPOSE_FILE%" logs --tail=20
    pause
    exit /b 1
)

curl -s -f http://localhost:8001/health >nul 2>&1
set CRM_HEALTHY=!errorlevel!
curl -s -f http://localhost:8002/health >nul 2>&1
set PLATFORM_HEALTHY=!errorlevel!

if !CRM_HEALTHY! equ 0 if !PLATFORM_HEALTHY! equ 0 (
    echo.
    echo [SUCCESS] All services are healthy!
    goto :test_services
)

echo|set /p="."
timeout /t 2 >nul
set /a count+=1
goto :wait_loop

:test_services
echo [INFO] Testing services with sample requests...

curl -s -X GET "http://localhost:8001/contacts" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] CRM service test failed
    pause
    exit /b 1
)
echo [SUCCESS] CRM service responding

curl -s -X GET "http://localhost:8002/content" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Platform service test failed
    pause
    exit /b 1
)
echo [SUCCESS] Platform service responding

echo [SUCCESS] All services tested successfully!

REM Show service information
echo.
echo ============================================
echo Mock Services Information:
echo.
echo 🔧 CRM Service:
echo    - Health: http://localhost:8001/health
echo    - API Docs: http://localhost:8001/docs
echo    - OpenAPI: http://localhost:8001/openapi.json
echo.
echo 🌐 Platform Service:
echo    - Health: http://localhost:8002/health
echo    - API Docs: http://localhost:8002/docs
echo    - OpenAPI: http://localhost:8002/openapi.json
echo.
echo 📊 Service Status:
!COMPOSE_CMD! -f "%COMPOSE_FILE%" ps
echo.
echo 📝 View logs: docker-compose -f docker-compose.mocks.yml logs -f
echo 🛑 Stop services: docker-compose -f docker-compose.mocks.yml down
echo.
echo [SUCCESS] Mock services are ready! 🚀
echo ============================================

pause