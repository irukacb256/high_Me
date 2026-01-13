from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .models import BusinessProfile, Store

def landing(request):
    """画像3: 事業者向けランディングページ"""
    return render(request, 'business/landing.html')

def signup(request):
    """画像4, 5: 求人掲載アカウント開設（同意とメールアドレス入力）"""
    if request.method == 'POST':
        # 本来はここでメール送信などを行う
        return redirect('biz_verify')
    return render(request, 'business/signup.html')

def verify_docs(request):
    """画像6: 書類アップロード流れ"""
    if request.method == 'POST':
        return redirect('biz_store_setup')
    return render(request, 'business/verify_docs.html')

def store_setup(request):
    """画像7: 店舗情報入力"""
    if request.method == 'POST':
        return redirect('biz_login')
    return render(request, 'business/store_setup.html')

def biz_login(request):
    """★これが足りなかった関数です: 事業者用ログイン画面"""
    if request.method == 'POST':
        # ログインロジック（簡易版）
        return redirect('biz_dashboard')
    return render(request, 'business/login.html')

def dashboard(request):
    """画像8, 9, 10: 事業者管理画面（ダッシュボード）"""
    return render(request, 'business/dashboard.html')