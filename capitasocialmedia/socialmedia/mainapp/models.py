from xml.dom import ValidationErr
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
    #each user has a profile and each profile belongs to a user
    #if a user is deleted, their profile is also deleted
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    #will be uploaded to a diretory 
    profile_pic = models.ImageField(upload_to=user_directory_path, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=180, blank=True, null=True)
    private_account = models.BooleanField(default=False)
    email= models.EmailField(max_length=254, blank=True, null=True)
   


class Post(models.Model):
    POST_TYPES = (
        ('image', 'Image'),
        ('video', 'Video'),
        ('text', 'Text'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    file = models.FileField(upload_to=user_directory_path, blank=True, null=True)  
    text_content = models.TextField(blank=True, null=True)
    post_type = models.CharField(max_length=10, choices=POST_TYPES )
    created_at = models.DateTimeField(auto_now_add=True)
    
   
 

    
    
   
    
   


#this is for private profiles
class FollowRequest(models.Model):
    from_user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='follow_requests_sent')
    to_user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='follow_requests_received')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('from_user', 'to_user')

#for public profiles we just create follower without sending requests
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
    
    

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
   

   


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
          
    



class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class Share(models.Model):
   
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self,  **kwargs):
        #used to set id same as post id
        if not self.pk:
            self.id = self.post.id
        super().save( **kwargs)



    

    
   