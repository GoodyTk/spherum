from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from social.utils import create_notification
from .models import Follow, Like, Profile, Comment

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

@receiver(post_save, sender=Comment)
def notify_comment(sender, instance, created, **kwargs):
    if created:
        create_notification(
            instance.post.author,
            'comment',
            f'Пользователь {instance.author.username} прокомментировал ваш пост!'
        )

@receiver(post_save, sender=Like)
def notify_like(sender, instance, created, **kwargs):
    if created:
        create_notification(
            instance.post.author,
            'like',
            f'Пользователь {instance.user.username} лайкнул ваш пост!'
        )

@receiver(post_save, sender=Follow)
def notify_follow(sender, instance, created, **kwargs):
    if created:
        create_notification(
            instance.following,  
            'follow',
            f'Пользователь {instance.follower.username} подписался на вас!'
        )
