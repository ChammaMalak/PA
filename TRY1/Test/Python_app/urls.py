from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views  # Importe toutes les vues (Web et API)
from django.contrib.auth import views as auth_views  # Vues d'authentification intégrées de Django

# Création du router DRF
router = DefaultRouter()

# Enregistrement des ViewSets pour l'API (si présents)
try:
    router.register(r'users', views.UserViewSet)
except Exception:
    pass

try:
    router.register(r'player-scores', views.PlayerScoreViewSet)
except Exception:
    pass

try:
    router.register(r'player-answers', views.PlayerAnswerViewSet)
except Exception:
    pass

try:
    router.register(r'quiz-questions', views.QuizQuestionViewSet)
except Exception:
    pass

try:
    router.register(r'game-sessions', views.GameSessionViewSet)
except Exception:
    pass

# Patterns d'URL
urlpatterns = [
    # --- A. ROUTES D'API (DRF) ---
    path('api/auth/register/', views.RegisterAPIView.as_view(), name='api-register'),
    path('api/auth/login/', views.LoginAPIView.as_view(), name='api-login'),
    path('api/auth/me/', views.MeAPIView.as_view(), name='api-me'),
    path('api/auth/logout/', views.LogoutAPIView.as_view(), name='api-logout'),

    # Routes du router (toutes les viewsets enregistrées ci-dessus)
    path('api/', include(router.urls)),

    # --- B. ROUTES WEB (rendu HTML) ---
    path('', views.home_view, name='home'),

    # Authentification Django standard (templates)
    path('login/', auth_views.LoginView.as_view(template_name='login.html', next_page='/'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

    # Profil utilisateur
    path('profile/', views.profile_view, name='profile'),

    # Mode offline / catégories / jeu
    path('offline/', views.offline_category_selection, name='offline_category'),
    path('offline/play/<int:category_id>/', views.offline_game_view, name='offline_game_view'),

    # Multijoueur / classements / inscription
    
    path('multiplayer/', views.multiplayer_initial_setup, name='multiplayer_initial_setup'), 
    path('multiplayer/lobby/', views.multiplayer_lobby_view, name='multiplayer_lobby'),
    path('multiplayer/lobby/game/', views.multiplayer_game_start, name='multiplayer_game_start'),
   
    path('classements/', views.classements_view, name='classements'),
    path('register/', views.register_view, name='register'),
]