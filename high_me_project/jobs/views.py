from django.shortcuts import render

# Create your views here.
def index(request):
    # あとで求人データを渡しますが、まずは画面表示だけ確認
    return render(request, 'jobs/index.html')

def favorites(request):
    """お気に入り画面 (画像2)"""
    return render(request, 'jobs/favorites.html')

def work_schedule(request):
    """はたらく画面 (画像3)"""
    return render(request, 'jobs/work_schedule.html')

def messages(request):
    """メッセージ画面 (画像4)"""
    return render(request, 'jobs/messages.html')