# ============================================================
# 一键停止所有后端：杀掉占用 8000 / 5001 端口的进程
# 用法：  .\stop_all.ps1
# ============================================================

foreach ($port in @(8000, 5001)) {
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($conns) {
        foreach ($c in $conns) {
            try {
                Stop-Process -Id $c.OwningProcess -Force -ErrorAction Stop
                Write-Host "已停止端口 $port 的进程 (PID $($c.OwningProcess))" -ForegroundColor Green
            } catch {
                Write-Host "端口 $port 进程停止失败：$($_.Exception.Message)" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "端口 $port 没有在运行的服务" -ForegroundColor DarkGray
    }
}
