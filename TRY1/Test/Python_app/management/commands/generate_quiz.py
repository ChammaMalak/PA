from django.core.management.base import BaseCommand
# Assurez-vous d'importer time pour le time.sleep dans la boucle d'attente
import time
from Python_app.services import generate_and_save_question

class Command(BaseCommand):
    help = 'Génère des questions de quiz pour plusieurs catégories et niveaux de difficulté, en s\'assurant de générer le nombre exact de questions UNIQUES.'

    def add_arguments(self, parser):
        
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Nombre de questions à générer par catégorie ET par niveau de difficulté.'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Le temps de pause (en secondes) après un échec/doublon avant de réessayer
        DELAY_ON_FAILURE = 1 
        # Le nombre maximum de fois où l'on essaie de générer une question pour un même slot
        MAX_ATTEMPTS_PER_QUESTION = 5
        
        difficulty_levels = [1, 2, 3]  # Facile, Moyen, Difficile
        
        categories_to_process = ["Géographie","Islam", "Histoire", "Sciences", "Informatique", "Culture Générale"] 
        
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"Démarrage de la génération : {count} questions UNIQUES pour chacun des {len(difficulty_levels)} niveaux ({difficulty_levels}) pour {len(categories_to_process)} catégories."
            )
        )

        for category_name in categories_to_process:
            self.stdout.write(f'\n--- Catégorie: {category_name} ---')
            
            # Boucle sur les niveaux de difficulte
            for difficulty in difficulty_levels:
                self.stdout.write(self.style.NOTICE(f'  [ Niveau de Difficulté : {difficulty} ]'))
                
                # NOUVEAU SYSTÈME DE BOUCLE (RÉTENTION)
                questions_generated = 0

                # Boucle principale: continue tant que 'count' questions uniques n'ont pas été générées
                while questions_generated < count:
                    self.stdout.write(f'     - Question {questions_generated + 1}/{count}: ', ending='')
                    
                    # Boucle secondaire: tente de générer une question unique
                    for attempt in range(MAX_ATTEMPTS_PER_QUESTION):
                        try:
                            # Appel a la fonction de service avec le niveau actuel
                            new_question = generate_and_save_question(category_name, difficulty)
                            
                            if new_question:
                                # Succès : La question est unique et sauvegardée
                                self.stdout.write(self.style.SUCCESS(f'OK. ID: {new_question.id}'))
                                questions_generated += 1  # Incrémenter le compteur de succès
                                break # Sortir de la boucle d'essai
                            else:
                                # ÉCHEC (Doublon ou Erreur de Service)
                                if attempt < MAX_ATTEMPTS_PER_QUESTION - 1:
                                    # Tenter à nouveau
                                    self.stdout.write(self.style.WARNING(f'ÉCHEC/Doublon (Ré-essai {attempt + 2}/{MAX_ATTEMPTS_PER_QUESTION} après {DELAY_ON_FAILURE}s)...'), ending='')
                                    time.sleep(DELAY_ON_FAILURE) 
                                    continue # Passe à la tentative suivante
                                else:
                                    # Échec après toutes les tentatives
                                    self.stdout.write(self.style.ERROR(f'ÉCHEC FINAL. Impossible de générer une question unique après {MAX_ATTEMPTS_PER_QUESTION} essais.'))
                                    questions_generated += 1 # Avancer pour ne pas bloquer le script
                                    break # Sortir de la boucle d'essai
                                    
                        except Exception as e:
                            # Erreur critique du système ou de la base de données
                            self.stdout.write(self.style.ERROR(f'ERREUR CRITIQUE. {e}'))
                            questions_generated += 1 # Avancer pour ne pas bloquer le script
                            break # Sortir de la boucle d'essai
                            
        self.stdout.write(self.style.SUCCESS('\n✅ Base de données de questions remplie avec succès!'))