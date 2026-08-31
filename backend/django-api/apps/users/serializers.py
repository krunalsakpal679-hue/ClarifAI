"""
Serializers for authentication endpoints (signup, login, user representation).
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class UserReadSerializer(serializers.ModelSerializer):
    """
    Public representation serializer for User model.
    """
    class Meta:
        model = User
        fields = ('id', 'email', 'created_at', 'is_admin')
        read_only_fields = ('id', 'email', 'created_at', 'is_admin')


class UserSignUpSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration (signup).
    Engineering Implementation Detail: Password validated via Django's validator (min length 8).
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )

    class Meta:
        model = User
        fields = ('email', 'password')

    def validate_email(self, value):
        normalized_email = User.objects.normalize_email(value)
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return normalized_email

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for login payload validation.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
