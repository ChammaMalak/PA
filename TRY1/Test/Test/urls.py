
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 🚨 LIGNE CRITIQUE 1: Définition explicite du nom 'logout'
    # Ceci garantit que le nom existe avant que le template d'accueil ne le cherche.
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'), 
    
    # LIGNE CRITIQUE 2: Inclusion des autres URLs d'authentification (login, etc.)
    path('accounts/', include('django.contrib.auth.urls')), 
    
    # LIGNE CRITIQUE 3: Inclusion de votre application à la racine (/)
    path('', include('Python_app.urls')),
    path('admin/', admin.site.urls),
    path('', include('Python_app.urls')),
]
