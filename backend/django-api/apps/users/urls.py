"""
URL Routing for Auth microservice endpoints (Ch. 30.1).
"""
from django.urls import path
from apps.users.views import SignUpView, LoginView, RefreshTokenView, LogoutView

urlpatterns = [
    path('signup', SignUpView.as_view(), name='auth_signup'),
    path('login', LoginView.as_view(), name='auth_login'),
    path('refresh', RefreshTokenView.as_view(), name='auth_refresh'),
    path('logout', LogoutView.as_view(), name='auth_logout'),
]
