# ============================================================
# 智慧养老后端一键启动脚本
# 用法：在 D:\桌面\houduan 目录下右键“使用 PowerShell 运行”，
#       或在 PowerShell 中执行：  .\start_all.ps1
# 会自动弹出两个窗口，分别运行：
#   窗口1  AI/业务后端 (FastAPI, 端口8000)  —— base 环境
#   窗口2  视频/跌倒后端 (Flask,  端口5001) —— deeplearning 环境
# 关闭对应窗口即停止该服务。
# ============================================================

$ROOT = "D:\桌面\houduan"

# D 盘上的两个解释器（都在 D 盘，不污染 C 盘）
$PY_BASE = "D:\79458\Documents\anaconda3\python.exe"
$PY_DL   = "D:\79458\Documents\anaconda3\envs\deeplearning\python.exe"

# 窗口1：FastAPI 主后端（AI问答 / 用药 / 健康 / 定时提醒 / TTS）
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$ROOT\smart_elderly_care'; Write-Host '=== FastAPI 业务后端 端口8000 (base) ===' -ForegroundColor Green; & '$PY_BASE' main.py"
)

# 稍等片刻，避免两个窗口同时刷屏
Start-Sleep -Seconds 1

# 窗口2：Flask 视频监控 / 跌倒检测后端
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$ROOT\smart_elderly_care_backend'; Write-Host '=== Flask 视频/跌倒后端 端口5001 (deeplearning) ===' -ForegroundColor Cyan; & '$PY_DL' app.py"
)

Write-Host ""
Write-Host "已启动两个后端窗口：" -ForegroundColor Yellow
Write-Host "  FastAPI 业务后端 : http://127.0.0.1:8000/docs"
Write-Host "  Flask  视频后端  : http://127.0.0.1:5001/"
Write-Host ""
Write-Host "停止服务：直接关闭弹出的两个窗口即可。" -ForegroundColor Yellow
