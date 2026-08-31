"""
Authentication Views matching PRD Ch. 30.1 & Security Posture Ch. 26.1, 26.7, 32.
"""
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from apps.users.serializers import (
    UserLoginSerializer,
    UserReadSerializer,
    UserSignUpSerializer,
)

User = get_user_model()


def set_refresh_cookie(response, refresh_token_str):
    """
    Sets the refresh token in a secure httpOnly cookie (Ch. 26.1).
    """
    refresh_days = int(getattr(settings, 'SIMPLE_JWT', {}).get('REFRESH_TOKEN_LIFETIME_DAYS', 7))
    max_age = refresh_days * 24 * 3600
    response.set_cookie(
        key='refresh_token',
        value=refresh_token_str,
        max_age=max_age,
        httponly=True,
        samesite='Lax',
        secure=not settings.DEBUG,
    )


def clear_refresh_cookie(response):
    """
    Clears the refresh_token cookie on logout.
    """
    response.delete_cookie('refresh_token')


class SignUpView(APIView):
    """
    POST /api/auth/signup (Public)
    Registers a new user account.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def post(self, request):
        serializer = UserSignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        response = Response(
            {
                "user": UserReadSerializer(user).data,
                "access": access_token,
            },
            status=status.HTTP_201_CREATED,
        )
        set_refresh_cookie(response, str(refresh))
        return response


class LoginView(APIView):
    """
    POST /api/auth/login (Public)
    Authenticates user and returns access token + httpOnly refresh token cookie.
    Generic error on invalid credentials (PRD Ch. 32).
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = authenticate(request, username=email, password=password)
        if user is None or not user.is_active:
            raise AuthenticationFailed("Invalid email or password.")

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        response = Response(
            {
                "user": UserReadSerializer(user).data,
                "access": access_token,
            },
            status=status.HTTP_200_OK,
        )
        set_refresh_cookie(response, str(refresh))
        return response


class RefreshTokenView(APIView):
    """
    POST /api/auth/refresh (Public, valid refresh token required)
    Rotates refresh token and returns a new access token (Ch. 26.1).
    Reads refresh token from httpOnly cookie or payload.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        raw_refresh_token = request.COOKIES.get('refresh_token') or request.data.get('refresh')
        if not raw_refresh_token:
            raise AuthenticationFailed("Authentication refresh token was not provided.")

        try:
            old_refresh = RefreshToken(raw_refresh_token)
            
            # Fetch user and issue new rotated refresh token pair
            user_id = old_refresh.payload.get(settings.SIMPLE_JWT.get('USER_ID_CLAIM', 'user_id'))
            user = User.objects.get(id=user_id)
            if not user.is_active:
                raise AuthenticationFailed("User account is inactive.")

            # Server-side blacklist the previous refresh token per Ch. 26.1 rotation rules
            try:
                old_refresh.blacklist()
            except Exception:
                pass

            new_refresh = RefreshToken.for_user(user)
            new_access_token = str(new_refresh.access_token)

            response = Response(
                {"access": new_access_token},
                status=status.HTTP_200_OK,
            )
            set_refresh_cookie(response, str(new_refresh))
            return response
        except (TokenError, InvalidToken, User.DoesNotExist) as exc:
            raise AuthenticationFailed("Invalid or expired refresh token.") from exc


class LogoutView(APIView):
    """
    POST /api/auth/logout (Authenticated)
    Server-side invalidates/blacklists current refresh token and clears httpOnly cookie (AC-1.3).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        raw_refresh_token = request.COOKIES.get('refresh_token') or request.data.get('refresh')
        if raw_refresh_token:
            try:
                token = RefreshToken(raw_refresh_token)
                token.blacklist()
            except (TokenError, InvalidToken):
                # Ignore invalid token during logout attempt
                pass

        response = Response(
            {"message": "Successfully logged out."},
            status=status.HTTP_200_OK,
        )
        clear_refresh_cookie(response)
        return response
