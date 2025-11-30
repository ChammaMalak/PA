import json
import os
import time
from google import genai
from dotenv import load_dotenv, find_dotenv
from django.db import IntegrityError 
from .models import QuizQuestion, Category, Answer 
from django.core.exceptions import ObjectDoesNotExist

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    # fallback minimal: no-op loader that keeps using os.environ
    def load_dotenv(path: str = None):
        return False

try:
    from google.genai import errors as genai_errors  # type: ignore
except Exception:
    # minimal placeholder for expected exception types
    class genai_errors:
        class GoogleAPIError(Exception):
            pass
        class Error(Exception):
            pass

# Remplace la simple invocation load_dotenv() par une recherche explicite du .env
try:
    from dotenv import load_dotenv, find_dotenv  # type: ignore
except Exception:
    def load_dotenv(path: str = None):
        return False
    def find_dotenv():
        return None

# Charge les variables d'environnement (y compris GEMINI_API_KEY) depuis le fichier .env trouvé
env_path = find_dotenv()
if env_path:
    load_dotenv(env_path)
    print(f"[config] .env chargé depuis : {env_path}")
else:
    # Tentative supplémentaire : cherche dans le dossier parent du projet (compatibilité Windows)
    guessed = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Test', '.env'))
    if os.path.exists(guessed):
        load_dotenv(guessed)
        print(f"[config] .env chargé depuis chemin deviné : {guessed}")
    else:
        print("[config] Aucun .env trouvé par find_dotenv() ni chemin deviné. Continuation sans .env.")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"[config] GEMINI_API_KEY présent: {'YES' if GEMINI_API_KEY else 'NO'}")
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
    print("Erreur : La variable d'environnement GEMINI_API_KEY n'est pas définie. La génération AI est désactivée.")



def _local_generate_and_save(category_obj, difficulty: int, time_limit: int = 30):
    """Fallback local amélioré : crée une question variée et réaliste en base si l'IA n'est pas disponible.
    - Utilise un petit catalogue de questions par catégorie.
    - Génère 4 choix (1 correct + 3 distracteurs) et les sauvegarde.
    """
    import random

    def save_question(text, correct_answer, wrong_answers):
        try:
            # Eviter doublon exact
            if QuizQuestion.objects.filter(text__iexact=text, Category=category_obj).exists():
                return QuizQuestion.objects.filter(text__iexact=text, Category=category_obj).first()
            q = QuizQuestion.objects.create(
                text=text,
                Category=category_obj,
                Difficulty=difficulty,
                TimeLimit=time_limit
            )
            # Préparer les choix et marquer la bonne réponse
            choices = [correct_answer] + list(wrong_answers)
            random.shuffle(choices)
            for ch in choices:
                Answer.objects.create(
                    text=ch,
                    Question=q,
                    IsCorrect=(ch == correct_answer)
                )
            return q
        except Exception as e:
            print(f"[FALLBACK ERROR] Impossible de sauvegarder la question : {e}")
            return None

    # Catalogue simple — ajoutez/éditez selon vos besoins
    pool = {
        'géographie': [
            ("Quelle est la capitale de la France ?", "Paris", ["Lyon", "Marseille", "Toulouse"]),
            ("Quel est le plus grand océan du monde ?", "Océan Pacifique", ["Océan Atlantique", "Océan Indien", "Océan Arctique"]),
            ("Quel pays possède la plus grande superficie ?", "Russie", ["Canada", "États-Unis", "Chine"]),
        ],
        'geographie': [ # sans accent
            ("Quelle est la capitale de l'Allemagne ?", "Berlin", ["Munich", "Hambourg", "Francfort"]),
            ("Quel fleuve traverse Paris ?", "La Seine", ["La Loire", "Le Rhône", "La Garonne"]),
            ("Quelle montagne est la plus haute d'Europe ?", "Mont Blanc", ["Mont Elbrouz", "Mont Rosa", "Grossglockner"]),
        ],
        'histoire': [
            ("En quelle année Christophe Colomb a-t-il découvert l'Amérique (arrivée) ?", "1492", ["1453", "1517", "1607"]),
            ("Quel empire a construit la Grande Muraille ?", "Empire chinois (dynasties)", ["Empire romain", "Empire ottoman", "Empire perse"]),
            ("Quel événement marque le début de la Révolution française ?", "Prise de la Bastille", ["Traité de Versailles", "Couronnement de Louis XVI", "Guerre de Cent Ans"]),
        ],
        'sciences': [
            ("Quel est l'état de la matière qui a un volume défini mais pas de forme définie ?", "Liquide", ["Solide", "Gaz", "Plasma"]),
            ("Quel est l'unité de base de la vie ?", "Cellule", ["Atome", "Molécule", "Tissu"]),
            ("Quel gaz les plantes absorbent pour la photosynthèse ?", "Dioxyde de carbone", ["Oxygène", "Azote", "Hydrogène"]),
        ],
        'informatique': [
            ("Que signifie HTML ?", "HyperText Markup Language", ["HighText Machine Language", "Hyperlink and Text Markup Language", "Home Tool Markup Language"]),
            ("Quel protocole est utilisé pour sécuriser les connexions web (HTTPS) ?", "TLS/SSL", ["FTP", "SMTP", "IP"]),
            ("Quel mot décrit le stockage temporaire utilisé par un processeur ?", "Cache", ["Register", "Heap", "Stack"]),
        ],
        'islam': [
            ("Quel livre est considéré comme la source principale de la foi islamique ?", "Le Coran", ["La Bible", "La Torah", "Les Hadiths (complément)"]),
            ("Combien y a-t-il de prières obligatoires quotidiennes en Islam ?", "5", ["3", "4", "6"]),
            ("Quel est le mois du jeûne annuel chez les musulmans ?", "Ramadan", ["Muharram", "Shawwal", "Dhu al-Hijjah"]),
        ],
        'culture générale': [
            ("Combien de minutes comporte une heure ?", "60", ["30", "100", "45"]),
            ("Quelle couleur obtient-on en mélangeant le bleu et le jaune (couleurs pigmentaires) ?", "Vert", ["Violet", "Orange", "Marron"]),
            ("Quel instrument a 6 cordes et est souvent utilisé dans la musique pop/rock ?", "Guitare", ["Piano", "Violon", "Saxophone"]),
        ],
        'default': [
            ("Quelle est la couleur du ciel en journée (sans nuages) ?", "Bleu", ["Vert", "Rouge", "Noir"]),
            ("Combien de jours contient une semaine ?", "7", ["5", "6", "8"]),
            ("Quel sens utilise-t-on pour écouter ?", "Ouïe", ["Vue", "Goût", "Toucher"]),
        ]
    }

    key = category_obj.descriptor.lower()
    bucket = pool.get(key) or pool.get(key.replace('é','e')) or pool.get('default')

    # Choix en fonction de la difficulté : index plus élevé => question plus loin dans la liste si possible
    if difficulty <= 1:
        idx = 0
    elif difficulty == 2:
        idx = min(1, len(bucket)-1)
    else:
        idx = min(2, len(bucket)-1)

    q_text, correct, wrongs = bucket[idx]
    # Pour varier légèrement, permuter wrongs ou modifier un distracteur simple
    wrongs = list(wrongs)
    random.shuffle(wrongs)

    return save_question(q_text, correct, wrongs[:3])

# --- NEW: safe reference to GoogleAPIError to avoid AttributeError if module exists but name missing ---
try:
    GoogleAPIError = getattr(genai_errors, 'GoogleAPIError', Exception)
except Exception:
    GoogleAPIError = Exception

def generate_and_save_question(category: str, difficulty: int, time_limit: int = 30):
    global gemini_client
   
    if gemini_client is None:
        print("Warning: gemini_client is not initialized. Using local fallback generator.")
        try:
            # si la catégorie n'existe pas, la créer pour permettre le fallback local
            category_obj, created = Category.objects.get_or_create(descriptor=category)
            if created:
                print(f"[FALLBACK] Catégorie '{category}' créée automatiquement pour fallback.")
        except Exception as e:
            print(f"Erreur BDD lors du get_or_create pour la catégorie '{category}': {e}")
            return None
        return _local_generate_and_save(category_obj, difficulty, time_limit)
        
    # 1. Vérification de l'existence de la Catégorie
    try:
        category_obj = Category.objects.get(descriptor=category) 
    except ObjectDoesNotExist:
        print(f"Erreur BDD: La catégorie '{category}' n'existe pas dans la base de données.")
        # essayer de créer pour permettre la génération locale ultérieure
        try:
            category_obj, created = Category.objects.get_or_create(descriptor=category)
            print(f"[INFO] Création automatique de la catégorie '{category}' pour la génération.")
        except Exception as e:
            print(f"Impossible de créer la catégorie '{category}': {e}")
            return None
    
    # 2. Préparation du Prompt
    prompt = f"""
    Génère une question de quiz de niveau {difficulty} sur le thème "{category}". 
La question doit être **concise et ne pas dépasser deux lignes**.
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

        except GoogleAPIError as e:
            # Si la clé est bloquée/invalidée => ne plus réessayer, utiliser fallback local
            err_str = str(e)
            if 'PERMISSION_DENIED' in err_str or '403' in err_str or getattr(e, 'code', None) == 403:
                print("[API] Permission denied (API key invalid/blocked). Disabling remote generation and using local fallback.")
                # Désactive le client global pour éviter futurs appels
                gemini_client = None
                try:
                    category_obj, _ = Category.objects.get_or_create(descriptor=category)
                except Exception as ex:
                    print(f"[FALLBACK ERROR] Impossible d'obtenir/créer la catégorie '{category}': {ex}")
                    return None
                return _local_generate_and_save(category_obj, difficulty, time_limit)

            # Sinon gérer surcharge comme avant
            if "503 UNAVAILABLE" in err_str or "OVERLOADED" in err_str:
                if attempt < MAX_RETRIES - 1:
                    delay = BASE_DELAY * (2 ** attempt)
                    print(f"Modèle surchargé (503). Attente de {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    print(f"Échec final de l'appel à l'API après {MAX_RETRIES} tentatives : {e}")
                    break
            else:
                print(f"Erreur API inattendue : {e}")
                break

        except Exception as e:
            print(f"Erreur de connexion/inattendue lors de l'appel à l'API : {e}")
            break

    # si aucune réponse ou si client désactivé -> fallback
    if response is None or gemini_client is None:
        print("Utilisation du fallback local (questions factices).")
        try:
            category_obj, _ = Category.objects.get_or_create(descriptor=category)
        except Exception as ex:
            print(f"[FALLBACK ERROR] Impossible d'obtenir/créer la catégorie '{category}': {ex}")
            return None
        return _local_generate_and_save(category_obj, difficulty, time_limit)

    # 4. Traitement de la Réponse et Sauvegarde BDD
    try:
        json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(json_text)
        
        # Validation de base des champs JSON
        if not all(key in data for key in ["question", "correct_answer", "incorrect_answers"]):
            raise ValueError("Le format JSON retourné par l'IA est incomplet.")
    except Exception as e:
        # En cas d'erreur d'analyse JSON ou valeur manquante -> fallback local
        print(f"Erreur lors du parsing JSON ou format incorrect: {e}. Utilisation du fallback local.")
        try:
            category_obj = Category.objects.get(descriptor=category)
        except ObjectDoesNotExist:
            print(f"Erreur BDD: La catégorie '{category}' n'existe pas dans la base de données.")
            return None
        return _local_generate_and_save(category_obj, difficulty, time_limit)

   # 4.5. Vérification des doublons de questions DANS LA MÊME CATÉGORIE
    try:
        existing_question = QuizQuestion.objects.filter(
            text__iexact=data['question'], 
            Category=category_obj
        ).first()

        if existing_question:
            print(f"ALERTE: Question déjà existante (ID: {existing_question.pk}) dans la catégorie '{category}'. Ignorée.")
            return None # Empêche la sauvegarde du doublon
    except Exception as e:
        print(f"Erreur lors de la vérification des doublons : {e}")
        # On continue quand même si la vérification échoue, mais on alerte
        pass
    
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