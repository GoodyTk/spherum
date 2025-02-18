from django.shortcuts import render, redirect, get_object_or_404
from .forms import CommentForm, PollCommentForm, PollForm, ProfileUpdateForm, PostForm, PublicGroupForm
from django.contrib.auth.models import User
from .models import Choice, FriendRequest, GroupPost, Like, Poll, Post, Profile, Comment, PublicGroup, Vote
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from django.http import JsonResponse, HttpResponseRedirect
from django.views.generic import ListView, DetailView
from django.db.models import Q
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
        else:
            Like.objects.create(post=post, user=request.user)

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

class PollListView(ListView):
    model = Poll
    template_name = "social/poll_list.html"
    context_object_name = "polls"

class PollDetailView(DetailView):
    model = Poll
    template_name = "social/poll_detail.html"
    context_object_name = "poll"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated:
            context["has_voted"] = self.object.votes.filter(user=user).exists()
            context["comment_form"] = PollCommentForm()  
            context["comments"] = self.object.poll_comments.all() 
        else:
            context["has_voted"] = False  

        return context

    def post(self, request, *args, **kwargs):
        poll = self.get_object()
        if request.user.is_authenticated:
            form = PollCommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.poll = poll  
                comment.author = request.user 
                comment.save()
            return redirect('poll_detail', pk=poll.pk)  
        return super().post(request, *args, **kwargs)

@login_required
def vote(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    
    if Vote.objects.filter(user=request.user, poll=poll).exists():
        return redirect("poll_detail", pk=poll_id) 
    
    choice_id = request.POST.get("choice")
    choice = get_object_or_404(Choice, id=choice_id, poll=poll)
    
    Vote.objects.create(user=request.user, poll=poll, choice=choice)
    
    choice.votes += 1
    choice.save()
    
    return redirect("poll_detail", pk=poll_id)

@login_required
def create_poll(request):
    if request.method == "POST":
        poll_form = PollForm(request.POST)
        if poll_form.is_valid():
            poll = poll_form.save(commit=False)
            poll.author = request.user
            poll.save()

            choices = request.POST.getlist('choices[]') 
            for choice_text in choices:
                if choice_text.strip():  
                    Choice.objects.create(poll=poll, text=choice_text)

            return redirect('profile', username=request.user.username)

    else:
        poll_form = PollForm()

    return render(request, 'social/create_poll.html', {'poll_form': poll_form})

@login_required
def create_group(request):
    if request.method == 'POST':
        form = PublicGroupForm(request.POST, request.FILES)
        if form.is_valid():
            group = form.save(commit=False)
            group.owner = request.user
            group.save()
            return redirect('group_detail', group_id=group.id) 
    else:
        form = PublicGroupForm()

    return render(request, 'social/create_group.html', {'form': form})

def group_detail(request, group_id):
    group = get_object_or_404(PublicGroup, id=group_id)
    return render(request, 'social/group_detail.html', {'group': group})

@login_required
def create_group_post(request, group_id):
    group = get_object_or_404(PublicGroup, id=group_id)

    if request.user != group.owner and not request.user in group.admins.all():
        return redirect('group_detail', group_id=group.id)  

    if request.method == 'POST':
        content = request.POST.get('content')
        image = request.FILES.get('image') 
        if content:
            post = GroupPost.objects.create(group=group, author=request.user, content=content, image=image)
            return redirect('group_detail', group_id=group.id) 

    return render(request, 'social/create_group_post.html', {'group': group})

def my_groups(request):
    if not request.user.is_authenticated:
        return redirect('login') 
    
    groups = PublicGroup.objects.filter(owner=request.user)
    return render(request, 'social/my_groups.html', {'groups': groups})

@login_required
def manage_group(request, id):
    group = get_object_or_404(PublicGroup, id=id)
    
    if request.user != group.owner:
        return redirect("group_detail", group_id=group.id)
    
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update":
            group.name = request.POST.get("name")
            group.description = request.POST.get("description")
            group.save()
        elif action == "delete":
            group.delete()
            return redirect('my_groups')  
        elif action == "add_admin":
            admin_id = request.POST.get("admin")
            new_admin = User.objects.get(id=admin_id)
            group.admins.add(new_admin)
        elif action == "remove_admin":
            admin_id = request.POST.get("admin")
            remove_admin = User.objects.get(id=admin_id)
            group.admins.remove(remove_admin)

    admins = group.admins.all()
    users = User.objects.exclude(id=group.owner.id)  

    return render(request, 'social/manage_group.html', {
        'group': group,
        'admins': admins,
        'users': users,
    })

def search(request):
    query = request.GET.get('query', '')

    users = User.objects.filter(Q(username__icontains=query))
    groups = PublicGroup.objects.filter(Q(name__icontains=query))

    users_data = [{'username': user.username} for user in users]
    groups_data = [{'id': group.id, 'name': group.name} for group in groups]

    return JsonResponse({'users': users_data, 'groups': groups_data})

def friends_list(request):
    user = request.user

    friends_from = FriendRequest.objects.filter(from_user=user, status='accepted')
    friends_to = FriendRequest.objects.filter(to_user=user, status='accepted')

    friends_ids = set(friends_from.values_list('to_user', flat=True)) | set(friends_to.values_list('from_user', flat=True))
    
    friends = User.objects.filter(id__in=friends_ids)

    return render(request, 'friends_list.html', {'friends': friends})