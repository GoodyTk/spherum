from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login') 
    else:
        form = CustomUserCreationForm()

    return render(request, 'log_system/register.html', {'form': form})


def welcome_page(request):
    return render(request, 'log_system/welcome.html') 

def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/')