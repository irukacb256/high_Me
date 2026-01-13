from django.shortcuts import render

# これが足りないためエラーになっています
from django.shortcuts import render

def onboarding1(request):
    return render(request, 'accounts/onboarding1.html')

def onboarding2(request):
    return render(request, 'accounts/onboarding2.html')

def onboarding3(request):
    return render(request, 'accounts/onboarding3.html')

# 次のステップで使う関数も今のうちに作っておくとエラーを防げます
def gate(request):
    return render(request, 'accounts/gate.html')

def signup(request):
    return render(request, 'accounts/signup.html')

# accounts/views.py

def login_view(request): # 他の関数と名前が被らないように login_view とします
    return render(request, 'accounts/login.html')