from django.db import models


class User(models.Model):
    
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    passwordHash = models.CharField(max_length=255) 
    Role = models.CharField(max_length=20, default='Player') # 'Player', 'Admin'
    ControlTimestamp = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'user' 


class Category(models.Model):
    descriptor = models.CharField(max_length=100)

    def __str__(self):
        return self.descriptor
    
    class Meta:
        db_table = 'category'

class QuizQuestion(models.Model):
    text = models.TextField()
    
    Category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='questions')
    Difficulty = models.IntegerField()  
    TimeLimit = models.IntegerField()   

    def __str__(self):
        return self.text[:50]
    
    class Meta:
        db_table = 'quiz_question'


# NOTE: Fusionne CorrectAnswer et IncorrectAnswer
class Answer(models.Model):
    text = models.CharField(max_length=255)
    Question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='answers')
    
    IsCorrect = models.BooleanField(default=False) 
    
    # Contrainte pour s'assurer qu'il n'y a qu'une seule bonne réponse
    class Meta:
        constraints = [
           models.UniqueConstraint(fields=['Question', 'IsCorrect'], condition=models.Q(IsCorrect=True), name='unique_correct_answer')
       ]

    def __str__(self):
        return f"{self.Question.id}: {self.text[:30]}"
    
    class Meta:
        db_table = 'answer'

class GameSession(models.Model):
    PinCode = models.CharField(max_length=10, unique=True)
    
    Category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='sessions')
    
    Difficulty = models.IntegerField()
    Time = models.DateTimeField(auto_now_add=True) 
    def __str__(self):
        return f"Session: {self.PinCode}"
    
    class Meta:
        db_table = 'game_session'


class PlayerScore(models.Model):
 
    Session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='scores')
    User = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scores')
    
    Score = models.IntegerField(default=0)
    Time = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = (('Session', 'User'),)
        db_table = 'player_score'

class PlayerAnswer(models.Model):
    
    Question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='player_responses')
    User = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers')
    Session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='player_responses')
    
    Answer = models.ForeignKey(Answer, on_delete=models.SET_NULL, null=True, blank=True, related_name='player_selections')
    
    SubmitTimestamp = models.DateTimeField(auto_now_add=True)
    IsCorrect = models.BooleanField()
    ReactionTime = models.IntegerField(null=True, blank=True) 
    
    class Meta:
       
        unique_together = (('Question', 'User', 'Session'),)
        db_table = 'player_answer'