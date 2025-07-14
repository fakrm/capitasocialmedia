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
    #how to show when calling this obeject gets the username from the user model
    def __str__(self):
        return f'{self.user.username} Profile'


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
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f'{self.title} by {self.user.username}'
    
 #to check validations fist and then my validations
    def clean(self):
        super().clean()
        if (self.post_type == 'image' or self.post_type == 'video') and not self.file:
            raise ValidationErr({'file': 'Image and video posts require a file upload.'})
        

    def delete(self, *args, **kwargs):
        # Delete the file when the post is deleted
        if self.file and os.path.isfile(self.file.path):
            os.remove(self.file.path)
        super().delete(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('post_detail', kwargs={'post_id': self.id})

    def total_posts(self):
        return Post.objects.filter(user=self.user).count()
    
   
    
   


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
        
        if not self.pk:
            self.id = self.post.id
        super().save( **kwargs)



    

    
   