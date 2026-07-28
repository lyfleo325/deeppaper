# ============================================================
# Paper Automation - Windows Task Scheduler Setup
# 使用 schtasks.exe 创建每周一/周三 12:10 运行的定时任务
# ============================================================

param(
    [switch]$Remove,
    [switch]$Status,
    [switch]$RunNow,
    [string]$PythonPath = "C:\Users\Leo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
)

$ErrorActionPreference = "Stop"

$TaskName = "PaperAutomation"
$ScriptDir = "C:\Users\Leo\Documents\PaperAutomation"
$MainScript = Join-Path $ScriptDir "main.py"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Paper Automation - Task Scheduler Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Python:  $PythonPath"
Write-Host "Script:  $MainScript"
Write-Host ""

if ($Status) {
    Write-Host "=== Current Task Status ===" -ForegroundColor Yellow
    schtasks /Query /TN $TaskName /FO LIST /V 2>&1
    exit 0
}

if ($Remove) {
    Write-Host "Removing task..." -ForegroundColor Yellow
    schtasks /Delete /TN $TaskName /F 2>&1
    Write-Host "Task removed." -ForegroundColor Green
    if (-not $RunNow) { exit 0 }
}

# Remove existing task if any
schtasks /Delete /TN $TaskName /F 2>$null

# Create task: Run every Monday AND Thursday at 11:00
# SCHTASKS syntax: /SC WEEKLY /D MON,WED /ST 12:10
$pipAction = "`"$PythonPath`" -m pip install PyYAML --quiet"; $action = "`"$PythonPath`" `"$MainScript`""; $fullAction = "cmd /c `"$pipAction & $action`""
$cmd = "schtasks /Create /TN `"$TaskName`" /TR `"$fullAction`" /SC WEEKLY /D MON,WED /ST 12:10 /RL LIMITED /F"

Write-Host "Running: schtasks /Create ..." -ForegroundColor Gray
Write-Host ""

$result = cmd /c $cmd 2>&1
Write-Host $result

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  [OK] Task created successfully!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Schedule:" -ForegroundColor Cyan
    Write-Host "  Every Monday    12:10 (Asia/Shanghai)"
    Write-Host "  Every Wednesday  12:10 (Asia/Shanghai)"
    Write-Host ""
    Write-Host "Management:" -ForegroundColor Cyan
    Write-Host "  View status:  .\setup_scheduler.ps1 -Status"
    Write-Host "  Run now:      .\setup_scheduler.ps1 -RunNow"
    Write-Host "  Remove:       .\setup_scheduler.ps1 -Remove"
    Write-Host ""
    Write-Host "Log file: $ScriptDir\logs\automation.log" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "[ERROR] Failed to create task!" -ForegroundColor Red
    Write-Host "Try running as Administrator if the issue persists." -ForegroundColor Yellow
    exit 1
}

if ($RunNow) {
    Write-Host ""
    Write-Host "Running task now..." -ForegroundColor Yellow
    schtasks /Run /TN $TaskName
    Start-Sleep -Seconds 3
    Write-Host "Check logs: $ScriptDir\logs\automation.log" -ForegroundColor Cyan
}
