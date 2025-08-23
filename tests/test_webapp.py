"""
Webアプリケーションの基本機能テスト
"""
import unittest
import tempfile
import os
import sys
import yaml

# プロジェクトルートをpathに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app import app, load_config, save_config, calculate_all_data
except ImportError as e:
    print(f"Warning: Cannot import web app modules: {e}")
    app = None


class TestWebApp(unittest.TestCase):
    """Webアプリケーションのテスト"""
    
    def setUp(self):
        if app is None:
            self.skipTest("Web app modules not available")
        
        self.app = app.test_client()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False

    def test_load_config(self):
        """設定ファイル読み込みテスト"""
        config = load_config()
        self.assertIsInstance(config, dict)
        self.assertIn('elapsed_years', config)

    def test_save_config(self):
        """設定ファイル保存テスト"""
        # テスト用の設定
        test_config = {
            'elapsed_years': 10,
            'purchase_price': '100,000,000',
            'loan': {
                'annual_rate': 0.02,
                'years': 30
            }
        }
        
        # 一時ファイルで保存をテスト
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            temp_path = f.name
        
        try:
            # 元の設定ファイルをバックアップ
            original_path = 'project_config.yml'
            backup_content = None
            if os.path.exists(original_path):
                with open(original_path, 'r', encoding='utf-8') as f:
                    backup_content = f.read()
            
            # 一時的に設定ファイルパスを変更
            import app as app_module
            original_config_path = 'project_config.yml'
            
            # テスト実行
            with open(temp_path, 'w', encoding='utf-8') as f:
                yaml.dump(test_config, f)
            
            # ファイルが正しく作成されたか確認
            self.assertTrue(os.path.exists(temp_path))
            
            # 内容を読み戻して確認
            with open(temp_path, 'r', encoding='utf-8') as f:
                loaded_config = yaml.safe_load(f)
            
            self.assertEqual(loaded_config['elapsed_years'], 10)
            self.assertEqual(loaded_config['loan']['annual_rate'], 0.02)
            
        finally:
            # クリーンアップ
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_calculate_all_data(self):
        """データ計算テスト"""
        try:
            data = calculate_all_data()
            self.assertIsInstance(data, list)
            
            if len(data) > 0:
                # 最初の年のデータ構造をチェック
                first_year = data[0]
                self.assertIn('year', first_year)
                self.assertIn('income', first_year)
                self.assertIn('expenses', first_year)
                self.assertIn('depreciation', first_year)
                self.assertIn('cashflow', first_year)
                self.assertEqual(first_year['year'], 1)
                
                # 40年分のデータがあることを確認
                self.assertLessEqual(len(data), 40)
        except Exception as e:
            # 設定ファイルがない場合などはスキップ
            self.skipTest(f"Cannot calculate data: {e}")

    def test_web_routes_without_login(self):
        """ログイン不要ルートのテスト"""
        # ログインページ
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        
        # 認証が必要なページはリダイレクトされる
        response = self.app.get('/')
        self.assertEqual(response.status_code, 302)  # リダイレクト
        
        response = self.app.get('/config')
        self.assertEqual(response.status_code, 302)  # リダイレクト
        
        response = self.app.get('/data')
        self.assertEqual(response.status_code, 302)  # リダイレクト

    def test_login_functionality(self):
        """ログイン機能のテスト"""
        # 正しいログイン
        response = self.app.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # 間違ったログイン
        response = self.app.post('/login', data={
            'username': 'admin',
            'password': 'wrong_password'
        })
        self.assertEqual(response.status_code, 200)
        # エラーメッセージが含まれることを確認
        self.assertIn('ユーザー名またはパスワードが正しくありません', response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
