from django.shortcuts import render, redirect

def index(request):
    if not request.user.is_authenticated:  
        return redirect('welcome')
    return render(request, 'home.html') 