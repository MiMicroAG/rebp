@echo off
echo 不動産事業計画 Webアプリケーションを起動します...
echo.

cd /d "%~dp0"

REM 仮想環境の確認
if not exist ".venv\Scripts\activate.bat" (
    echo 仮想環境が見つかりません。setup.batを先に実行してください。
    pause
    exit /b 1
)

REM 仮想環境を有効化
call .venv\Scripts\activate.bat

REM 依存関係のチェック
python -c "import flask" 2>nul
if errorlevel 1 (
    echo 依存関係がインストールされていません。インストール中...
    pip install -r requirements.txt
)

echo.
echo Webアプリケーションを起動しています...
echo ブラウザで http://127.0.0.1:5000 にアクセスしてください
echo.
echo ログイン情報:
echo   管理者: admin / admin123
echo   一般ユーザー: user / user123
echo.
echo 終了するには Ctrl+C を押してください
echo.

python app.py
