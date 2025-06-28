import email
from shlex import quote
from charset_normalizer import from_bytes
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.db.models import Q
import base64
from django.core.files.base import ContentFile
import tweepy
from .forms import UserRegisterForm, UserLoginForm, ProfileUpdateForm, PostForm
from .models import Profile, Post, Follower, FollowRequest
import json
import base64
import os
import uuid
from .models import Conversation, Message
from django import forms
from .forms import MessageForm
from django.db.models import Max, Count, Q
from django.shortcuts import render

from .forms import CommentForm
from .models import Post, Comment, Like

from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator

from django.contrib.auth.tokens import default_token_generator as token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode



@login_required
def home(request):

    if not request.user.is_authenticated:
        messages.warning(request, 'Please log in first.')
        return redirect('login')  
    elif request.user.is_authenticated:
        try:
            # Get IDs of users the current user follows
            following_ids = Follower.objects.filter(
                follower=request.user.profile
            ).values_list('following__user', flat=True)
            
            # Get posts from users the current user follows (and own posts)
            followed_posts = Post.objects.filter(
                Q(user__in=following_ids) | Q(user=request.user)
            )
            
            # Get public posts from users not followed
            public_posts = Post.objects.filter(
                ~Q(user__in=following_ids),
                ~Q(user=request.user),
                user__profile__private_account=False
            )
            
            # Combine and sort by created_at
            posts = (followed_posts | public_posts).order_by('-created_at')
        except:
            # Fallback if any error occurs (such as Follower table not existing yet)
            posts = Post.objects.filter(
                Q(user=request.user) | Q(user__profile__private_account=False)
            ).order_by('-created_at')
    else:
        # For non-authenticated users, show only public posts
        posts = Post.objects.filter(user__profile__private_account=False).order_by('-created_at')
    
    return render(request, 'home.html', {'posts': posts})


@login_required
def user_search(request):
    if not request.user.is_authenticated:
        messages.warning(request, 'Please log in first.')
        print(request._messages)
        return redirect('login')  
    else:
        query = request.GET.get('q', '')
    if query:
        users = User.objects.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query)
        )
    else:
        users = User.objects.none()
    
    return render(request, 'search_results.html', {'users': users, 'query': query})
    

def explore(request):
    # Your code for the explore page
    return render(request, 'explore.html')
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            reqemail=request.POST.get('email')
             # if email== reqemail:

            if User.objects.filter(email=reqemail).exists():
                messages.error(request, 'Email already exists. Please use a different email.')
                return redirect('register')
            
            user = form.save()
            
           
            # Create profile
            token = str(uuid.uuid4())
            Profile.objects.create(user=user, verification_token=token)
            
            # Send verification email
            verification_url = request.build_absolute_uri(
                reverse('verify_email', args=[token])
            )
            send_mail(
                'Verify your email',
                f'Please click the link to verify your email: {verification_url}',
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            
            messages.success(request, 'Account created! Please verify your email.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})

def verify_email(request, token):
    profile = get_object_or_404(Profile, verification_token=token)
    if profile:
        profile.email_verified = True
        profile.verification_token = None
        profile.save()
        messages.success(request, 'Email verified! You can now log in.')
        return redirect('login')
    else:
        messages.error(request, 'Invalid verification token.')
        return redirect('home')
    


import json
import base64
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import UserLoginForm
from .models import Profile

def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                profile = Profile.objects.get(user=user)
                if profile.email_verified:
                    login(request, user)
                    remember_me = request.POST.get('remember_me', None)
                    response = redirect('home')

                    if remember_me:
                        request.session.set_expiry(1209600)  # 2 weeks

                        # Load existing remembered credentials
                        credentials_raw = request.COOKIES.get('remembered_credentials', '[]')
                        try:
                            decoded = base64.b64decode(credentials_raw.encode()).decode()
                            remembered_credentials = json.loads(decoded)
                        except Exception:
                            remembered_credentials = []

                        # Update or add current user
                        updated = False
                        for cred in remembered_credentials:
                            if cred["username"] == username:
                                cred["password"] = password
                                updated = True
                                break
                        if not updated:
                            remembered_credentials.append({"username": username, "password": password})

                        # Save back to cookie
                        encoded = base64.b64encode(json.dumps(remembered_credentials).encode()).decode()
                        response.set_cookie(
                            'remembered_credentials',
                            encoded,
                            max_age=1209600,
                            httponly=True,
                            samesite='Strict'
                        )
                    else:
                        request.session.set_expiry(0)  # session ends on browser close

                        # Remove credentials if present
                        credentials_raw = request.COOKIES.get('remembered_credentials', '[]')
                        try:
                            decoded = base64.b64decode(credentials_raw.encode()).decode()
                            remembered_credentials = json.loads(decoded)
                        except Exception:
                            remembered_credentials = []

                        remembered_credentials = [
                            c for c in remembered_credentials if c["username"] != username
                        ]

                        if remembered_credentials:
                            encoded = base64.b64encode(json.dumps(remembered_credentials).encode()).decode()
                            response.set_cookie(
                                'remembered_credentials',
                                encoded,
                                max_age=1209600,
                                httponly=True,
                                samesite='Strict'
                            )
                        else:
                            response.delete_cookie('remembered_credentials')

                    messages.success(request, f'Welcome, {username}!')
                    return response
                else:
                    messages.warning(request, 'Please verify your email before logging in.')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        # GET request — pre-fill form with last remembered credentials
        encoded = request.COOKIES.get('remembered_credentials', None)
        if encoded:
            try:
                decoded = base64.b64decode(encoded.encode()).decode()
                credentials = json.loads(decoded)
                last_cred = credentials[-1]
                form = UserLoginForm(initial={
                    'username': last_cred.get('username', ''),
                    'password': last_cred.get('password', '')
                })
                form.fields['username'].widget.attrs.update({'data-remembered': 'true'})
            except Exception:
                form = UserLoginForm()
        else:
            form = UserLoginForm()

    return render(request, 'login.html', {'form': form})


def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')

@login_required
def profile(request):
    
    if request.method == 'POST':
        
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user.profile)
      
       
    user_posts = Post.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'form': form,
        'user_posts': user_posts,
     
        

    }
    return render(request, 'profile.html', context)

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            # Create a new post instance but don't save it yet
            post = form.save(commit=False)
            post.user = request.user
            
            # Check if post is a text post
            if post.post_type == 'text':
                post.file = None
                post.text_content = request.POST.get('text_content')
            else:
                    file = request.FILES.get('file')
                    if file:
                        file_name = file.name.lower()
                        
                        if post.post_type == 'image' and not file_name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                            messages.error(request, 'Only image files are allowed.')
                            return redirect('create_post')
                            
                        if post.post_type == 'video' and not file_name.endswith('.mp4'):
                            messages.error(request, 'Only MP4 videos are allowed.')
                            return redirect('create_post')
            
            post.save()
            messages.success(request, 'Your post has been created!')
            return redirect('home')
    else:
        form = PostForm()
    return render(request, 'create_post.html', {'form': form})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    post.delete()
    messages.success(request, 'Post deleted successfully!')
    return redirect('profile')


import base64
from django.core.files.base import ContentFile

@login_required
def edit_image(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    # Check if the post belongs to the current user or is an image post
    if post.user != request.user or post.post_type != 'image':
        messages.error(request, 'You cannot edit this post.')
        return redirect('home')
    
    return render(request, 'edit_image.html', {'post': post})

@login_required
def toggle_privacy(request):
    if request.method == 'POST':
        profile = request.user.profile
        profile.private_account = not profile.private_account
        profile.save()
        
        status = 'private' if profile.private_account else 'public'
        messages.success(request, f'Your account is now {status}.')
    
    return redirect('profile')



@login_required
def save_edited_image(request, post_id):
    if request.method != 'POST':
        return redirect('home')
    
    post = get_object_or_404(Post, id=post_id)
    
    # Check if the post belongs to the current user
    if post.user != request.user:
        messages.error(request, 'You cannot edit this post.')
        return redirect('home')
    
    # Get the image data from the form
    image_data = request.POST.get('edited_image_data')
    
    if image_data:
        # Remove the data URL prefix to get the base64 string
        format, imgstr = image_data.split(';base64,')
        ext = format.split('/')[-1]
        
        # Generate a unique filename
        filename = f"{post.id}_edited.{ext}"
        
        # Convert base64 to file
        image_file = ContentFile(base64.b64decode(imgstr), name=filename)
        
        # Update the post's file
        post.file = image_file
        post.save()
        
        messages.success(request, 'Image edited successfully!')
    
    return redirect('profile')

@login_required
def create_text_post(request):
    if request.method == 'POST':
        # Handle the form submission
        text_content = request.POST.get('text_content')  # Get the text content from the form

        if text_content:
            # Create a new post with text
            post = Post(user=request.user, post_type='text', text_content=text_content)
            post.save()
            messages.success(request, 'Your text post has been created!')
            return redirect('home')
        else:
            messages.error(request, 'Text content cannot be empty.')
            return redirect('create_text_post')
    return render(request, 'create_text_post.html')


@login_required
def download_file(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    file_path = post.file.path
    
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename={os.path.basename(file_path)}'
            return response
    else:
        messages.error(request, 'File not found.')
        return redirect('home')



# views.py - add these new views
@login_required
def follow_user(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    from_profile = request.user.profile
    to_profile = user_to_follow.profile
    
    # Don't allow self-follow
    if request.user == user_to_follow:
        messages.warning(request, "You cannot follow yourself.")
        return redirect('profile_detail', username=username)
    
    # Check if already following
    if Follower.objects.filter(follower=from_profile, following=to_profile).exists():
        messages.info(request, f"You are already following {username}.")
        return redirect('profile_detail', username=username)
    
    # Check if a follow request already exists
    if FollowRequest.objects.filter(from_user=from_profile, to_user=to_profile).exists():
        messages.info(request, f"You have already sent a follow request to {username}.")
        return redirect('profile_detail', username=username)
    
    # If account is private, create a follow request
    if to_profile.private_account:
        FollowRequest.objects.create(from_user=from_profile, to_user=to_profile)
        messages.success(request, f"Follow request sent to {username}.")
    else:
        # For public accounts, directly create follower relationship
        Follower.objects.create(follower=from_profile, following=to_profile)
        messages.success(request, f"You are now following {username}.")
    
    return redirect('profile_detail', username=username)

@login_required
def unfollow_user(request, username):
    user_to_unfollow = get_object_or_404(User, username=username)
    from_profile = request.user.profile
    to_profile = user_to_unfollow.profile
    
    follow_relationship = get_object_or_404(Follower, follower=from_profile, following=to_profile)
    follow_relationship.delete()
    
    messages.success(request, f"You have unfollowed {username}.")
    return redirect('profile_detail', username=username)

@login_required
def cancel_request(request, username):
    user_to_cancel = get_object_or_404(User, username=username)
    from_profile = request.user.profile
    to_profile = user_to_cancel.profile
    
    follow_request = get_object_or_404(FollowRequest, from_user=from_profile, to_user=to_profile)
    follow_request.delete()
    
    messages.success(request, f"Follow request to {username} canceled.")
    return redirect('profile_detail', username=username)

@login_required
def follow_requests(request):
    # Get all pending follow requests for the current user
    pending_requests = FollowRequest.objects.filter(to_user=request.user.profile).order_by('-created_at')
    return render(request, 'follow_requests.html', {'requests': pending_requests})

@login_required
def accept_request(request, request_id):
    follow_request = get_object_or_404(FollowRequest, id=request_id, to_user=request.user.profile)
    
    # Create follower relationship
    Follower.objects.create(follower=follow_request.from_user, following=follow_request.to_user)
    
    # Delete the request
    follow_request.delete()
    
    messages.success(request, f"You accepted {follow_request.from_user.user.username}'s follow request.")
    return redirect('follow_requests')

@login_required
def reject_request(request, request_id):
    follow_request = get_object_or_404(FollowRequest, id=request_id, to_user=request.user.profile)
    username = follow_request.from_user.user.username
    follow_request.delete()
    
    messages.success(request, f"You rejected {username}'s follow request.")
    return redirect('follow_requests')

@login_required
def profile_detail(request, username):
    user_profile = get_object_or_404(User, username=username)
    profile = user_profile.profile
    
    # Check if the current user is following this profile
    is_following = False
    has_requested = False
    
    if request.user.is_authenticated:
        is_following = Follower.objects.filter(
            follower=request.user.profile, 
            following=profile
        ).exists()
        
        has_requested = FollowRequest.objects.filter(
            from_user=request.user.profile,
            to_user=profile
        ).exists()
    
    # Get user posts (filter if private and not following)
    if request.user == user_profile or is_following or not profile.private_account:
        user_posts = Post.objects.filter(user=user_profile).order_by('-created_at')
    else:
        user_posts = []
    
    # Get follower count
    follower_count = Follower.objects.filter(following=profile).count()
    following_count = Follower.objects.filter(follower=profile).count()
    
    context = {
        'profile_user': user_profile,
        'profile': profile,
        'user_posts': user_posts,
        'is_following': is_following,
        'has_requested': has_requested,
        'follower_count': follower_count,
        'following_count': following_count,
    }
    
    return render(request, 'profile_detail.html', context)

@login_required
def followers_list(request, username):
    user = get_object_or_404(User, username=username)
    profile = user.profile
    followers = Follower.objects.filter(following=profile).order_by('-created_at')
    
    context = {
        'profile_user': user,
        'followers': followers,
    }
    
    return render(request, 'followers_list.html', context)

@login_required
def following_list(request, username):
    user = get_object_or_404(User, username=username)
    profile = user.profile
    following = Follower.objects.filter(follower=profile).order_by('-created_at')
    
    context = {
        'profile_user': user,
        'following': following,
    }
    
    return render(request, 'following_list.html', context)




# Add this form class to your views.py
class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Type your message...', 'class': 'w-full p-2 border rounded'})
        }



@login_required
def inbox(request):
    # Get all conversations this user is part of
    conversations = Conversation.objects.filter(
        participants=request.user
    ).annotate(
        last_message_time=Max('messages__created_at'),
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    ).order_by('-last_message_time')
    
    context = {
        'conversations': conversations,
    }
    return render(request, 'inbox.html', context)

@login_required
def conversation_view(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    
    # Mark unread messages as read
    Message.objects.filter(
        conversation=conversation, 
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)
    
    # Get messages
    messages = conversation.messages.all()
    
    # Handle new message form
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
            return redirect('conversation_view', conversation_id=conversation.id)
    else:
        form = MessageForm()
    
    context = {
        'conversation': conversation,
        'messages': messages,
        'form': form,
        'other_user': conversation.get_other_participant(request.user),
    }
    
    return render(request, 'conversation.html', context)

@login_required
def search_users(request):
    query = request.GET.get('q', '')
    if query:
        users = User.objects.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id)
    else:
        users = User.objects.none()
    
    context = {
        'users': users,
        'query': query,
    }
    
    return render(request, 'search_users.html', context)

@login_required
def new_conversation(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    
    # Check if a conversation already exists between these users
    conversations = Conversation.objects.filter(participants=request.user).filter(participants=other_user)
    
    if conversations.exists():
        # If conversation exists, redirect to it
        return redirect('conversation_view', conversation_id=conversations.first().id)
    else:
        # Create new conversation
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)
        return redirect('conversation_view', conversation_id=conversation.id)

# Add this context processor function
def unread_message_count(request):
    if request.user.is_authenticated:
        count = Message.objects.filter(
            conversation__participants=request.user,
            is_read=False
        ).exclude(sender=request.user).count()
        
        return {'unread_message_count': count}
    return {'unread_message_count': 0}

def splash(request):
    return render(request, 'splash.html')



def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    return render(request, 'post_detail.html', {'post': post})


def add_comment(request, post_id):
    if not request.user.is_authenticated:
        messages.warning(request, 'Please log in to comment.')
        return redirect('login')
    
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        text = request.POST.get('comment_text')
        if text:
            Comment.objects.create(
                post=post,
                user=request.user,
                text=text
            )
            messages.success(request, 'Comment added successfully.')
        else:
            messages.error(request, 'Comment cannot be empty.')
    
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('home')))

def toggle_like(request, post_id):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Login required'}, status=401)
    
    post = get_object_or_404(Post, id=post_id)
    
    # Check if the user has already liked the post
    like = Like.objects.filter(post=post, user=request.user).first()
    
    if like:
        # Unlike if already liked
        like.delete()
        return JsonResponse({'status': 'success', 'action': 'unliked', 'count': post.likes.count()})
    else:
        # Like if not already liked
        Like.objects.create(post=post, user=request.user)
        return JsonResponse({'status': 'success', 'action': 'liked', 'count': post.likes.count()})

# def share_post(request, post_id):
#     if not request.user.is_authenticated:
#         messages.warning(request, 'Please log in to share posts.')
#         return redirect('login')
    
#     post = get_object_or_404(Post, id=post_id)
    
#     # For simple sharing, we'll create a new post that references the original
#     if request.method == 'POST':
#         # Create a new post with reference to the original
#         shared_post = Post.objects.create(
#             user=request.user,
#             title=f"Shared: {post.title}",
#             description=request.POST.get('share_text', ''),
#             post_type='text',  # Or you might want to copy the original type
#             text_content=f"Original post by @{post.user.username}: {post.title}"
#         )
#         messages.success(request, 'Post shared successfully.')
#         return redirect('post_detail', post_id=shared_post.id)
    
#     return render(request, 'share_post.html', {'post': post})


#This will share post but with an extra '??? and not in format of a link

def share_post(request, post_id):
    if not request.user.is_authenticated:
        messages.warning(request, 'Please log in to share posts.')
        return redirect('login')
    
    post = get_object_or_404(Post, id=post_id)
    
    # Prepare the shareable content for WhatsApp
    post_url = request.build_absolute_uri(post.get_absolute_url())  # Get the URL of the post
    post_title = post.title
    post_description = post.description or 'No description provided.'
    post_image_url = post.file.url if post.post_type == 'image' else ''
    
    # Create a message for WhatsApp sharing
    whatsapp_message = f"Check out this post: {post_url}"
    print("WhatsApp Share message:", whatsapp_message)
    
    # URL encode the message for WhatsApp
    whatsapp_share_url = f"https://wa.me/?text={quote(whatsapp_message)}"
    print("WhatsApp Share URL:", whatsapp_share_url)
    
    # For simple sharing, we'll create a new post that references the original
    if request.method == 'POST':
        # Create a new post with reference to the original
        shared_post = Post.objects.create(
            user=request.user,
            title=f"Shared: {post.title}",
            file=post.file if post.file else None, 
            description=request.POST.get('share_text', ''),
            post_type=post.post_type,  # Or you might want to copy the original type
            text_content=f"Original post by @{post.user.username}: {post.title}"
        )

        if post.file:
            print("File URL:", post.file.url)
        messages.success(request, 'Post shared successfully.')
        #return redirect('post_detail', post_id=shared_post.id)
        return redirect('home')
    
    

    
   
    
    return render(request, 'share_post.html', {'post': post, 'whatsapp_share_url': whatsapp_share_url})



def socialmedia(request):
    return render(request, 'socialmedia.html')

def delete_account(request):
    if request.method != 'POST':
        return render(request, 'delete_account.html')
        
    email = request.POST.get('email')
    
    if not email:
        return render(request, 'delete_account.html', {'error': 'Email is required'})

    try:
        user = User.objects.get(email=email)
        
        # Ensure the primary key is converted to bytes
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Use default_token_generator consistently
        token = default_token_generator.make_token(user)

        # Create the confirmation link
        link = f"{request.scheme}://{request.get_host()}/confirm_delete/{uid}/{token}/"
        
        # Send the email with the link
        send_mail(
            'Delete Account Confirmation',
            f'Click the link to delete your account: {link}',
            'from@example.com',
            [user.email],
            fail_silently=False,
        )
        
        # Just use render with confirm_deletion.html which you already have
        return render(request, 'confirm_deletion.html', {
            'email_sent': True,
            'message': 'Please check your email to confirm account deletion'
        })

    except User.DoesNotExist:
        return render(request, 'delete_account.html', {'error': 'User not found'})

def confirm_deletion(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is None or not default_token_generator.check_token(user, token):
        return HttpResponse("Invalid or expired link", status=400)
        
    if request.method == 'POST':
        password = request.POST.get('password')
        if user.check_password(password):
            username = user.username  # Store before deletion
            user.delete()
            return render(request, 'account_deleted.html', {'username': username})
        else:
            return render(request, 'confirm_deletion.html', {'error': 'Incorrect password.'})
            
    return render(request, 'confirm_deletion.html', {'user': user})