import json
import os
import time
from google import genai
from dotenv import load_dotenv
from django.db import IntegrityError 
from google.genai.errors import APIError 
from .models import QuizQuestion, Category, Answer 
from django.core.exceptions import ObjectDoesNotExist

# Charge les variables d'environnement (y compris GEMINI_API_KEY) depuis le fichier .env
load_dotenv()


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = None 
MODEL_NAME = 'gemini-2.5-flash'

if GEMINI_API_KEY:
    try:
        # Initialisation du client 
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        print("Client Gemini initialisé avec succès.")
    except Exception as e:
        print(f"Erreur fatale lors de l'initialisation du client Gemini : {e}")
        gemini_client = None
else:
    print("Erreur : La variable d'environnement GEMINI_API_KEY n'est pas définie dans .env. La génération AI est désactivée.")



def generate_and_save_question(category: str, difficulty: int, time_limit: int = 30):
   
    if gemini_client is None:
        print("Erreur: Le client Gemini n'est pas initialisé (Clé API manquante ou invalide).")
        return None
        
    # 1. Vérification de l'existence de la Catégorie
    try:
        category_obj = Category.objects.get(descriptor=category) 
    except ObjectDoesNotExist:
        print(f"Erreur BDD: La catégorie '{category}' n'existe pas dans la base de données.")
        return None
    
    # 2. Préparation du Prompt
    prompt = f"""
    Génère une question de quiz de niveau {difficulty} sur le thème "{category}".
    La réponse doit être STRICTEMENT au format JSON : 
    {{ 
        "question": "Votre question ici", 
        "correct_answer": "La bonne réponse", 
        "incorrect_answers": ["Fausses réponse 1", "Fausses réponse 2", "Fausses réponse 3"] 
    }}
    NE RÉPONDEZ QU'AVEC LE CODE JSON.
    """

    # 3. Appel à l'API avec Nouvelle Tentative
    MAX_RETRIES = 3 
    BASE_DELAY = 5
    response = None

    for attempt in range(MAX_RETRIES):
        try:
            print(f"Génération de la question sur '{category}' (Diff. {difficulty}) - Tentative {attempt + 1}/{MAX_RETRIES}...")
            
            response = gemini_client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )
            # Succès : sortir de la boucle
            break 

        except APIError as e:
            # Gérer la surcharge (503 UNAVAILABLE)
            if "503 UNAVAILABLE" in str(e) or "OVERLOADED" in str(e):
                if attempt < MAX_RETRIES - 1:
                    delay = BASE_DELAY * (2 ** attempt)
                    print(f"Modèle surchargé (503). Attente de {delay}s...")
                    time.sleep(delay)
                else:
                    print(f"Échec final de l'appel à l'API après {MAX_RETRIES} tentatives : {e}")
                    return None
            else:
                # Gérer d'autres erreurs API (quota, clé invalide)
                print(f"Erreur API inattendue : {e}")
                return None 
        
        except Exception as e:
            # Gérer les erreurs de connexion, etc.
            print(f"Erreur de connexion/inattendue lors de l'appel à l'API : {e}")
            return None

    # Si la boucle a échoué toutes les tentatives
    if response is None:
        return None

    # 4. Traitement de la Réponse et Sauvegarde BDD
    try:
        json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(json_text)
        
        # Validation de base des champs JSON
        if not all(key in data for key in ["question", "correct_answer", "incorrect_answers"]):
            raise ValueError("Le format JSON retourné par l'IA est incomplet.")

    except json.JSONDecodeError as e:
        print(f"Erreur lors de l'analyse JSON : {e}")
        
        return None
    except ValueError as e:
        print(f"Erreur de données : {e}")
        return None
    
    # 5. Sauvegarde en Base de Données
    try:
        # Création de la Question
        new_question = QuizQuestion.objects.create(
            text=data['question'],
            Category=category_obj,   
            Difficulty=difficulty,
            TimeLimit=time_limit
        )
        print(f"Question (ID: {new_question.pk}) créée : {new_question.text[:40]}...")

        # Création de la Vraie Réponse
        Answer.objects.create(
            text=data['correct_answer'],
            Question=new_question, 
            IsCorrect=True
        )
        
        # Création des Fausses Réponses
        for incorrect_text in data['incorrect_answers']:
           Answer.objects.create(
                text=incorrect_text,
                Question=new_question,
                IsCorrect=False
            )
            
        print("Réponses enregistrées avec succès.")
        return new_question
        
    except IntegrityError as e:
        print(f"Erreur d'intégrité de la base de données lors de la sauvegarde : {e}")
        return None
    except Exception as e:
        print(f"Erreur inattendue lors de la sauvegarde en BDD : {e}")
        return None