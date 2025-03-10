from django.shortcuts import render, redirect, get_object_or_404
from .forms import CommentForm, PollCommentForm, PollForm, ProfileUpdateForm, PostForm, PublicGroupForm, ReportForm
from django.contrib.auth.models import User
from .models import Choice, Follow, FriendRequest, GroupPost, GroupSubscription, Like, Notification, Poll, Post, Profile, Comment, PublicGroup, Report, Vote
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from django.http import JsonResponse, HttpResponseRedirect
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import authenticate, login
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

    followers = user.followers.all()
    following = user.following.all()

    sent_request_exists = FriendRequest.objects.filter(from_user=request.user, to_user=user).exists()
    is_following = Follow.objects.filter(follower=request.user, following=user).exists()
    return render(request, 'social/profile.html', {
        'user': user,
        'profile': profile,
        'sent_request_exists': sent_request_exists,
        'followers': followers,
        'following': following,
        'is_following': is_following
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
    is_subscribed = GroupSubscription.objects.filter(user=request.user, group=group).exists()
    return render(request, 'social/group_detail.html', {
        'group': group,
        'is_subscribed': is_subscribed,
    })

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
    my_groups = PublicGroup.objects.filter(owner=request.user)
    
    subscribed_groups = PublicGroup.objects.filter(subscribers__user=request.user)

    return render(request, 'social/my_groups.html', {
        'my_groups': my_groups,
        'subscribed_groups': subscribed_groups
    })

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
    friends = []

    friends_from_user = request.user.profile.friends.all()

    friends_to_user = User.objects.filter(profile__friends=request.user.profile)

    friends = list(friends_from_user) + list(friends_to_user)

    friends = list(set(friends))

    return render(request, 'social/friends_list.html', {'friends': friends})

@login_required
def follow_user(request, user_id):
    user_to_follow = get_object_or_404(User, id=user_id)
    
    if not Follow.objects.filter(follower=request.user, following=user_to_follow).exists():
        Follow.objects.create(follower=request.user, following=user_to_follow)
    
    return redirect('profile', username=user_to_follow.username)


@login_required
def unfollow_user(request, user_id):
    user_to_unfollow = get_object_or_404(User, id=user_id)

    follow_instance = Follow.objects.filter(follower=request.user, following=user_to_unfollow).first()
    if follow_instance:
        follow_instance.delete()
    
    return redirect('profile', username=user_to_unfollow.username)

@login_required
def followers_list(request, user_id):
    user = get_object_or_404(User, id=user_id)
    followers = user.followers.all()
    return render(request, 'social/followers_list.html', {
        'user': user,
        'followers': followers,
    })

@login_required
def following_list(request, user_id):
    user = get_object_or_404(User, id=user_id)
    following = user.following.all()
    return render(request, 'social/following_list.html', {
        'user': user,
        'following': following,
    })

def subscribe_to_group(request, group_id):
    group = get_object_or_404(PublicGroup, id=group_id)
    
    if not GroupSubscription.objects.filter(user=request.user, group=group).exists():
        GroupSubscription.objects.create(user=request.user, group=group)
    
    return redirect('group_detail', group_id=group.id)

def unsubscribe_from_group(request, group_id):
    group = get_object_or_404(PublicGroup, id=group_id)
    subscription = GroupSubscription.objects.filter(user=request.user, group=group).first()
    if subscription:
        subscription.delete()
    return redirect('group_detail', group_id=group.id)

@login_required
def create_report(request):
    if request.method == "POST":
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.save()
            return redirect('index') 
    else:
        form = ReportForm()
    return render(request, 'social/create_report.html', {'form': form})

@login_required
def admin_reports(request):
    if not request.user.is_staff:
        return redirect('index')  
    
    reports = Report.objects.all()
    return render(request, 'social/admin_reports.html', {'reports': reports})

@login_required
def change_report_status(request, report_id, status):
    if not request.user.is_staff:
        return redirect('home')

    report = get_object_or_404(Report, id=report_id)
    if status in ['accepted', 'rejected']:
        report.status = status
        report.save()
    
    return redirect('admin_reports')

@login_required
def report_user(request, user_id):
    reported_user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reported_user = reported_user
            report.reporter = request.user
            report.save()
            return redirect('profile', username=reported_user.username)
    else:
        form = ReportForm()

    return render(request, 'social/report_form.html', {'form': form, 'report_type': 'користувача'})

@login_required
def report_group(request, group_id):
    reported_group = get_object_or_404(PublicGroup, id=group_id)
    
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reported_group = reported_group
            report.reporter = request.user
            report.save()
            return redirect('group_detail', group_id=reported_group.id)
    else:
        form = ReportForm()

    return render(request, 'social/report_form.html', {'form': form, 'report_type': 'групу'})

def archive_report(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    report.is_archived = True
    report.save()
    return redirect('admin_reports') 

@login_required
def ban_user_or_group(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    
    if report.report_type == 'user' and report.reported_user:
        report.reported_user.is_active = False  
        report.reported_user.save()
        messages.success(request, f"Користувач {report.reported_user.username} заблокований.")
    elif report.report_type == 'group' and report.reported_group:
        report.reported_group.is_banned = True 
        report.reported_group.save()
        messages.success(request, f"Група {report.reported_group.name} заблокована.")
    
    report.is_banned = True
    report.is_archived = True  
    report.save()
    
    return redirect('admin_reports')

@login_required
def unban_user_or_group(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    
    if report.report_type == 'user' and report.reported_user:
        report.reported_user.is_active = True  
        report.reported_user.save()
        messages.success(request, f"Користувач {report.reported_user.username} розблокований.")
    elif report.report_type == 'group' and report.reported_group:
        report.reported_group.is_banned = False  
        report.reported_group.save()
        messages.success(request, f"Група {report.reported_group.name} розблокована.")
    
    report.is_banned = False
    report.is_archived = False
    report.save()
    
    return redirect('admin_reports')

def group_detail(request, group_id):
    group = get_object_or_404(PublicGroup, id=group_id)

    return render(request, 'social/group_detail.html', {'group': group})

def custom_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if not user.is_active:
                messages.error(request, "Ваш акаунт заблокований.")
                return redirect('login')
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Неправильний логін або пароль.")
    
    return render(request, 'log_system/login.html')

def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

    notifications.update(is_read=True)

    return render(request, 'social/notifications.html', {'notifications': notifications})

def home_view(request):
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

        return render(request, 'home.html', {
            'unread_notifications': unread_notifications,
            'notifications': notifications,
        })
    else:
        return render(request, 'home.html')