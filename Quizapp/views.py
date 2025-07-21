import os
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from . import models
from django.contrib import messages
import google.generativeai as genai
import re
from django.utils.safestring import mark_safe
import json
from django.utils.timezone import now
from django.http import HttpResponseBadRequest
import uuid
from django.urls import reverse



genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)


# Create your views here.
def HomePage(request):
    return render(request, 'index.html')

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def LoginPage(request):
    if request.method == 'POST':
        user_name_login = request.POST.get('username')
        password_login = request.POST.get('password')
        user_type = request.POST.get('user_type')  # Get user type from dropdown

        login_user = authenticate(request, username=user_name_login, password=password_login)

        if login_user is not None:
            login(request, login_user)
            # Check if user is superuser
            if user_type == 'educator' and login_user.is_superuser:
                return redirect('educator_home')
            elif user_type == 'student' and not login_user.is_superuser:
                return redirect('student_home')
            else:
                return render(request, 'login.html', {
                'error_message': 'Incorrect User Type Selected.' })
        else:
            return render(request, 'login.html', {
                'error_message': 'Username or Password Incorrect.' })

    return render(request, 'login.html')

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def register_page(request):
    if request.method == 'POST':
        # Get common form data
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')
        user_type = request.POST.get('user_type')  # 'student' or 'educator'

        # Validate passwords match
        if pass1 != pass2:
            return render(request, 'register.html', {
                'error_message': 'Your Password and Confirm Password are not the same.'
            })

        # Create user based on type
        if user_type == 'student':
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=pass1
            )
        elif user_type == 'educator':
            user = User.objects.create_superuser(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=pass1
            )
        else:
            return render(request, 'register.html', {
                'error_message': 'Invalid user type selected.'
            })

        user.save()
        return redirect('login')

    return render(request, 'register.html')

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@login_required
def EducatorHomePage(request):
    user = request.user
    return render(request, 'educator_home.html', {'user': user})

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@login_required
def StudentHomePage(request):
    user = request.user
    return render(request, 'student_home.html', {'user': user})

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@login_required
def CategoryList(request):
    categories = models.QuizCategory.objects.all()
    return render(request, 'category_list.html', {'categories': categories})

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@login_required
def AddQuizCategory(request):
    if request.method == 'POST':
        category_name = request.POST.get('name')
        category_image = request.FILES.get('image')  # Get the uploaded image file

        # Check if the category already exists
        if models.QuizCategory.objects.filter(cat_name=category_name).exists():
            return render(request, 'add_category.html', {
                'error_message': "Category already exists."
            })

        # Save new category with the image
        new_category = models.QuizCategory(cat_name=category_name, cat_image=category_image)
        new_category.save()

        return redirect('category_list')

    return render(request, 'add_category.html')

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@login_required
def update_category(request, category_id):
    category = get_object_or_404(models.QuizCategory, id=category_id)

    if request.method == 'POST':
        # Update category name
        category.cat_name = request.POST.get('cat_name')

        # Update category image if a new file is uploaded
        if 'cat_image' in request.FILES:
            # Delete the old image file if it exists
            if category.cat_image:
                old_image_path = os.path.join(settings.MEDIA_ROOT, category.cat_image.name)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)

            # Save the new image
            category.cat_image = request.FILES['cat_image']

        # Save changes
        category.save()
        messages.success(request, "Category updated successfully!")
        return redirect('category_list')

    return render(request, 'update_category.html', {'category': category})

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@login_required
def confirm_delete_category(request, category_id):
    category = get_object_or_404(models.QuizCategory, id=category_id)

    if request.method == 'POST':
        # Delete the associated image file if it exists
        if category.cat_image:
            image_path = os.path.join(settings.MEDIA_ROOT, category.cat_image.name)
            if os.path.exists(image_path):
                os.remove(image_path)

        # Delete the category
        category.delete()
        messages.success(request, "Category deleted successfully!")
        return redirect('category_list')

    # Render the confirmation template for GET requests
    return render(request, 'confirm_delete.html', {'category': category})

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@login_required
def category_question_list(request,cat_id):
    categoryQuestion=models.QuizCategory.objects.get(id=cat_id)
    questions=models.Quiz.objects.filter(category=categoryQuestion)
    return render(request,'category_question_list.html',{'category':categoryQuestion,'questions':questions})

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@login_required
def quiz_list(request, category_id):
    category = get_object_or_404(models.QuizCategory, id=category_id)
    quizzes = models.Quiz.objects.filter(category=category, user=request.user).order_by('-created_at')
    return render(request, 'quiz_list.html', {'category': category, 'quizzes': quizzes})

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@login_required
def add_quiz(request, category_id):
    category = get_object_or_404(models.QuizCategory, id=category_id)
    if request.method == 'POST':
        title = request.POST.get('quiz_title')
        time_limit = request.POST.get('time_limit')
        total_marks = request.POST.get('total_marks')
        if title and time_limit:
            models.Quiz.objects.create(
                user=request.user,
                quiz_title=title,
                category=category,
                time_limit=time_limit,
                total_marks=total_marks
            )
            return redirect('quiz_list', category_id=category_id)
    return render(request, 'add_quiz.html', {'category': category})

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# Update quiz
@login_required
def update_quiz(request, quiz_id):
    quiz = get_object_or_404(models.Quiz, id=quiz_id, user=request.user)
    if request.method == 'POST':
        quiz.quiz_title = request.POST.get('quiz_title')
        quiz.time_limit = request.POST.get('time_limit')
        quiz.save()
        return redirect('quiz_list', category_id=quiz.category.id)
    return render(request, 'update_quiz.html', {'quiz': quiz})

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# Delete quiz
@login_required
def delete_quiz(request, quiz_id):
    quiz = get_object_or_404(models.Quiz, id=quiz_id, user=request.user)
    category_id = quiz.category.id
    quiz.delete()
    messages.success(request, "Quiz deleted successfully.")
    return redirect('quiz_list', category_id=category_id)

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# Show all questions in a quiz
@login_required
def question_list(request, category_id, quiz_id):
    category = get_object_or_404(models.QuizCategory, id=category_id)
    quiz = get_object_or_404(models.Quiz, id=quiz_id, user=request.user)
    questions = models.Question.objects.filter(quiz_number=quiz, category=category, user=request.user).order_by('id')
    return render(request, 'question_list.html', {'quiz': quiz, 'category':category, 'questions': questions})

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@login_required
def CategoryLinkList(request):
    categories_link = models.QuizCategory.objects.all()
    return render(request, 'category_link_list.html', {'categories_link': categories_link})


@login_required
def quiz_linkList(request, category_id):
    categories_link = get_object_or_404(models.QuizCategory, id=category_id)
    quizes = models.Quiz.objects.filter(category=categories_link).order_by('-created_at')
    return render(request, 'linked_quiz_list.html', {'categories_link': categories_link, 'quizes': quizes})



# Show all questions in a quiz
@login_required
def all_quizes_list(request, category_id, quiz_id):
    category = get_object_or_404(models.QuizCategory, id=category_id)
    quiz = get_object_or_404(models.Quiz, id=quiz_id)
    mcqs = models.Question.objects.filter(quiz_number=quiz, category=category).order_by('id')

    # Check if a QuizLink exists for this quiz (even if no link_id is provided)
    quiz_link = models.QuizLink.objects.filter(
        quiz_number=quiz,
        category=category,
        user=request.user
    ).first()  # Get the first matching link or None

    return render(request, 'all_question_list.html', {
        'categories_link': category,
        'quizes': quiz,
        'quiz_link': quiz_link,  # Pass the link (or None)
        'mcqs': mcqs
    })
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def shared_quiz(request, unique_link):
    quiz_link = get_object_or_404(models.QuizLink, unique_link=unique_link)
    quiz = quiz_link.quiz_number
    category = quiz_link.category
    mcqs = models.Question.objects.filter(quiz_number=quiz, category=category)
    
    return render(request, 'shared_quiz.html', {
        'quiz': quiz,
        'mcqs': mcqs,
    })

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# Add a new question
@login_required
def add_question(request, quiz_id):
    quiz = get_object_or_404(models.Quiz, id=quiz_id, user=request.user)
    if request.method == 'POST':
        difficulty = request.POST.get('difficulty_level')
        topic = request.POST.get('topic')
        question_text = request.POST.get('question')
        option1 = request.POST.get('option1')
        option2 = request.POST.get('option2')
        option3 = request.POST.get('option3')
        option4 = request.POST.get('option4')
        correct_answer = request.POST.get('correct_answer')
        if question_text and option1 and option2 and correct_answer:
            models.Question.objects.create(
                user=request.user,
                category=quiz.category,
                quiz_number=quiz,
                difficulty_level=difficulty,
                topic=topic,
                question=question_text,
                option1=option1,
                option2=option2,
                option3=option3,
                option4=option4,
                correct_answer=correct_answer
            )
            return redirect('question_list', quiz_id=quiz.id)
    return render(request, 'add_question.html', {'quiz': quiz})

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# Update question
@login_required
def update_question(request, question_id):
    question = get_object_or_404(models.Question, id=question_id, user=request.user)
    if request.method == 'POST':
        question.difficulty_level = request.POST.get('difficulty_level')
        question.topic = request.POST.get('topic')
        question.question = request.POST.get('question')
        question.option1 = request.POST.get('option1')
        question.option2 = request.POST.get('option2')
        question.option3 = request.POST.get('option3')
        question.option4 = request.POST.get('option4')
        question.correct_answer = request.POST.get('correct_answer')
        question.save()
        messages.success(request, "Question updated successfully.")
        return redirect('question_list', category_id=question.category.id, quiz_id=question.quiz_number.id)
    return render(request, 'update_question.html', {'question': question})

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@login_required
def delete_question(request, question_id):
    question = get_object_or_404(models.Question, id=question_id, user=request.user)
    category_id = question.category.id
    quiz_id = question.quiz_number.id

    if request.method == 'POST':
        question.delete()
        messages.success(request, "Question deleted successfully.")
        return redirect('question_list', category_id=category_id, quiz_id=quiz_id)

    # Optional: render a confirmation page
    return render(request, 'confirm_delete_question.html', {'question': question})

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def parse_gemini_response(text, topic_questions, category, difficulty):
    questions = []
    
    # Regex to split questions correctly
    parts = re.split(r"\bQuestion\s*\d*:", text, flags=re.IGNORECASE)

    for part in parts[1:]:  # Skip the first empty split
        lines = part.strip().split("\n")
        if len(lines) < 5:  # Ensure enough lines for a valid question
            continue
        
        question = lines[0].strip()
        question = re.sub(r"\*\*", "", question).strip()
        options = {}
        correct = ""

        for line in lines[1:]:
            line = line.strip()
            option_match = re.match(r"\((.)\)\s*(.*)", line, re.IGNORECASE)
            correct_match = re.match(r"\*\*Correct answer:\*\*\s*\((.)\)\s*(.*)", line, re.IGNORECASE)

            if option_match:
                options[option_match.group(1).lower()] = option_match.group(2)
            elif correct_match:
                correct = correct_match.group(1).lower().strip()

        if len(options) == 4 and question and correct in options:
            questions.append({
                "category": category,
                "difficulty": difficulty,
                "topic": topic_questions,
                "question": question,
                "option1": options.get('a', ''),
                "option2": options.get('b', ''),
                "option3": options.get('c', ''),
                "option4": options.get('d', ''),
                "correct_answer": options.get(correct, '')
            })
    
    return questions

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@login_required
def add_gpt_quiz(request, quiz_id, category_id):
    quiz = get_object_or_404(models.Quiz, id=quiz_id)
    category = get_object_or_404(models.QuizCategory, id=category_id)
    
    if request.method == 'POST':
        difficulty = request.POST.get('difficulty')
        topic_questions = request.POST.get('topic')
        question_numbers = request.POST.get('question_numbers')
        
        # Generate prompt using the pre-selected category
        prompt = f"""Generate {question_numbers} multiple-choice questions with some true false also for this "{topic_questions}" of category "{category.cat_name}" with {difficulty.lower()} difficulty.
        Format each question as:
        **Question:** [question text]
        (A) [option A]
        (B) [option B]
        (C) [option C]
        (D) [option D]
        **Correct Answer:** ([correct answer])"""
        
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        response = model.generate_content(prompt)
        
        if response and response.text:
            parsed_questions = parse_gemini_response(response.text, topic_questions, category, difficulty)
            if parsed_questions:
                for q in parsed_questions:
                    models.Question.objects.create(
                        user=request.user,
                        category=category,
                        quiz_number=quiz,
                        difficulty_level=difficulty,
                        topic = topic_questions,
                        question=q['question'],
                        option1=q['option1'],
                        option2=q['option2'],
                        option3=q['option3'],
                        option4=q['option4'],
                        correct_answer=q['correct_answer'],
                    )
                messages.success(request, f"Successfully created {len(parsed_questions)} questions!")
                return redirect('quiz_list', category_id=category.id)
            else:
                messages.error(request, "Failed to parse questions from response")
        else:
            messages.error(request, "Failed to get response from Gemini API")
    
    return render(request, 'add_gpt_quiz.html', {
        'category': category,
        'difficulty_levels': ['Easy', 'Medium', 'Difficult']
    })

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def generate_quiz_code(request, quiz_id):
    quiz = get_object_or_404(models.Quiz, id=quiz_id)
    category = quiz.category
    user = request.user

    # Get or create the link
    quiz_link, created = models.QuizLink.objects.get_or_create(
        user=user,
        category=category,
        quiz_number=quiz,
        defaults={'unique_link': uuid.uuid4()}
    )

    if created:
        messages.success(request, "Unique shareable link generated!")
    else:
        messages.info(request, "Shareable link already exists.")

    # Redirect with the link_id
    return redirect(
        reverse('all_quizes_list', kwargs={'category_id': category.id, 'quiz_id': quiz.id}) + f'?link_id={quiz_link.id}'
    )
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@login_required
def quiz_link(request):
    quizLink = models.QuizLink.objects.all()
    return render(request, 'quiz_link_list.html', {'linksQuiz': quizLink})


#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@login_required
def take_quiz(request):
    # Get all quiz links NOT completed by the current user
    quiz_link = models.QuizLink.objects.exclude(completed_by=request.user)
    
    return render(request, 'takeQuiz.html', {
        'linksQuiz': quiz_link,
        'error_message': request.GET.get('error_message', None)
    })


#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@login_required 
def quiz_solver(request, category_id, quiz_number, unique_link):
    try:
        # 1. Validate the unique link and fetch the associated QuizLink
        quiz_link = get_object_or_404(
            models.QuizLink,
            category_id=category_id,
            quiz_number_id=quiz_number,
            unique_link=unique_link
        )

        # 2. Extract quiz and category data
        quiz = quiz_link.quiz_number
        category = quiz_link.category.cat_name
        total_time = quiz.time_limit
        total_marks = quiz.total_marks

        # 3. Fetch related questions, limit by total_marks
        questions = models.Question.objects.filter(quiz_number=quiz)[:total_marks]

        # 4. Convert questions to list of dicts
        quizzes = [
            {
                'question': q.question,
                'option1': q.option1,
                'option2': q.option2,
                'option3': q.option3,
                'option4': q.option4,
                'correct_answer': q.correct_answer
            }
            for q in questions
        ]

        # 5. Pass everything to template context
        context = {
        'category': category,
        'difficulty': questions[0].difficulty_level if questions else 'N/A',
        'quizzes_json': json.dumps(quizzes),
        'total_time': total_time,
        'total_questions': len(questions),
        'unique_link': unique_link,  # Add this line
    }

        return render(request, 'quizsolver.html', context)

    except Exception as e:
        # For development/debugging — change this to a custom error page in production
        return HttpResponse(f"An error occurred: {str(e)}")
    
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def quiz_page(request, quiz_id):
    quiz = get_object_or_404(models.Quiz, id=quiz_id)
    questions = models.Quiz.objects.filter(quiz=quiz)

    return render(request, 'quizsolver.html', {
        'category': quiz.category.cat_name,
        'difficulty': quiz.difficulty_level,
        'questions': questions
    })


#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@login_required
def ThankuPage(request):
    return render(request, 'thank_you.html')
    
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@login_required
def save_quiz_result(request):
    if request.method == "POST":
        user = request.user
        category = request.POST.get('category')
        difficulty = request.POST.get('difficulty')
        obtained_marks = int(request.POST.get('obtained_marks', 0))
        total_marks = int(request.POST.get('total_marks', 0))
        unique_link = request.POST.get('unique_link')  # You'll need to pass this from your form

        # Save result to database
        quiz_result = models.QuizResult.objects.create(
            user=user,
            category=category,
            difficulty=difficulty,
            obtained_marks=obtained_marks,
            total_marks=total_marks,
            submitted_at=now()
        )

        # Mark quiz as completed by this user
        if unique_link:
            try:
                quiz_link = models.QuizLink.objects.get(unique_link=unique_link)
                quiz_link.completed_by.add(request.user)
            except models.QuizLink.DoesNotExist:
                pass  # Handle case where link doesn't exist

        return redirect('thank_you')  # Redirect to thank you page

    return redirect('quiz_page')  # Redirect if accessed incorrectly
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@login_required
def StudentResults(request):
    # Get all results with related user data in a single query
    student_results = models.QuizResult.objects.select_related('user').all().order_by('-submitted_at')
    
    # Add calculated fields to each result
    for result in student_results:
        result.percentage = (result.obtained_marks / result.total_marks) * 100
        result.full_name = result.user.get_full_name() or result.user.username
    
    context = {
        'student_results': student_results,
    }
    return render(request, 'result_students_list.html', context)

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@login_required
def user_quiz_results(request):
    user_results = models.QuizResult.objects.filter(user=request.user).order_by('-submitted_at')
    
    # Generate AI reviews for any results that don't have them
    for result in user_results:
        if not result.ai_review_generated:
            result.ai_review = generate_ai_review(
                result.obtained_marks,
                result.total_marks,
                result.category,
                result.difficulty
            )
            result.ai_review_generated = True
            result.save()
    
    return render(request, 'user_quiz_results.html', {'user_results': user_results})
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@login_required
def add_review(request, quiz_result_id):
    # Get the quiz result that the review is being added to
    quiz_result = get_object_or_404(models.QuizResult, id=quiz_result_id)

    # Handle POST request when form is submitted
    if request.method == 'POST':
        rating = request.POST.get('rating')
        message = request.POST.get('message')

        # Basic validation
        if not rating or not message:
            return HttpResponseBadRequest("Rating and message are required.")

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError("Rating must be between 1 and 5.")
        except ValueError as e:
            return HttpResponseBadRequest(str(e))

        # Save the review
        review = models.Review.objects.create(
            user=request.user,
            quiz_result=quiz_result,
            rating=rating,
            message=message
        )

        # Redirect to quiz results after saving the review
        return redirect('user_quiz_results')

    # If it's a GET request, just render the review form
    return render(request, 'add_review.html', {'quiz_result': quiz_result})

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def generate_ai_review(obtained_marks, total_marks, category, difficulty):
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    
    prompt = f"""
    A student scored {obtained_marks}/{total_marks} in a {difficulty} difficulty quiz on {category}.
    Generate a constructive review that:
    1. Starts with a positive note
    2. Analyzes their performance
    3. Identifies weak areas
    4. Provides study suggestions
    5. Is encouraging
    
    Keep it under 150 words and professional.
    """
    
    response = model.generate_content(prompt)
    return response.text

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

@login_required
def delete_quiz_link(request, link_id: int):
    quiz_link = get_object_or_404(models.QuizLink, id=link_id, user=request.user)
    quiz_id = quiz_link.quiz_number.id
    category_id = quiz_link.category.id
    quiz_link.delete()
    messages.success(request, "Shareable link has been deleted.")
    return redirect('all_quizes_list', category_id=category_id, quiz_id=quiz_id)

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def subscribe_plan(request):
    return render(request, 'subscribe_plan.html')

#++++++++++++++++++++++++++++++++++++++++++++++++


def payment_step(request):
    if request.method == 'POST':
        plan_name = request.POST.get('plan_name')
        plan_amount = request.POST.get('plan_amount')

        if not plan_name or not plan_amount:
            return redirect('subscribe_plan')

        request.session['selected_plan'] = plan_name
        request.session['plan_amount'] = plan_amount

        return render(request, 'payment_step.html', {
            'plan_name': plan_name,
            'plan_amount': plan_amount
        })

    return redirect('subscribe_plan')

#++++++++++++++++++++++++++++++++++++++++++++++++


def final_payment(request):
    plan_name = request.session.get('selected_plan')
    plan_amount = request.session.get('plan_amount')
    email = request.session.get('user_email')

    # Step 2: Handle email submission
    if request.method == 'POST' and 'email' in request.POST:
        email = request.POST.get('email')
        if not email:
            return redirect('subscribe_plan')

        request.session['user_email'] = email
        return render(request, 'final_payment.html', {
            'plan_name': plan_name,
            'plan_amount': plan_amount,
            'email': email
        })

    # Step 3: Handle card and agreement
    elif request.method == 'POST' and 'card_number' in request.POST:
        if not request.POST.get('agree'):
            return render(request, 'final_payment.html', {
                'plan_name': plan_name,
                'plan_amount': plan_amount,
                'email': email,
                'error': "You must agree to the terms."
            })

        txn_id = str(uuid.uuid4())

        # Save to Transaction table
        models.Transaction.objects.create(
            email=email,
            plan=plan_name,
            amount=plan_amount,
            transaction_id=txn_id
        )

        # Save to UserSubscription table
        models.UserSubscription.objects.create(
            email=email,
            plan=plan_name,
            amount=plan_amount
        )

        return render(request, 'payment_success.html', {
            'txn_id': txn_id,
            'email': email,
            'plan': plan_name,
            'amount': plan_amount
        })

    return redirect('subscribe_plan')

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@login_required
def LogoutPage(request):
    logout(request)
    return redirect('login')
