from django.contrib import admin
from django.urls import path

from .views import LoginAPIView, RegisterView, VerifyEmail, ResendVerification, UserProfileView, CurrentUserProfileView, UpdateProfileView, CheckUsernameView

urlpatterns = [
    path('authentication/login', LoginAPIView.as_view(), name='login'),
    path('authentication/register', RegisterView.as_view(), name='register'),
    path('authentication/verify-email', VerifyEmail.as_view(), name='verify-email'),
    path('authentication/resend-verification', ResendVerification.as_view(), name='resend-verification'),

    
    # Profile URLs
    path('profile/<str:username>/', UserProfileView.as_view(), name='user-profile'),
    path('profile/', CurrentUserProfileView.as_view(), name='current-user-profile'),
    path('profile/update/', UpdateProfileView.as_view(), name='update-profile'),
    path('check-username/', CheckUsernameView.as_view(), name='check-username'),
]
