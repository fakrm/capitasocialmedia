from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
import os

# Utility function to determine upload path
def user_directory_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return f'user_{instance.user.id}/{filename}'

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    profile_pic = models.ImageField(upload_to=user_directory_path, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=180, blank=True, null=True)
    private_account = models.BooleanField(default=False)
    email= models.EmailField(max_length=254, blank=True, null=True)
    def __str__(self):
        return f'{self.user.username} Profile'


class Post(models.Model):
    POST_TYPES = (
        ('image', 'Image'),
        ('video', 'Video'),
        ('text', 'Text'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to=user_directory_path, blank=True, null=True)  # Optional for text posts
    text_content = models.TextField(blank=True, null=True)
    post_type = models.CharField(max_length=10, choices=POST_TYPES)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f'{self.title} by {self.user.username}'
    
    def delete(self, *args, **kwargs):
        # Delete the file when the post is deleted
        if self.file and os.path.isfile(self.file.path):
            os.remove(self.file.path)
        super().delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('post_detail', kwargs={'post_id': self.id})
    
    def __str__(self):
        return f'{self.title} by {self.user.username}'
    
    @property
    def total_likes(self):
        return self.likes.count()
    
      


# In models.py - add these models
class FollowRequest(models.Model):
    from_user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='follow_requests_sent')
    to_user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='follow_requests_received')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('from_user', 'to_user')

class Follower(models.Model):
    follower = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'following')


class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_other_participant(self, user):
        return self.participants.exclude(id=user.id).first()
    
    def __str__(self):
        usernames = [user.username for user in self.participants.all()]
        return f"Chat between {' and '.join(usernames)}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:30]}"     


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']  # Most recent comments first
    
    def __str__(self):
        return f'Comment by {self.user.username} on {self.post.title}'       
    


# Add these to your models.py
class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('post', 'user')  # A user can only like a post once
    
    def __str__(self):
        return f'Like by {self.user.username} on {self.post.title}'    