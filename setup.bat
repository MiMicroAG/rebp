@echo off
echo 不動産事業計画システムのセットアップを開始します...
echo.

cd /d "%~dp0"

REM 仮想環境の作成
echo 1. 仮想環境を作成中...
python -m venv .venv
if errorlevel 1 (
    echo エラー: 仮想環境の作成に失敗しました。
    echo Pythonが正しくインストールされているか確認してください。
    pause
    exit /b 1
)

REM 仮想環境を有効化
echo 2. 仮想環境を有効化中...
call .venv\Scripts\activate.bat

REM 依存関係のインストール
echo 3. 依存関係をインストール中...
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo エラー: 依存関係のインストールに失敗しました。
    pause
    exit /b 1
)

REM テスト実行
echo 4. テストを実行中...
python -m pytest tests/ -v
if errorlevel 1 (
    echo 警告: 一部のテストが失敗しましたが、セットアップは完了しました。
) else (
    echo すべてのテストが成功しました。
)

echo.
echo セットアップが完了しました！
echo.
echo 使用方法:
echo   Webアプリ起動: start_webapp.bat をダブルクリック
echo   コマンドライン: .venv\Scripts\activate.bat でenvを有効化後、pythonコマンドを実行
echo.
pause
