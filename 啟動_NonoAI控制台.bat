@echo off
chcp 65001 >nul
title NonoAI 異質個人 AI 叢集控制台軟體
color 0B
echo =====================================================================
echo  ⚡ NonoAI: 異質個人 AI 叢集排程與去中心化兩平面控制台軟體
echo     (Heterogeneous Personal AI Cluster Control Center)
echo =====================================================================
echo.
echo [*] 正在啟動叢集服務中，請稍候...
echo.

python run_app.py

if %errorlevel% neq 0 (
    echo.
    echo [!] 程式執行發生異常，請檢查 Python 環境。
    pause
)
