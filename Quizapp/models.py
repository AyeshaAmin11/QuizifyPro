import os
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


# Create your models here.
class QuizCategory(models.Model):
    cat_name = models.CharField(max_length=100)
    cat_image = models.ImageField(upload_to='cat_images/', null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.cat_name
    
    def delete(self, *args, **kwargs):
        # Delete the associated image file if it exists
        if self.cat_image:
            image_path = os.path.join(settings.MEDIA_ROOT, self.cat_image.name)
            if os.path.exists(image_path):
                os.remove(image_path)
        # Call the parent class's delete method
        super().delete(*args, **kwargs)


class Quiz(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Logged in user
    quiz_title = models.CharField(max_length=200)
    category = models.ForeignKey(QuizCategory, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    time_limit = models.CharField(max_length=200)
    total_marks = models.IntegerField(default=0)
    
    def __str__(self):
        return self.quiz_title


class Question(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Logged in user
    category = models.ForeignKey(QuizCategory, on_delete=models.CASCADE)
    quiz_number = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    difficulty_level = models.CharField(max_length=50)
    topic = models.CharField(max_length=200)
    question = models.TextField()  # Question text
    option1 = models.CharField(max_length=200)  # Option 1 (Mandatory)
    option2 = models.CharField(max_length=200)  # Option 2 (Mandatory)
    option3 = models.CharField(max_length=200, blank=True, null=True)  # Option 3 (Optional)
    option4 = models.CharField(max_length=200, blank=True, null=True)  # Option 4 (Optional)
    correct_answer = models.CharField(max_length=200)  # Correct Answer (Mandatory)

    def __str__(self):
        return self.question


class QuizResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=200)
    difficulty = models.CharField(max_length=50)
    obtained_marks = models.IntegerField()
    total_marks = models.IntegerField()
    submitted_at = models.DateTimeField(default=timezone.now)  # <-- Fixed here
    ai_review = models.TextField(blank=True, null=True)
    ai_review_generated = models.BooleanField(default=False)


    class Meta:
        verbose_name_plural = "Results"

    def __str__(self):
        return f"{self.user.username} - {self.category} ({self.difficulty})"


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz_result = models.ForeignKey(QuizResult, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField()  # Rating from 1 to 5
    message = models.TextField()  # Review message
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} on {self.quiz_result.category}"
    

class QuizLink(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(QuizCategory, on_delete=models.CASCADE)
    quiz_number = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    unique_link = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, blank=True, null=True)
    completed_by = models.ManyToManyField(User, related_name='completed_quizzes', blank=True)

    def __str__(self):
        return str(self.unique_link)


class UserSubscription(models.Model):
    email = models.EmailField()
    plan = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    subscribed_on = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.email} - {self.plan} ({'Active' if self.is_active else 'Inactive'})"


class Transaction(models.Model):
    email = models.EmailField()
    plan = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, unique=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.transaction_id)
