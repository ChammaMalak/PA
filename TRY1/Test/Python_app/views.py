from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from .models import Category, QuizQuestion, Answer, PlayerScore, PlayerAnswer, GameSession
from .services import generate_and_save_question # Assurez-vous que cette fonction existe
import random

# DRF imports (Avec gestion des exceptions si DRF n'est pas installé)
try:
    from rest_framework import status, viewsets, permissions
    from rest_framework.views import APIView
    from rest_framework.response import Response
except Exception:
    status = type('status', (), {'HTTP_200_OK': 200, 'HTTP_201_CREATED': 201, 'HTTP_400_BAD_REQUEST': 400, 'HTTP_401_UNAUTHORIZED': 401})()
    APIView = object
    Response = dict
    viewsets = type('viewsets', (), {'ModelViewSet': object})()
    permissions = type('permissions', (), {'AllowAny': object, 'IsAuthenticated': object})()

from .serializers import (
    PlayerScoreSerializer, PlayerAnswerSerializer, QuizQuestionSerializer,
    GameSessionSerializer, UserSerializer, UserRegistrationSerializer,
    LoginSerializer
)

# =================================================================
# ===== I. VUES WEB (Rendu HTML) =====
# =================================================================

def home_view(request):
    """Affiche la page d'accueil."""
    context = {'is_authenticated': request.user.is_authenticated, 'user': request.user}
    return render(request, 'home.html', context)



def offline_category_selection(request):
    """Affiche la liste des catégories pour le jeu offline."""
    default_categories = ["Géographie", "Histoire", "Sciences", "Informatique", "Islam", "Culture Générale"]
    try:
        # Assure l'existence des catégories par défaut
        if not Category.objects.exists():
            for name in default_categories:
                Category.objects.get_or_create(descriptor=name)
    except Exception:
        pass
    categories = Category.objects.all()
    return render(request, 'offline/category_selection.html', {'categories': categories, 'page_title': "Choisir une Catégorie"})



def offline_game_view(request, category_id):
    """Affiche une question de quiz et gère la soumission de réponse (mode hors ligne)."""
    category = get_object_or_404(Category, pk=category_id)
    
    # Logique de suivi des questions jouées (Anti-répétition)
    session_key = f'played_questions_{category_id}'
    played_question_ids = request.session.get(session_key, [])
    all_question_ids = QuizQuestion.objects.filter(Category=category).values_list('pk', flat=True)
    available_question_ids = list(set(all_question_ids) - set(played_question_ids))

    question = None
    
    if available_question_ids:
        question = QuizQuestion.objects.filter(pk__in=available_question_ids).order_by('?').first()
    
    if not question:
        try:
            if not all_question_ids or not available_question_ids:
                 # Tentative de générer une question si la base est vide ou si tout a été joué
                 question = generate_and_save_question(category.descriptor, difficulty=2)
        except Exception:
             pass
    
    if not question:
        # Gérer l'épuisement des questions
        if played_question_ids:
             del request.session[session_key]
             request.session.modified = True 
             message = "Toutes les questions de cette catégorie ont été jouées. <a href='/offline/'>Retour aux catégories</a>"
        else:
             message = "La base de données est vide pour cette catégorie, et la génération a échoué."
        return render(request, 'error.html', {'message': message})

    # Enregistrer la question actuelle comme jouée
    played_question_ids.append(question.pk)
    request.session[session_key] = played_question_ids
    request.session.modified = True 
    
    answers = list(question.answers.all())
    random.shuffle(answers)
    context = {
        'category': category, 'question': question, 'answers': answers,
        'fixed_time': 15, 'page_title': f"Quiz : {category.descriptor}",
        'submitted': False,
    }

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
            pass

    return render(request, 'offline/game.html', context)



@login_required
def multiplayer_initial_setup(request):
    """Affiche le formulaire initial pour saisir le nombre de joueurs (Étape 1 du Multijoueur)."""
    MAX_PLAYERS = 6
    
    if request.method == 'POST':
        try:
            num_players = int(request.POST.get('num_players', 2))
            
            if 2 <= num_players <= MAX_PLAYERS:
                request.session['num_players_to_register'] = num_players
                return redirect('multiplayer_lobby')
            else:
                messages.error(request, f"Le nombre de joueurs doit être compris entre 2 et {MAX_PLAYERS}.")
        except ValueError:
            messages.error(request, "Veuillez saisir un nombre valide.")
            
    context = {
        'page_title': "Sélection du nombre de joueurs",
        'max_players': MAX_PLAYERS
    }
    return render(request, 'multiplayer/initial_setup.html', context)


@login_required 
def multiplayer_lobby_view(request):
    """Affiche le formulaire pour saisir les noms des joueurs ET choisir la catégorie (Étape 2 du Multijoueur)."""
    num_players = request.session.get('num_players_to_register') 
    
    if not num_players:
        messages.warning(request, "Veuillez d'abord choisir le nombre de joueurs.")
        return redirect('multiplayer_initial_setup')
        
    categories = Category.objects.all()
    if not categories.exists():
        messages.error(request, "Veuillez créer des catégories avant de démarrer une partie multijoueur.")
        return redirect('home')
        
    AVAILABLE_COLORS = ['#FF6347', '#4682B4', '#3CB371', '#FFA500', '#9370DB', '#F08080'] 
    
    if request.method == 'POST':
        selected_category_id = request.POST.get('category_id') 
        
        if not selected_category_id:
            messages.error(request, "Veuillez sélectionner une catégorie.")
            # Repasse les catégories au context en cas d'erreur pour éviter un crash
            context = {'page_title': "Lobby Multijoueur", 'player_range': range(1, num_players + 1), 'num_players': num_players, 'categories': categories}
            return render(request, 'multiplayer/lobby.html', context)


        player_names = {}
        for i in range(1, num_players + 1): 
            name = request.POST.get(f'player_name_{i}', f'Joueur {i}').strip()
            if name:
                 player_names[i] = name

        # Initialisation de la session de jeu
        random.shuffle(AVAILABLE_COLORS)
        
        players = []
        for i, (index, name) in enumerate(player_names.items()):
            players.append({
                'id': index,
                'name': name,
                'color': AVAILABLE_COLORS[i % len(AVAILABLE_COLORS)],
                'score': 0,
            })
            
        request.session['multiplayer_game'] = {
            'players': players,
            'current_turn_index': 0,
            'category_id': int(selected_category_id), # Stocke l'ID de catégorie
        }
        
        del request.session['num_players_to_register']
        
        messages.success(request, "Lobby créé ! Début du jeu.")
        return redirect('multiplayer_game_start') 
        
    # Affichage du formulaire
    player_range = range(1, num_players + 1)
    
    context = {
        'page_title': "Lobby Multijoueur",
        'player_range': player_range,
        'num_players': num_players,
        'categories': categories,
    }
    return render(request, 'multiplayer/lobby.html', context)


@login_required
def multiplayer_game_start(request):
    """
    Affiche la question actuelle, gère le tour du joueur, le score et le passage au joueur suivant (Étape 3 du Multijoueur).
    """
    # CORRECTION DE LA CLÉ : Utiliser la clé 'multiplayer_game'
    game_data = request.session.get('multiplayer_game') 
    
    if not game_data:
        messages.error(request, "Aucune partie multijoueur en cours. Veuillez créer un lobby.")
        return redirect('multiplayer_initial_setup')

    players = game_data['players']
    current_index = game_data['current_turn_index']
    current_player = players[current_index]
    
    # Récupère la catégorie choisie dans la session
    category_id = game_data.get('category_id')
    
    if category_id:
        category = get_object_or_404(Category, pk=category_id)
    else:
        # Mesure de sécurité si l'ID a disparu (utilise la première catégorie)
        category = Category.objects.first()

    if not category:
        messages.error(request, "Erreur : Aucune catégorie disponible.")
        return redirect('multiplayer_initial_setup')

    # Sélectionne une question aléatoire pour la catégorie choisie
    question = QuizQuestion.objects.filter(Category=category).order_by('?').first()

    if not question:
        messages.error(request, f"Erreur: Aucune question disponible pour la catégorie '{category.descriptor}'.")
        # Met fin à la partie multijoueur si aucune question n'est trouvée
        del request.session['multiplayer_game']
        request.session.modified = True
        return redirect('multiplayer_initial_setup')
        
    answers = list(question.answers.all())
    random.shuffle(answers)

    # --- Gestion de la soumission de réponse ---
    if request.method == 'POST':
        selected_answer_id = request.POST.get('answer_id')
        
        try:
            selected_answer = Answer.objects.get(pk=selected_answer_id)
            is_correct = selected_answer.IsCorrect
            
            # Mise à jour du score
            if is_correct:
                current_player['score'] += 10
                messages.success(request, f"✅ {current_player['name']} a marqué 10 points!")
            else:
                messages.warning(request, f"❌ {current_player['name']} a manqué la question.")
            
            # Passer au joueur suivant
            next_index = (current_index + 1) % len(players)
            
            # Mise à jour et sauvegarde de la session
            game_data['current_turn_index'] = next_index
            game_data['players'][current_index] = current_player 
            request.session['multiplayer_game'] = game_data
            request.session.modified = True
            
            # Rediriger vers la même vue (nouvelle question/nouveau joueur)
            return redirect('multiplayer_game_start')
            
        except Answer.DoesNotExist:
            messages.error(request, "Réponse invalide.")
    
    # --- Rendu de la page de jeu ---
    context = {
        'page_title': "Partie Multijoueur",
        'players': players,
        'current_player': current_player,
        'question': question,
        'answers': answers,
    }
    return render(request, 'multiplayer/game.html', context)



@login_required
def classements_view(request):
    """Page des classements."""
    # Logique pour récupérer et afficher PlayerScore
    return render(request, 'classements.html', {})



@csrf_protect
def register_view(request):
    """Page d'inscription."""
    # (Logique de gestion du formulaire d'inscription non modifiée)
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        password_confirm = request.POST.get('confirm_password', '').strip()

        errors = {}

        if not username: errors['username'] = 'Le nom d\'utilisateur est requis.'
        elif len(username) < 3: errors['username'] = 'Le nom d\'utilisateur doit contenir au moins 3 caractères.'
        if not email: errors['email'] = 'L\'email est requis.'
        elif '@' not in email: errors['email'] = 'L\'email doit être valide.'
        if not password: errors['password'] = 'Le mot de passe est requis.'
        elif len(password) < 8: errors['password'] = 'Le mot de passe doit contenir au moins 8 caractères.'
        if password != password_confirm: errors['confirm_password'] = 'Les mots de passe ne correspondent pas.'

        if username and User.objects.filter(username=username).exists():
            errors['username'] = 'Ce nom d\'utilisateur existe déjà.'
        if email and User.objects.filter(email=email).exists():
            errors['email'] = 'Cet email est déjà utilisé.'

        if errors:
            return render(request, 'register.html', {'errors': errors, 'username': username, 'email': email})

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, f'Compte créé avec succès ! Bienvenue {username}.')
            login(request, user)
            return redirect('home')
        except Exception as e:
            messages.error(request, f'Erreur : {str(e)}')
            return render(request, 'register.html', {'errors': {}, 'username': username, 'email': email})

    return render(request, 'register.html', {'errors': {}})



@login_required(login_url='login')
def profile_view(request):
    """Affiche le profil de l'utilisateur connecté."""
    return render(request, 'profile.html', {'user': request.user})

# =================================================================
# ===== II. VUES API (Django Rest Framework) =====
# =================================================================
# (Ces classes API n'ont pas été modifiées)

class RegisterAPIView(APIView):
    """API pour créer un compte : POST /api/auth/register/"""
    permission_classes = [permissions.AllowAny] 

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {'message': 'Compte créé avec succès', 'user': UserSerializer(user).data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginAPIView(APIView):
    """API pour se connecter : POST /api/auth/login/"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return Response(
                    {'message': 'Connecté avec succès', 'user': UserSerializer(user).data},
                    status=status.HTTP_200_OK
                )
            return Response(
                {'error': 'Nom d\'utilisateur ou mot de passe incorrect'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MeAPIView(APIView):
    """API pour récupérer l'utilisateur connecté : GET /api/auth/me/"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.is_authenticated:
            return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)
        return Response({'error': 'Non authentifié'}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutAPIView(APIView):
    """API pour se déconnecter : POST /api/auth/logout/"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'message': 'Déconnecté avec succès'}, status=status.HTTP_200_OK)

class PlayerScoreViewSet(viewsets.ModelViewSet):
    queryset = PlayerScore.objects.all()
    serializer_class = PlayerScoreSerializer

class PlayerAnswerViewSet(viewsets.ModelViewSet):
    queryset = PlayerAnswer.objects.all()
    serializer_class = PlayerAnswerSerializer

class QuizQuestionViewSet(viewsets.ModelViewSet):
    queryset = QuizQuestion.objects.all()
    serializer_class = QuizQuestionSerializer

class GameSessionViewSet(viewsets.ModelViewSet):
    queryset = GameSession.objects.all()
    serializer_class = GameSessionSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserRegistrationSerializer
        return self.serializer_class