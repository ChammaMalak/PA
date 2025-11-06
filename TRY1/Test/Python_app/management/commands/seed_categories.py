# Python_app/management/commands/seed_categories.py

from django.core.management.base import BaseCommand
from Python_app.models import Category

class Command(BaseCommand):
    help = 'Crée les catégories de base si elles n\'existent pas.'

    def handle(self, *args, **options):
        # Liste de vos catégories
        categories_list = [
            "Géographie", 
            "Histoire", 
            "Sciences", 
            "Informatique", 
            "Islam", 
            "Culture Générale"
        ]
        
        created_count = 0
        
        self.stdout.write(self.style.MIGRATE_HEADING("Démarrage du remplissage des catégories..."))

        for category_name in categories_list:
            #  vérifie si l'objet existe. Si oui, il le récupère. Sinon, il le crée.
            category, created = Category.objects.get_or_create(
                descriptor=category_name 
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"  -> Catégorie '{category_name}' créée."))
                created_count += 1
            else:
                self.stdout.write(f"  -> Catégorie '{category_name}' existe déjà. Ignorée.")
                
        self.stdout.write(self.style.SUCCESS(f"\n✅ Opération terminée. {created_count} nouvelles catégories créées."))