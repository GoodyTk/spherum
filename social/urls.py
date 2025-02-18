from django.urls import path
from . import views


urlpatterns = [
    path('profile/<str:username>/', views.profile, name='profile'),
    path('profile/<str:username>/edit/', views.edit_profile, name='edit_profile'),
    path('create_post/', views.create_post, name='create_post'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('comment/like/<int:pk>/', views.CommentLikeToggle.as_view(), name='comment-like-toggle'),
    path('post-like-toggle/<int:pk>/', views.PostLikeToggle.as_view(), name='post-like-toggle'),
    path('send_request/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('accept_request/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('decline_request/<int:request_id>/', views.decline_friend_request, name='decline_friend_request'),
    path('remove_friend/<int:user_id>/', views.remove_friend, name='remove_friend'),
    path("", views.PollListView.as_view(), name="poll_list"),
    path("<int:pk>/", views.PollDetailView.as_view(), name="poll_detail"),
    path("<int:poll_id>/vote/", views.vote, name="vote"),
    path('create_poll/', views.create_poll, name='create_poll'),
    path('create_group/', views.create_group, name='create_group'),
    path('group/<int:group_id>/', views.group_detail, name='group_detail'),
    path('group/<int:group_id>/create_post/', views.create_group_post, name='create_group_post'),
    path('my_groups/', views.my_groups, name='my_groups'),
    path('groups/<int:id>/manage/', views.manage_group, name='manage_group'),
    path('search/', views.search, name='search'),
    path('friends/', views.friends_list, name='friends_list')
]
