from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views # Importe toutes les vues (Web et API)
from django.contrib.auth import views as auth_views # Pour les vues d'authentification intégrées de Django

# =================================================================
# 1. Configuration du Router DRF pour les ViewSets
# =================================================================
router = DefaultRouter()

# Enregistrement des ViewSets pour l'API (e.g., /api/users/, /api/player-scores/)
router.register(r'users', views.UserViewSet)
router.register(r'player-scores', views.PlayerScoreViewSet)
router.register(r'player-answers', views.PlayerAnswerViewSet)
router.register(r'quiz-questions', views.QuizQuestionViewSet)
router.register(r'game-sessions', views.GameSessionViewSet)

# =================================================================
# 2. Définition des Patterns d'URL
# =================================================================
urlpatterns = [
    # --- A. ROUTES D'API (DRF) ---
    
    # 1. Routes d'Authentification d'API (APIViews)
    path('api/auth/login/', views.LoginAPIView.as_view(), name='api-login'),
    path('api/auth/me/', views.MeAPIView.as_view(), name='api-me'),
    path('api/auth/logout/', views.LogoutAPIView.as_view(), name='api-logout'),
    
    # 2. Routes génériques du Router (ViewSets)
    # Ceci inclut toutes les routes enregistrées ci-dessus (e.g., /api/users/)
    path('api/', include(router.urls)),
    
    
    # --- B. ROUTES WEB TRADITIONNELLES (Rendu HTML) ---
    
    # 3. Route d'Accueil
    # NOTE: On utilise home_view car elle est la vue d'accueil complète
    path('', views.home_view, name='home'),
    
    # 4. Authentification Classique (Django standard)
    # Laissez ces chemins si vous utilisez toujours le système de templates de Django pour la connexion/déconnexion
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    # path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'), # Exemple
    
    # 5. Routes du Mode Offline
    path('offline/', views.offline_category_selection, name='offline_category'), 
    path('offline/play/<int:category_id>/', views.offline_game_view, name='offline_game_view'), 
    
    # 6. Routes Multijoueur/Classements
    path('multiplayer/', views.multiplayer_lobby_view, name='multiplayer_lobby'),
    path('classements/', views.classements_view, name='classements'),
]