from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from PIL import Image
from django.urls import reverse
# Create your models here.

class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.author.username}: {self.content[:30]}"
    
    def get_absolute_url(self):
        return reverse('post_detail', kwargs={'pk': self.pk})
    
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username}"

class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_likes', null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='comment_likes', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('comment', 'user')


class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png')
    bio = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(default=now)
    is_online = models.BooleanField(default=False)
    friends = models.ManyToManyField("self", blank=True, symmetrical=False)

    def __str__(self):
        return f'Профіль {self.user.username}'
    
    def save(self, *args, **kwargs):
        
        super().save(*args, **kwargs)

        img = Image.open(self.avatar.path)
        max_size = (300, 300) 
        img.thumbnail(max_size)
        img.save(self.avatar.path)

class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, related_name="sent_requests", on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name="received_requests", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def accept(self):
        self.to_user.profile.friends.add(self.from_user.profile)
        self.from_user.profile.friends.add(self.to_user.profile)
        self.delete()

    def decline(self):
        self.delete()

class Poll(models.Model):  
    question = models.CharField(max_length=255)  
    created_at = models.DateTimeField(auto_now_add=True)  
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="polls")  # Автор опроса  

    def __str__(self):  
        return self.question  

class Choice(models.Model):  
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="choices")  
    text = models.CharField(max_length=255)  
    votes = models.IntegerField(default=0)  

    def __str__(self):  
        return self.text  

    def get_percentage(self):
        total_votes = self.poll.votes.count()
        if total_votes == 0:
            return 0
        return (self.votes / total_votes) * 100
    
class Vote(models.Model):  
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="votes")  
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="votes")  
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)  
    voted_at = models.DateTimeField(auto_now_add=True)  

    class Meta:  
        unique_together = ('user', 'poll')

class PollComment(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='poll_comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on poll: {self.poll.question}"
    
class PublicGroup(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_groups')
    cover_image = models.ImageField(upload_to='group_covers/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class GroupPost(models.Model):
    group = models.ForeignKey(PublicGroup, on_delete=models.CASCADE, related_name='posts')  
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_posts')
    content = models.TextField() 
    image = models.ImageField(upload_to='group_posts/', blank=True, null=True)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  

    def __str__(self):
        return f"Post by {self.author.username} in {self.group.name}: {self.content[:30]}"

    def get_absolute_url(self):
        return reverse('group_post_detail', kwargs={'group_id': self.group.id, 'post_id': self.id})
    

