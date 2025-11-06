# Python_app/views.py

from django.shortcuts import render ,redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Category, QuizQuestion, Answer
from .services import generate_and_save_question
import random

# La vue d'accueil du site.
# Si l'utilisateur est connecté, elle affiche les options de jeu (Offline/Multijoueur).
# Si l'utilisateur n'est PAS connecté, elle affiche l'option Connexion/Inscription.
def home_view(request):
    """
    Affiche la page d'accueil du jeu de quiz.
    """
    # L'objet request.user vérifie automatiquement si l'utilisateur est connecté
    # grâce à Django.
    context = {
        'is_authenticated': request.user.is_authenticated,
        'user': request.user
    }
    return render(request, 'home.html', context)

#@login_required
def offline_category_selection(request):
    """
    Affiche la liste de toutes les catégories pour le jeu hors ligne.
    """
    categories = Category.objects.all()
    context = {
        'categories': categories,
        'page_title': "Choisir une Catégorie"
    }
    return render(request, 'offline/category_selection.html', context)

#@login_required
def offline_game_view(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    
    # -------------------------------------------------------------
    # LOGIQUE DE RÉCUPÉRATION/GÉNÉRATION DE LA QUESTION (Début du jeu)
    # -------------------------------------------------------------
    try:
        # Tente de récupérer une question existante
        # Vous pourriez vouloir utiliser request.session pour gérer la progression
        question = QuizQuestion.objects.filter(Category=category).order_by('?').first()

        if not question:
            # Tente de générer une question si la base est vide
            # NOTE : Assurez-vous que generate_and_save_question utilise le 'descriptor' de la catégorie
            question = generate_and_save_question(category.descriptor, difficulty=2)

        if not question:
            # Échec de la récupération ET de la génération
            message = "La base de données ne contient aucune question pour cette catégorie, et la génération via l'API a échoué ou a été désactivée."
            return render(request, 'error.html', {'message': message})
            
    except Exception as e:
        return render(request, 'error.html', {'message': f"Erreur critique lors de la préparation de la question : {e}"})

    # Récupérer toutes les réponses et les mélanger
    answers = list(question.answers.all()) # Mieux d'utiliser answer_set si 'answers' n'est pas le related_name
    random.shuffle(answers)
    
    # Préparation du contexte par défaut (pour l'affichage initial)
    context = {
        'category': category,
        'question': question,
        'answers': answers,
        'fixed_time': 15, # Temps de réponse fixe en secondes
        'page_title': f"Quiz : {category.descriptor}",
        'submitted': False, # État initial : la réponse n'a pas été soumise
    }
    
    # ---------------------------------------------
    # GESTION DE LA SOUMISSION DE LA RÉPONSE (POST)
    # ---------------------------------------------
    if request.method == 'POST':
        selected_answer_id = request.POST.get('answer_id')
        
        try:
            selected_answer = Answer.objects.get(pk=selected_answer_id)
            
            # CORRECTION CRITIQUE : Utiliser 'IsCorrect' (avec majuscule)
            is_correct = selected_answer.IsCorrect # <--- CORRECTION D'ATTRIBUT
            
            # Trouver la bonne réponse pour afficher le vert
            correct_answer = Answer.objects.get(Question=question, IsCorrect=True)
            
            # Ajouter les données de résultat au contexte pour le rendu HTML
            context.update({
                'submitted': True, # Permet d'activer la logique d'affichage vert/rouge
                'is_correct': is_correct,
                'submitted_answer_id': int(selected_answer_id),
                'correct_answer_id': correct_answer.pk,
                # Logique pour la prochaine question (pourrait être dans une session)
                # next_question_id = get_next_question_id(question_id, category_id)
                # 'next_question_id': next_question_id 
            })
            
            # On passe à l'étape suivante, le rendu de la même page avec les résultats
            
        except Answer.DoesNotExist:
            # L'utilisateur a soumis un ID invalide (à gérer plus proprement)
            pass

    # ---------------------------------------------
    # ÉTAPE FINALE: Rendre le template
    # ---------------------------------------------
    return render(request, 'offline/game.html', context)

@login_required 
def multiplayer_lobby_view(request):
    return HttpResponse("Page du Lobby Multijoueur (en construction)")


@login_required
def classements_view(request):
    return HttpResponse("Page du Lobby classements (en construction)")