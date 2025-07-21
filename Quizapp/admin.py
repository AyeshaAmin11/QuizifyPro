from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.QuizCategory)

admin.site.register(models.Quiz)

class QuizAdmin(admin.ModelAdmin):
    list_display = ['category','quiz_number','difficulty_level','topic', 'question','option1','option2','option3','option4','correct_answer']
admin.site.register(models.Question,QuizAdmin)

admin.site.register(models.QuizResult)  # Basic registration without customization

admin.site.register(models.Review)

admin.site.register(models.QuizLink)

admin.site.register(models.UserSubscription)

admin.site.register(models.Transaction)