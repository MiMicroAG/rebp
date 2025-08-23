# 不動産事業計画Webアプリケーション起動スクリプト

Write-Host "======================================" -ForegroundColor Green
Write-Host "  不動産事業計画 Webアプリケーション" -ForegroundColor Green  
Write-Host "======================================" -ForegroundColor Green
Write-Host

# 仮想環境をチェック
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "仮想環境が見つかりません。セットアップを実行してください。" -ForegroundColor Red
    Write-Host "python -m venv .venv"
    Write-Host ".\.venv\Scripts\Activate.ps1"
    Write-Host "pip install -r requirements.txt"
    Read-Host "Enterキーを押して終了"
    exit 1
}

# 仮想環境を有効化
Write-Host "仮想環境を有効化中..." -ForegroundColor Yellow
& ".\.venv\Scripts\Activate.ps1"

# 依存関係をチェック
Write-Host "依存関係をチェック中..." -ForegroundColor Yellow
try {
    python -c "import flask, flask_login, yaml" 2>$null
} catch {
    Write-Host "依存関係をインストール中..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Webアプリケーションを起動
Write-Host
Write-Host "Webアプリケーションを起動中..." -ForegroundColor Green
Write-Host "ブラウザで http://127.0.0.1:5000 にアクセスしてください" -ForegroundColor Cyan
Write-Host
Write-Host "ログイン情報:" -ForegroundColor White
Write-Host "  管理者: admin / admin123" -ForegroundColor White
Write-Host "  一般  : user / user123" -ForegroundColor White
Write-Host
Write-Host "終了するには Ctrl+C を押してください" -ForegroundColor Yellow
Write-Host "======================================" -ForegroundColor Green
Write-Host

python app.py
