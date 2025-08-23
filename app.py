"""
Real Estate Business Plan Web Application
不動産事業計画Webアプリケーション

Flask-based web application for managing real estate business planning
with authentication, YAML configuration editing, and 40-year financial projections.
"""
import os
import yaml
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd

# Import our calculation modules
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from income import compute_income_from_config
from expenses import compute_expenses_from_config
from depreciation import compute_depreciation_from_config
from loan import loan_schedule_annually
from tax import compute_annual_taxes
from cashflow import compute_cashflow_from_config
from utils import to_float, to_int

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # 本番環境では変更してください

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'ログインが必要です。'

# Simple user model (本番環境ではデータベースを使用してください)
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

# Demo users (本番環境ではデータベースから読み込んでください)
users = {
    'admin': User('admin', 'admin', generate_password_hash('admin123')),
    'user': User('user', 'user', generate_password_hash('user123'))
}

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

def load_config():
    """YAML設定ファイルを読み込み"""
    config_path = 'project_config.yml'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        # デフォルト設定を返す
        return {
            'elapsed_years': 15,
            'purchase_price': '420,000,000',
            'initial_capital_ratio': 0.25,
            'loan': {
                'annual_rate': 0.035,
                'years': 35,
                'start_month': 4
            },
            'building': {
                'cost': '35,654,400',
                'statutory_life': 34
            },
            'equipment': {
                'cost': 0,
                'statutory_life': 15
            },
            'tax': {
                'land_assessed_value': '88,559,000',
                'building_assessed_value': '35,654,400',
                'land_area_m2': 273.76,
                'units': 12
            }
        }

def save_config(config):
    """YAML設定ファイルを保存"""
    config_path = 'project_config.yml'
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def calculate_all_data():
    """すべての計算を実行して40年間のデータを取得"""
    try:
        # 各種計算を実行
        income_data = compute_income_from_config('project_config.yml')
        expenses_data = compute_expenses_from_config('project_config.yml')
        depreciation_data = compute_depreciation_from_config('project_config.yml')
        cashflow_data = compute_cashflow_from_config('project_config.yml')
        
        # 40年間のデータに統一
        years = 40
        result = []
        
        # 減価償却データから年間減価償却額を取得
        building_depreciation = depreciation_data.get('building', {}).get('annual_depreciation', [])
        equipment_depreciation = depreciation_data.get('equipment', {}).get('annual_depreciation', [])
        
        for year in range(1, years + 1):
            # 減価償却額の計算（年次インデックスに注意）
            building_dep = building_depreciation[year - 1] if year - 1 < len(building_depreciation) else 0
            equipment_dep = equipment_depreciation[year - 1] if year - 1 < len(equipment_depreciation) else 0
            total_depreciation = building_dep + equipment_dep
            
            year_data = {
                'year': year,
                'income': income_data[year - 1].get('annual_income', 0) if year - 1 < len(income_data) else 0,
                'expenses': expenses_data[year - 1].get('total_expenses', 0) if year - 1 < len(expenses_data) else 0,
                'depreciation': total_depreciation,
                'cashflow': cashflow_data[year - 1].get('cashflow', 0) if year - 1 < len(cashflow_data) else 0,
                'cumulative_cashflow': cashflow_data[year - 1].get('cumulative_cashflow', 0) if year - 1 < len(cashflow_data) else 0,
                'loan_balance': cashflow_data[year - 1].get('loan_balance_end', 0) if year - 1 < len(cashflow_data) else 0,
                'apr': cashflow_data[year - 1].get('apr', 0) if year - 1 < len(cashflow_data) else 0
            }
            result.append(year_data)
        
        return result
    except Exception as e:
        print(f"Error in calculate_all_data: {e}")
        return []

@app.route('/')
def index():
    """メインページ"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    config = load_config()
    return render_template('index.html', config=config)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """ログインページ"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = users.get(username)
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('ユーザー名またはパスワードが正しくありません。')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """ログアウト"""
    logout_user()
    return redirect(url_for('login'))

@app.route('/config', methods=['GET', 'POST'])
@login_required
def config():
    """設定編集ページ"""
    if request.method == 'POST':
        # フォームデータからYAML設定を更新
        # 入力値をユーティリティでサニタイズ（カンマ除去など）
        elapsed_years = to_int(request.form.get('elapsed_years', 15), 15)
        purchase_price = request.form.get('purchase_price', '420,000,000')
        initial_capital_ratio = to_float(request.form.get('initial_capital_ratio', 0.25), 0.25)
        loan_annual_rate = to_float(request.form.get('loan_annual_rate', 0.035), 0.035)
        loan_years = to_int(request.form.get('loan_years', 35), 35)
        loan_start_month = to_int(request.form.get('loan_start_month', 4), 4)
        building_cost = request.form.get('building_cost', '35,654,400')
        building_statutory_life = to_int(request.form.get('building_statutory_life', 34), 34)
        equipment_cost = request.form.get('equipment_cost', '0')
        equipment_statutory_life = to_int(request.form.get('equipment_statutory_life', 15), 15)
        tax_land_assessed_value = request.form.get('tax_land_assessed_value', '88,559,000')
        tax_building_assessed_value = request.form.get('tax_building_assessed_value', '35,654,400')
        tax_land_area_m2 = to_float(request.form.get('tax_land_area_m2', 273.76), 273.76)
        tax_units = to_int(request.form.get('tax_units', 12), 12)

        # income fields
        income_monthly_rent = request.form.get('income_monthly_rent', None)
        income_units = to_int(request.form.get('income_units', 12), 12)

        config_data = {
            'elapsed_years': elapsed_years,
            'purchase_price': purchase_price,
            'initial_capital_ratio': initial_capital_ratio,
            'loan': {
                'annual_rate': loan_annual_rate,
                'years': loan_years,
                'start_month': loan_start_month
            },
            'building': {
                'cost': building_cost,
                'statutory_life': building_statutory_life
            },
            'equipment': {
                'cost': equipment_cost,
                'statutory_life': equipment_statutory_life
            },
            'tax': {
                'land_assessed_value': tax_land_assessed_value,
                'building_assessed_value': tax_building_assessed_value,
                'land_area_m2': tax_land_area_m2,
                'units': tax_units
            }
        }

        # include income section if provided
        if income_monthly_rent is not None and str(income_monthly_rent).strip() != '':
            config_data['income'] = {
                'monthly_rent': to_float(income_monthly_rent, 0.0),
                'units': income_units
            }
        
        if save_config(config_data):
            flash('設定が保存されました。')
        else:
            flash('設定の保存に失敗しました。')
        
        return redirect(url_for('config'))
    
    config_data = load_config()
    return render_template('config.html', config=config_data)

@app.route('/data')
@login_required
def data():
    """データ表示ページ（40年間の表形式）"""
    all_data = calculate_all_data()
    return render_template('data.html', data=all_data)

@app.route('/api/calculate')
@login_required
def api_calculate():
    """計算API（AJAX用）"""
    try:
        all_data = calculate_all_data()
        return jsonify({'success': True, 'data': all_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/config', methods=['GET', 'POST'])
@login_required
def api_config():
    """設定API"""
    if request.method == 'GET':
        config_data = load_config()
        return jsonify(config_data)
    
    elif request.method == 'POST':
        try:
            config_data = request.json
            if save_config(config_data):
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': '設定の保存に失敗しました'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # テンプレートディレクトリを作成
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
