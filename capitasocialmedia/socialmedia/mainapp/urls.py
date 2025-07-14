from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('', views.splash, name='splash'),
     path('login/', views.user_login, name='login'),
    path('home/', views.home, name='home'),
    path('register/', views.register, name='register'),
   
    
    path('logout/', views.user_logout, name='logout'),

    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),

    path('search/', views.user_search, name='user_search'),
    path('profile/', views.profile, name='profile'),
    path('create-post/', views.create_post, name='create_post'),
    path('delete-post/<int:post_id>/', views.delete_post, name='delete_post'),
    path('download/<int:post_id>/', views.download_file, name='download_file'),
    path('create_text_post/', views.create_text_post, name='create_text_post'),
    
    
    path('toggle-privacy/', views.toggle_privacy, name='toggle_privacy'),
    
   
    path('profile/<str:username>/', views.profile_detail, name='profile_detail'),
    path('profile/<str:username>/followers/', views.followers_list, name='followers_list'),
    path('profile/<str:username>/following/', views.following_list, name='following_list'),
    path('follow/<str:username>/', views.follow_user, name='follow_user'),
    path('unfollow/<str:username>/', views.unfollow_user, name='unfollow_user'),
    path('cancel-request/<str:username>/', views.cancel_request, name='cancel_request'),
    path('follow-requests/', views.follow_requests, name='follow_requests'),
    path('accept-request/<int:request_id>/', views.accept_request, name='accept_request'),
    path('reject-request/<int:request_id>/', views.reject_request, name='reject_request'),

path('password_reset/', 
     auth_views.PasswordResetView.as_view(
         email_template_name='password_reset_email.html',  
         template_name='password_reset.html',
         subject_template_name='password_reset_subject.txt'
         
     ), 
     name='password_reset'),
#path('password_reset/',
#  auth_views.PasswordResetView.as_view(template_name='password_reset.html'),
#  name='password_reset'),
path('password_reset/done/',
      auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'),
        name='password_reset_done'),
path('reset/<uidb64>/<token>/',
      auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'),
        name='password_reset_confirm'),
path('reset/done/', 
     auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),
       name='password_reset_complete'),

     
     
    path('conversation/<int:conversation_id>/', views.conversation_view, name='conversation_view'),
    path('search-users/', views.search_users, name='search_users'),
    path('new-conversation/<int:user_id>/', views.new_conversation, name='new_conversation'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),

    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    
    path('post/<int:post_id>/like/', views.toggle_like, name='toggle_like'),
    path('post/<int:post_id>/share/', views.share_post, name='share_post'),
    
     path('delete_account/', views.delete_account, name='delete_account'),
    path('confirm_delete/<str:uidb64>/<str:token>/', views.confirm_deletion, name='confirm_deletion'),


]