from django.http import JsonResponse
from django.db import connection
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic import TemplateView
from functools import wraps
from survey.models import Question, Answer, Like
import json

def login_required_rest(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Se debe autentificar para realizar esta acción.'}, status=401)
        return view_func(request, *args, **kwargs)
    return _wrapped_view
class QuestionTemplateView(TemplateView):
    template_name = 'survey/question_list.html'

class QuestionCreateView(CreateView):
    model = Question
    fields = ['title', 'description']
    template_name = 'survey/question_form.html'
    redirect_url = ''

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('survey:question-list')

class QuestionUpdateView(UpdateView):
    model = Question
    fields = ['title', 'description']
    template_name = 'survey/question_form.html'

def get_top_questions(user_id=None):
    with connection.cursor() as cursor:
        cursor.execute("""
            select
                survey_question.*,
                auth_user.username,
                (
                    count(distinct survey_answer.id) * 10 +
                    coalesce(likes.quantity_likes, 0) * 5 -
                    coalesce(dislikes.quantity_dislikes, 0) * 3 +
                    case when created = date('now') then 10 else 0 end
                )                                                               as ranking,
                coalesce(user_answer.value, "")                                 as user_value,
                case when user_like.value is TRUE then 1 else '' end            as user_likes,
                case when user_like.value is FALSE then 1 else '' end           as user_dislikes    
            from survey_question
                inner join main.auth_user on survey_question.author_id = auth_user.id
                left join survey_answer as user_answer ON survey_question.id = user_answer.question_id and user_answer.author_id = %s
                left join survey_like as user_like ON survey_question.id = user_like.question_id and user_like.author_id = %s
                left join survey_answer ON survey_question.id = survey_answer.question_id
                left join (
                    select question_id, count(question_id) as quantity_likes from survey_like where value = TRUE group by question_id
                ) AS likes on survey_question.id = likes.question_id
                left join (
                    select question_id, count(question_id) as quantity_dislikes from survey_like where value = FALSE group by question_id
                ) AS dislikes on survey_question.id = dislikes.question_id
            group by survey_question.id
            order by ranking desc
            limit 20
        """, [user_id, user_id])
        rows = cursor.fetchall()

    questions_data = []
    for row in rows:
        question_dict = {
            'id': row[0],
            'created': row[1],
            'title': row[2],
            'description': row[3],
            'author': row[5],
            'ranking': row[6],
            'user_value': row[7],
            'user_likes': row[8] ,
            'user_dislikes': row[9],
        }
        questions_data.append(question_dict)

    return questions_data

def questions(request):
    return JsonResponse({'questions': get_top_questions(request.user.id)})

@login_required_rest
def answer_question(request):
    if request.method != 'POST':
        return JsonResponse({'message': 'Método no permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        question_pk = data.get('question_pk')
        if not question_pk:
            raise ValueError('Ha ocurrido un error al guardar su evaluación.')
        question = Question.objects.get(pk=question_pk)

        answer, _ = Answer.objects.get_or_create(
            question=question, 
            author=request.user
        )
        answer.value = data.get('value')
        answer.save()
        return JsonResponse({'questions': get_top_questions(request.user.id)})
    except ValueError as e:
        return JsonResponse({'message': str(e)}, status=400)
    except Question.DoesNotExist:
        return JsonResponse({'message': 'Pregunta no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'message': f'Error del servidor: {str(e)}'}, status=500)

@login_required_rest
def like_dislike_question(request):
    if request.method != 'POST':
        return JsonResponse({'message': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        question_pk = data.get('question_pk')
        if not question_pk:
            raise ValueError('Ha ocurrido un error al guardar su evaluación.')
        question = Question.objects.get(pk=question_pk)

        like, _ = Like.objects.get_or_create(
            question=question, 
            author=request.user
        )
        like.value = data.get('value') == 'like'
        like.save()
        return JsonResponse({'questions': get_top_questions(request.user.id)})
    except ValueError as e:
        return JsonResponse({'message': str(e)}, status=400)
    except Question.DoesNotExist:
        return JsonResponse({'message': 'Pregunta no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'message': f'Error del servidor: {str(e)}'}, status=500)

