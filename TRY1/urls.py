# TRY1/urls.py (Le fichier principal, DANS le dossier 'Test' ou 'TRY1')

from django.contrib import admin
from django.urls import path, include
# Supprimez: from . import views 🚨

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # CECI EST LA SEULE LIGNE NÉCESSAIRE pour inclure les chemins de l'app
    path('', include('Python_app.urls')), 
    path('accounts/', include('django.contrib.auth.urls')),
    
    # 🚨 SUPPRIMEZ TOUT CE QUI SUIT 🚨
    # path('offline/', views.offline_category_selection, name='offline_category'), 
    # path('offline/play/<int:category_id>/', views.offline_game_view, name='offline_game'),
]