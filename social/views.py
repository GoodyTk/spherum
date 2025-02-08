from django.shortcuts import render, redirect, get_object_or_404
from .forms import CommentForm, ProfileUpdateForm, PostForm
from django.contrib.auth.models import User
from .models import FriendRequest, Like, Post, Profile, Comment
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from django.http import JsonResponse, HttpResponseRedirect

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

    sent_request_exists = FriendRequest.objects.filter(from_user=request.user, to_user=user).exists()

    return render(request, 'social/profile.html', {
        'user': user,
        'profile': profile,
        'sent_request_exists': sent_request_exists, 
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

def post_detail(request, pk):
    post = Post.objects.get(id=pk)
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

class CommentLikeToggle(View):
    def post(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, pk=self.kwargs.get('pk'))
        like_qs = Like.objects.filter(comment=comment, user=request.user)
        
        if like_qs.exists():
            like_qs.delete()
            liked = False
        else:
            Like.objects.create(comment=comment, user=request.user)
            liked = True

        like_count = comment.comment_likes.count()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"liked": liked, "like_count": like_count})
        
        return redirect(request.META.get('HTTP_REFERER', '/'))

class PostLikeToggle(View):
    def post(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=self.kwargs.get('pk'))
        like_qs = Like.objects.filter(post=post, user=request.user)

        if like_qs.exists():
            like_qs.delete()
            #liked = False
        else:
            Like.objects.create(post=post, user=request.user)
            #liked = True

        #like_count = post.post_likes.count()

        return HttpResponseRedirect(post.get_absolute_url())
    
@login_required
def send_friend_request(request, user_id):
    user = get_object_or_404(User, id=user_id)
    to_user = get_object_or_404(User, id=user_id)
    
    if not FriendRequest.objects.filter(from_user=request.user, to_user=to_user).exists() and \
       not request.user.profile.friends.filter(id=to_user.profile.id).exists():
        FriendRequest.objects.create(from_user=request.user, to_user=to_user)

    return redirect('profile', username=user.username)

@login_required
def accept_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id)
    
    if friend_request.to_user == request.user:
        friend_request.accept()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})

@login_required
def decline_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id)
    
    if friend_request.to_user == request.user:
        friend_request.decline()  
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})

@login_required
def remove_friend(request, user_id):
    friend = get_object_or_404(User, id=user_id)
    
    if request.user.profile.friends.filter(id=friend.profile.id).exists():
        request.user.profile.friends.remove(friend.profile)
        friend.profile.friends.remove(request.user.profile)

    return redirect('profile', user_id=request.user.id)

