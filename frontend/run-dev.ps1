$nodeDir = "C:\Program Files\nodejs"
$npmCmd = Join-Path $nodeDir "npm.cmd"

if (-not (Test-Path $npmCmd)) {
    Write-Error "Node.js was not found at $nodeDir. Install Node.js LTS first."
    exit 1
}

$env:Path = "$nodeDir;$env:Path"

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..."
    & $npmCmd install
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

Write-Host "Starting Vite dev server..."
& $npmCmd run dev -- --host 127.0.0.1 --port 5173
