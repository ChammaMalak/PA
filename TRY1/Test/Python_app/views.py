from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout # Pour l'API
from .models import Category, QuizQuestion, Answer, PlayerScore, PlayerAnswer, GameSession, User
from .services import generate_and_save_question
import random

# Imports DRF (Django Rest Framework)
from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
# IMPORTANT : Assurez-vous que ces Serializers sont disponibles et importables
from .serializers import (
    PlayerScoreSerializer, PlayerAnswerSerializer, QuizQuestionSerializer,
    GameSessionSerializer, UserSerializer, UserRegistrationSerializer,
    LoginSerializer
)

# =================================================================
# I. VUES TRADITIONNELLES (Rendu HTML)
# =================================================================

def home_view(request):
    """ Affiche la page d'accueil du jeu de quiz. """
    context = {
        'is_authenticated': request.user.is_authenticated,
        'user': request.user
    }
    return render(request, 'home.html', context)

def home(request):
    """ Vue simple pour l'API home si l'autre n'est pas utilisée. """
    return HttpResponse("Bienvenue sur la page d'accueil! <a href='/accounts/login/'>Se connecter</a>")
    

def offline_category_selection(request):
    """ Affiche la liste de toutes les catégories pour le jeu hors ligne. """
    categories = Category.objects.all()
    context = {
        'categories': categories,
        'page_title': "Choisir une Catégorie"
    }
    return render(request, 'offline/category_selection.html', context)



#@login_required # Décommenter si l'authentification est nécessaire
def offline_game_view(request, category_id):
    """ Gère l'affichage d'une question de quiz et la soumission de la réponse. """
    category = get_object_or_404(Category, pk=category_id)
    
    # 1. LOGIQUE DE RÉCUPÉRATION/GÉNÉRATION DE LA QUESTION
    question = None
    try:
        question = QuizQuestion.objects.filter(Category=category).order_by('?').first()
        if not question:
            question = generate_and_save_question(category.descriptor, difficulty=2)
            
        if not question:
            message = "Aucune question disponible. Génération échouée."
            return render(request, 'error.html', {'message': message})
            
    except Exception as e:
        return render(request, 'error.html', {'message': f"Erreur critique: {e}"})

    # 2. Préparation des réponses
    answers = list(question.answers.all()) 
    random.shuffle(answers)
    
    context = {
        'category': category, 'question': question, 'answers': answers, 
        'fixed_time': 15, 'page_title': f"Quiz : {category.descriptor}",
        'submitted': False,
    }
    
    # 3. GESTION DE LA SOUMISSION DE LA RÉPONSE (POST)
    if request.method == 'POST':
        selected_answer_id = request.POST.get('answer_id')
        try:
            selected_answer = Answer.objects.get(pk=selected_answer_id)
            is_correct = selected_answer.IsCorrect 
            correct_answer = Answer.objects.get(Question=question, IsCorrect=True)
            
            context.update({
                'submitted': True, 
                'is_correct': is_correct,
                'submitted_answer_id': int(selected_answer_id),
                'correct_answer_id': correct_answer.pk,
            })
        except Answer.DoesNotExist:
            pass # Gérer l'ID invalide
            
    # 4. Rendre le template
    return render(request, 'offline/game.html', context)



@login_required 
def multiplayer_lobby_view(request):
    return HttpResponse("Page du Lobby Multijoueur (en construction)")

@login_required
def classements_view(request):
    return HttpResponse("Page du Lobby classements (en construction)")

# =================================================================
# II. VUES D'API (Django Rest Framework)
# =================================================================

# --- A. Existing Model ViewSets ---

class PlayerScoreViewSet(viewsets.ModelViewSet):
    """ API pour la gestion des scores des joueurs. """
    queryset = PlayerScore.objects.all()
    serializer_class = PlayerScoreSerializer

class PlayerAnswerViewSet(viewsets.ModelViewSet):
    """ API pour la gestion des réponses des joueurs. """
    queryset = PlayerAnswer.objects.all()
    serializer_class = PlayerAnswerSerializer

class QuizQuestionViewSet(viewsets.ModelViewSet):
    """ API pour la gestion des questions de quiz. """
    queryset = QuizQuestion.objects.all()
    serializer_class = QuizQuestionSerializer

class GameSessionViewSet(viewsets.ModelViewSet):
    """ API pour la gestion des sessions de jeu. """
    queryset = GameSession.objects.all()
    serializer_class = GameSessionSerializer

# --- B. User ViewSet (Registration Logic) ---
class UserViewSet(viewsets.ModelViewSet):
    """ API pour la gestion des utilisateurs (inscription/détails). """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_serializer_class(self):
        """ Utilise UserRegistrationSerializer pour la création (POST). """
        if self.request.method == 'POST':
            return UserRegistrationSerializer
        return self.serializer_class

# --- C. API AUTHENTICATION ENDPOINTS (Login/Logout/Me) ---

class LoginAPIView(APIView):
    """ Gère la connexion d'un utilisateur via l'API (POST /api/auth/login). """
    permission_classes = [permissions.AllowAny] 
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True) 
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user) 
            return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_400_BAD_REQUEST)

class MeAPIView(APIView):
    """ Renvoie les détails de l'utilisateur connecté (GET /api/auth/me). """
    permission_classes = [permissions.IsAuthenticated] 
    
    def get(self, request):
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)

class LogoutAPIView(APIView):
    """ Déconnecte l'utilisateur (POST /api/auth/logout). """
    permission_classes = [permissions.IsAuthenticated] 
    
    def post(self, request):
        logout(request) 
        return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)