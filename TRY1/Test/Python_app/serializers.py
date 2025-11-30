try:
    from rest_framework import serializers  # type: ignore
except Exception:
    # minimal stubs to avoid import errors when djangorestframework isn't installé
    class _DummySerializer:
        pass

    class _DummyModelSerializer(_DummySerializer):
        pass

    class _DummyField:
        pass

    class serializers:
        Serializer = _DummySerializer
        ModelSerializer = _DummyModelSerializer
        Field = _DummyField


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


class UserSerializer(serializers.ModelSerializer):
    """Serializer pour afficher les détails utilisateur (GET)."""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'date_joined')
        read_only_fields = ('id', 'date_joined')

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer pour créer un compte (POST /api/register/)."""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm')

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Les mots de passe ne correspondent pas.'})
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({'username': 'Ce nom d\'utilisateur existe déjà.'})
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({'email': 'Cet email est déjà utilisé.'})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

class UserLoginSerializer(serializers.Serializer):
    """Serializer pour la connexion (POST /api/auth/login/)."""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)