from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomePage,name='index'),
    path('loginPage/', views.LoginPage,name='login'),
    path('register/', views.register_page, name='register'),
    path('educator_home/', views.EducatorHomePage, name='educator_home'),
    path('categories/', views.CategoryList, name='category_list'),
    path('add-category/', views.AddQuizCategory, name='add_category'),
    path('update-category/<int:category_id>/', views.update_category, name='update_category'),
    path('confirm-delete-category/<int:category_id>/', views.confirm_delete_category, name='confirm_delete_category'),
    path('category/delete/<int:category_id>/', views.confirm_delete_category, name='confirm_delete_category'),
    path('category/<int:category_id>/quizzes/', views.quiz_list, name='quiz_list'),
    path('category/<int:category_id>/add-quiz/', views.add_quiz, name='add_quiz'),
    path('quiz/<int:quiz_id>/update/', views.update_quiz, name='update_quiz'),
    path('quiz/<int:quiz_id>/delete/', views.delete_quiz, name='delete_quiz'),
    path('category/<int:category_id>/quiz/<int:quiz_id>/questions/', views.question_list, name='question_list'),
    path('quiz/<int:quiz_id>/add-question/', views.add_question, name='add_question'),
    path('question/<int:question_id>/update/', views.update_question, name='update_question'),
    path('question/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('category/<int:category_id>/quiz/<int:quiz_id>/add_gpt_quiz/', views.add_gpt_quiz, name='add_gpt_quiz'),
    path('categories_link/', views.CategoryLinkList, name='category_link_list'),
    path('categories_link/<int:category_id>/quizes/', views.quiz_linkList, name='quizLink_list'),
    path('categories_link/<int:category_id>/quizes/<int:quiz_id>/mcqs/', views.all_quizes_list, name='all_quizes_list'),
    path('quiz/share/<uuid:unique_link>/', views.shared_quiz, name='shared_quiz'),

    path('generate-quiz-code/<int:quiz_id>/', views.generate_quiz_code, name='generate_quiz_code'),

    path('quiz_links/', views.quiz_link, name='linked_quizes'),

    path('take-quiz/', views.take_quiz, name='take_quiz'),

    path('studentRecords/', views.StudentResults, name='studentRecords'),
    path('student_home/', views.StudentHomePage, name='student_home'),

    path('quiz/<int:category_id>/<int:quiz_number>/<uuid:unique_link>/', views.quiz_solver, name='quiz_solver'),
    path('save-quiz-result/', views.save_quiz_result, name='save_quiz_result'),
    path('thank-you/', views.ThankuPage, name='thank_you'),
    path('quiz/delete-link/<int:link_id>/', views.delete_quiz_link, name='delete_quiz_link'),



    path('quiz/<int:quiz_id>/', views.quiz_page, name='quiz_page'),
    path('quiz-results/', views.user_quiz_results, name='user_quiz_results'),
    path('add-review/<int:quiz_result_id>/', views.add_review, name='add_review'),


    path('subscribe/', views.subscribe_plan, name='subscribe_plan'),
    path('payment/', views.payment_step, name='payment_step'),
    path('final-payment/', views.final_payment, name='final_payment'),


    path('logout/', views.LogoutPage,name='logout'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)