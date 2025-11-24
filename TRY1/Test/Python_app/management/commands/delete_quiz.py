from django.core.management.base import BaseCommand
# Assurez-vous que les imports de vos modèles sont corrects (ici .models)
from Python_app.models import QuizQuestion, Answer 

class Command(BaseCommand):
    help = 'Supprime TOUTES les questions de quiz et leurs réponses associées.'

    def handle(self, *args, **options):
        # La suppression des QuizQuestion entraîne la suppression des Answer
        # si vous avez configuré 'on_delete=models.CASCADE' sur la clé étrangère.
        
        question_count = QuizQuestion.objects.count()
        if question_count == 0:
            self.stdout.write(self.style.SUCCESS("✅ Aucune question de quiz à supprimer."))
            return

        self.stdout.write(
            self.style.WARNING(f"⚠️ Suppression de {question_count} questions de quiz et leurs réponses...")
        )

        # L'utilisation de .all().delete() est efficace pour supprimer tous les objets
        deleted_count, details = QuizQuestion.objects.all().delete()

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Suppression réussie! {deleted_count} objets ont été supprimés de la base de données."
        ))