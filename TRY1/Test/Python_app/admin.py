from django.contrib import admin
from .models import User, Category, QuizQuestion, Answer, GameSession, PlayerScore, PlayerAnswer

admin.site.register(User)
admin.site.register(Category)
admin.site.register(QuizQuestion)
admin.site.register(Answer)
admin.site.register(GameSession)
admin.site.register(PlayerScore)
admin.site.register(PlayerAnswer)