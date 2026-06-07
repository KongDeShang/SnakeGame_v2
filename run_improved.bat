@echo off
chcp 65001 >nul
echo ================================================
echo 贪吃蛇游戏 - 改进版启动脚本
echo ================================================
echo.

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 检查模型文件是否存在
if not exist hand_landmarker.task (
    echo 正在下载手势识别模型文件，请稍候...
    echo (首次运行需要下载约 8MB)
    echo.
    curl -L -o hand_landmarker.task "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
    if errorlevel 1 (
        echo.
        echo [错误] 模型文件下载失败
        echo 请手动下载并放到本目录:
        echo https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
        pause
        exit /b 1
    )
    echo 模型下载完成！
    echo.
)

echo 启动游戏...
echo 提示：请确保摄像头可用，用食指指尖控制蛇的方向
echo.
python main_improved.py

if errorlevel 1 (
    echo.
    echo [错误] 游戏运行出错
    echo 请查看上方错误信息
)

echo.
pause
