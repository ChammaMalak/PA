# Python_app/management/commands/generate_quiz.py

from django.core.management.base import BaseCommand
from Python_app.services import generate_and_save_question

class Command(BaseCommand):
    help = 'Génère des questions de quiz pour plusieurs catégories et niveaux de difficulté.'

    def add_arguments(self, parser):
       
        parser.add_argument(
            '--count',
            type=int,
            default=1,
            help='Nombre de questions à générer par catégorie ET par niveau de difficulté.'
        )

    def handle(self, *args, **options):
        count = options['count']
        
      
        difficulty_levels = [1, 2, 3]  # Facile, Moyen, Difficile
        
        categories_to_process = ["Géographie","Islam", "Histoire", "Sciences", "Informatique", "Culture Générale"] 
        
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"Démarrage de la génération : {count} questions pour chacun des {len(difficulty_levels)} niveaux ({difficulty_levels}) pour {len(categories_to_process)} catégories."
            )
        )

        for category_name in categories_to_process:
            self.stdout.write(f'\n--- Catégorie: {category_name} ---')
            
            #  Boucle sur les niveaux de difficulte
            for difficulty in difficulty_levels:
                self.stdout.write(self.style.NOTICE(f'  [ Niveau de Difficulté : {difficulty} ]'))
                
                for i in range(count):
                    self.stdout.write(f'    - Question {i + 1}/{count}: ', ending='')
                    try:
                        # Appel a la fonction de service avec le niveau actuel
                        new_question = generate_and_save_question(category_name, difficulty)
                        
                        if new_question:
                            self.stdout.write(self.style.SUCCESS(f'OK. ID: {new_question.id}'))
                        else:
                            self.stdout.write(self.style.WARNING(f'ÉCHEC. Question non sauvée (voir logs).'))
                            
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'ERREUR CRITIQUE. {e}'))
                        continue
        
        self.stdout.write(self.style.SUCCESS('\n✅ Base de données de questions remplie avec succès!'))