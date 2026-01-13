from django.shortcuts import render

# Create your views here.
def index(request):
    # あとで求人データを渡しますが、まずは画面表示だけ確認
    return render(request, 'jobs/index.html')