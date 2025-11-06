# Python_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    
    # 1. Home path
    path('', views.home_view, name='home'),
    
    # 2. Mode Offline - Category Selection (Correct view for /offline/)
    path('offline/', views.offline_category_selection, name='offline_category'), 
    
    # 3. Mode Offline - Game Start
    path('offline/play/<int:category_id>/', views.offline_game_view, name='offline_game_view'), 
    
    # 4. Mode Multijoueur
    path('multiplayer/', views.multiplayer_lobby_view, name='multiplayer_lobby'),
     path('classements/', views.classements_view, name='classements'),
    
    # ... any other paths (login, register, etc.)
]