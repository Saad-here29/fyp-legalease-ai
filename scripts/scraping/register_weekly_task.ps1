# kb-v2 C3: register the weekly knowledge-base update as a Windows scheduled task.
#
# Runs scripts\scraping\run_weekly.py every Sunday at 03:00 (scrape the three
# verified sources, validate, stage, embed, write the update log). Run this
# yourself, once, in PowerShell; it doesn't need administrator rights for a
# task that runs as you while you're signed in.
#
#   powershell -ExecutionPolicy Bypass -File scripts\scraping\register_weekly_task.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\scraping\register_weekly_task.ps1 -Unregister
#
# Check it:   Get-ScheduledTask -TaskName "LegalEase weekly KB update" | Get-ScheduledTaskInfo
# Run it now: Start-ScheduledTask -TaskName "LegalEase weekly KB update"
# Output:     backend\storage\kb\scraped\weekly_runs.log  (exit code 0 ok, 3 budget stop, 1 failure)

param(
    [string]$TaskName = "LegalEase weekly KB update",
    [string]$Worktree = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [string]$Python = "E:\Users\fyp-legalease-ai-main\fyp-legalease-ai-main\backend\venv\Scripts\python.exe",
    [string]$At = "03:00",
    [switch]$Unregister
)

if ($Unregister) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed scheduled task '$TaskName'."
    return
}

$backend = Join-Path $Worktree "backend"
$script = Join-Path $Worktree "scripts\scraping\run_weekly.py"
if (-not (Test-Path $Python)) { throw "Python not found: $Python" }
if (-not (Test-Path $script)) { throw "run_weekly.py not found: $script" }

$action = New-ScheduledTaskAction -Execute $Python -Argument "`"$script`"" -WorkingDirectory $backend
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At $At
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 4) `
    -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings `
    -Description "LegalEase: scrape Pakistan Code, KP Code and Federal Shariat Court; validate, stage, embed (kb-v2 C3)" `
    -Force | Out-Null
Write-Host "Registered '$TaskName': every Sunday at $At, running $script in $backend."
