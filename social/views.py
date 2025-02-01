from django.shortcuts import render, redirect, get_object_or_404
from .forms import CommentForm, ProfileUpdateForm, PostForm
from django.contrib.auth.models import User
from .models import Post, Profile
from django.contrib.auth.decorators import login_required

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

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('profile', username=request.user.username)
    else:
        form = PostForm()
    return render(request, 'social/create_post.html', {'form': form})

def post_detail(request, post_id):
    post = Post.objects.get(id=post_id)
    comments = post.comments.all()

    if 'profile_url' not in request.session:
        request.session['profile_url'] = request.META.get('HTTP_REFERER', '/')
        
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            if post.author != request.user:
                return redirect(f'/social/profile/{post.author.username}/')

            return redirect(request.session.get('profile_url', '/'))

    else:
        form = CommentForm()

    return render(request, 'social/post_detail.html', {
        'post': post,
        'comments': comments,
        'form': form,
    })



@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user == post.author:
        post.delete()
    return redirect('profile', username=request.user.username)