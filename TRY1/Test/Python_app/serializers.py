from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import (
    PlayerScore, PlayerAnswer, QuizQuestion,
    GameSession, Answer, Category, User
)


class PlayerScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerScore
        fields = '__all__'


class PlayerAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerAnswer
        fields = '__all__'


class QuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        fields = '__all__'


class GameSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameSession
        fields = '__all__'


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


# -----------------------------
# USER SERIALIZERS
# -----------------------------

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for GET/PUT/PATCH requests (read/update user data)
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'ControlTimestamp')
        read_only_fields = ('ControlTimestamp',)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for POST requests (user registration)
    """
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'password')

    def create(self, validated_data):
        # Extract password
        plain_password = validated_data.pop('password')

        # Create user without password first
        user = User.objects.create(**validated_data)

        # Hash password manually because model uses "passwordHash"
        user.passwordHash = make_password(plain_password)
        user.save()

        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer used to validate login data
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)