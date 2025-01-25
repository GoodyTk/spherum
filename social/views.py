from django.shortcuts import render, redirect, get_object_or_404
from .forms import ProfileUpdateForm
from django.contrib.auth.models import User
from .models import Profile

# Create your views here.

def edit_profile(request, username):
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect("profile", username=request.user.username)
    else:
        form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, 'social/edit_profile.html', {'form': form, 'username': username})

def profile(request, username):
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user)

    return render(request, 'social/profile.html', {
        'user': user,
        'profile': profile,
    })
